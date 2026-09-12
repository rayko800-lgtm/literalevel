"""Entrena y valida LiteraLevel V4 en Colab con una GPU T4.

Principios de diseño:
- solo prosa continua;
- ventanas de 250 palabras (los textos de 150-249 forman una sola ventana);
- la longitud total y el numero de ventanas nunca son entradas del modelo;
- separacion de entrenamiento/validacion a nivel de documento;
- prediccion del documento = media de sus ventanas;
- escala interna CEFR ordinal 0..5 y escala publica LiteraLevel 0..2.
"""

import json
import math
import os
import random
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path


def ensure_packages():
    needed = []
    for module, package in [("transformers", "transformers>=4.44,<5"),
                            ("sklearn", "scikit-learn>=1.3"),
                            ("scipy", "scipy>=1.10")]:
        try:
            __import__(module)
        except ImportError:
            needed.append(package)
    if needed:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", *needed], check=True)


ensure_packages()

import numpy as np
import pandas as pd
import torch
from scipy.stats import spearmanr
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset
from transformers import (AutoModelForSequenceClassification, AutoTokenizer,
                          DataCollatorWithPadding, get_linear_schedule_with_warmup)

SEED = 20260905
MODEL_NAME = "distilroberta-base"
BLOCK_WORDS = 250
MIN_WORDS = 150
MAX_BLOCKS_PER_DOC = 8
EPOCHS = 4
BATCH_SIZE = 16
LEARNING_RATE = 2e-5

DRIVE = Path("/content/drive/MyDrive/literalevel_bigdata")
DATA_PATH = DRIVE / "elg-cefr-en.json"
OUT_DIR = DRIVE / "modelo_literalevel_v4_transformer"
METRICS_PATH = DRIVE / "metricas_literalevel_v4.json"
PRED_PATH = DRIVE / "validacion_literalevel_v4.csv"
BC_PATH = DRIVE / "bc_texto_corregido.csv"
BC_OUT = DRIVE / "bc_validacion_v4.csv"

LEVEL_VALUE = {
    "A1": 0.0, "A1+": 0.5, "A2": 1.0, "A2+": 1.5,
    "B1": 2.0, "B1+": 2.5, "B2": 3.0, "B2+": 3.5,
    "C1": 4.0, "C2": 5.0,
}
ANCHORS = ["A1", "A2", "B1", "B2", "C1", "C2"]
WORD_RE = re.compile(r"[A-Za-z]+(?:['’-][A-Za-z]+)*")
SENT_RE = re.compile(r"[^.!?]+[.!?]+|[^.!?]+$")
BULLET_RE = re.compile(r"^\s*(?:[-*•▪◦]|\d+[.)]|[A-Z][.)])\s+")


def seed_everything(seed=SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def normalize(text):
    return re.sub(r"\s+", " ", str(text)).strip()


def words(text):
    return WORD_RE.findall(text)


def continuous_prose(text):
    """Conservative structural gate: enough prose, sentences, and no list-heavy layout."""
    raw = str(text).replace("\r", "\n")
    toks = words(raw)
    if len(toks) < MIN_WORDS:
        return False, "short"
    sentences = [s for s in SENT_RE.findall(normalize(raw)) if len(words(s)) >= 3]
    if len(sentences) < 4:
        return False, "few_sentences"
    mean_sentence = np.mean([len(words(s)) for s in sentences])
    if not 5 <= mean_sentence <= 55:
        return False, "sentence_shape"
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    bullet_lines = sum(bool(BULLET_RE.match(line)) for line in lines)
    short_lines = sum(len(words(line)) <= 4 for line in lines)
    if bullet_lines >= 2 or (len(lines) >= 6 and short_lines / len(lines) > 0.35):
        return False, "list_layout"
    return True, "ok"


def fixed_blocks(text, size=BLOCK_WORDS, minimum=MIN_WORDS, cap=MAX_BLOCKS_PER_DOC):
    """Return fixed word windows. A short final tail is represented by the last full window."""
    toks = words(text)
    n = len(toks)
    if n < minimum:
        return []
    if n <= size:
        return [" ".join(toks)]
    starts = list(range(0, n - size + 1, size))
    last_start = n - size
    if starts[-1] != last_start:
        starts.append(last_start)
    if len(starts) > cap:
        idx = np.linspace(0, len(starts) - 1, cap).round().astype(int)
        starts = [starts[i] for i in sorted(set(idx.tolist()))]
    return [" ".join(toks[s:s + size]) for s in starts]


def public_score(y):
    return float(np.clip(y, 0, 5) * 0.4)


def public_band(score):
    if score < 0.8:
        return "basico"
    if score < 1.6:
        return "intermedio"
    return "avanzado"


def load_documents():
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    docs, rejected = [], Counter()
    for i, item in enumerate(raw):
        level = str(item.get("cefr_level", "")).upper().strip()
        if level not in LEVEL_VALUE:
            rejected["unknown_level"] += 1
            continue
        text = normalize(item.get("text", ""))
        ok, reason = continuous_prose(text)
        if not ok:
            rejected[reason] += 1
            continue
        blocks = fixed_blocks(text)
        if not blocks:
            rejected["no_blocks"] += 1
            continue
        docs.append({
            "doc_id": str(item.get("title") or f"doc_{i}"),
            "level": level,
            "y": LEVEL_VALUE[level],
            "text": text,
            "blocks": blocks,
        })
    return docs, rejected


def split_documents(docs):
    # Stratify on the nearest main CEFR anchor; no block leakage is possible.
    strata = [ANCHORS[int(np.clip(round(d["y"]), 0, 5))] for d in docs]
    train_docs, val_docs = train_test_split(
        docs, test_size=0.22, random_state=SEED, stratify=strata)
    return train_docs, val_docs


def flatten(docs, training=False):
    counts = Counter(ANCHORS[int(np.clip(round(d["y"]), 0, 5))] for d in docs)
    rows = []
    for d in docs:
        cls = ANCHORS[int(np.clip(round(d["y"]), 0, 5))]
        # Each document has equal total influence; rare levels receive a moderate boost.
        doc_weight = (1.0 / len(d["blocks"])) * math.sqrt(len(docs) / (6 * counts[cls]))
        for block in d["blocks"]:
            rows.append({"text": block, "y": d["y"], "doc_id": d["doc_id"],
                         "level": d["level"], "weight": doc_weight if training else 1.0})
    return rows


class BlockDataset(Dataset):
    def __init__(self, rows, tokenizer):
        self.rows = rows
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        row = self.rows[idx]
        enc = self.tokenizer(row["text"], truncation=True, max_length=256)
        enc["labels"] = float(row["y"])
        enc["weights"] = float(row["weight"])
        enc["row_index"] = idx
        return enc


class Collator:
    def __init__(self, tokenizer):
        self.base = DataCollatorWithPadding(tokenizer, return_tensors="pt")

    def __call__(self, features):
        weights = torch.tensor([f.pop("weights") for f in features], dtype=torch.float32)
        row_index = torch.tensor([f.pop("row_index") for f in features], dtype=torch.long)
        batch = self.base(features)
        batch["weights"] = weights
        batch["row_index"] = row_index
        return batch


@torch.no_grad()
def predict_rows(model, loader, rows, device):
    model.eval()
    predictions = np.zeros(len(rows), dtype=float)
    for batch in loader:
        indexes = batch.pop("row_index").numpy()
        batch.pop("weights", None)
        labels = batch.pop("labels", None)
        inputs = {k: v.to(device) for k, v in batch.items()}
        out = model(**inputs).logits.squeeze(-1).float().cpu().numpy()
        predictions[indexes] = np.clip(out, 0, 5)
    return predictions


def document_metrics(rows, block_predictions):
    frame = pd.DataFrame(rows)[["doc_id", "level", "y"]].copy()
    frame["block_prediction"] = block_predictions
    docs = frame.groupby("doc_id", as_index=False).agg(
        level=("level", "first"), y=("y", "first"),
        predicted=("block_prediction", "mean"), n_blocks=("block_prediction", "size"))
    true_anchor = np.clip(np.rint(docs["y"]), 0, 5).astype(int)
    pred_anchor = np.clip(np.rint(docs["predicted"]), 0, 5).astype(int)
    rho = spearmanr(docs["y"], docs["predicted"]).statistic
    metrics = {
        "n_documents": int(len(docs)),
        "exact_anchor_accuracy": float(np.mean(true_anchor == pred_anchor)),
        "within_one_anchor": float(np.mean(np.abs(true_anchor - pred_anchor) <= 1)),
        "mae_cefr_steps": float(np.mean(np.abs(docs["y"] - docs["predicted"]))),
        "spearman": float(rho),
    }
    docs["score_0_2"] = docs["predicted"].map(public_score)
    docs["band"] = docs["score_0_2"].map(public_band)
    return metrics, docs


def make_loader(rows, tokenizer, shuffle):
    return DataLoader(BlockDataset(rows, tokenizer), batch_size=BATCH_SIZE,
                      shuffle=shuffle, num_workers=2, pin_memory=True,
                      collate_fn=Collator(tokenizer))


def train_model(train_rows, val_rows):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Dispositivo: {device}; GPU: {torch.cuda.get_device_name(0) if device.type == 'cuda' else 'ninguna'}")
    if device.type != "cuda":
        raise RuntimeError("V4 requiere la T4 seleccionada en Colab.")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME, num_labels=1, problem_type="regression").to(device)
    train_loader = make_loader(train_rows, tokenizer, True)
    val_loader = make_loader(val_rows, tokenizer, False)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=0.01)
    total_steps = EPOCHS * len(train_loader)
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=max(1, total_steps // 10), num_training_steps=total_steps)
    scaler = torch.amp.GradScaler("cuda")
    best = None
    best_state = None
    history = []
    for epoch in range(1, EPOCHS + 1):
        model.train()
        losses = []
        for batch in train_loader:
            batch.pop("row_index")
            weights = batch.pop("weights").to(device)
            labels = batch.pop("labels").to(device).float()
            inputs = {k: v.to(device) for k, v in batch.items()}
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type="cuda", dtype=torch.float16):
                pred = model(**inputs).logits.squeeze(-1)
                per_item = torch.nn.functional.smooth_l1_loss(pred, labels, reduction="none")
                loss = (per_item * weights).sum() / weights.sum()
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()
            losses.append(float(loss.detach().cpu()))
        val_pred = predict_rows(model, val_loader, val_rows, device)
        val_metrics, _ = document_metrics(val_rows, val_pred)
        record = {"epoch": epoch, "train_loss": float(np.mean(losses)), **val_metrics}
        history.append(record)
        print(json.dumps(record, ensure_ascii=False, indent=2))
        criterion = val_metrics["mae_cefr_steps"] - 0.15 * val_metrics["spearman"]
        if best is None or criterion < best:
            best = criterion
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)
    return model, tokenizer, history, device


def validate_british_council(model, tokenizer, device):
    if not BC_PATH.exists():
        return {"available": False}
    bc = pd.read_csv(BC_PATH)
    if "prosa_ambos" in bc:
        bc = bc[bc["prosa_ambos"].astype(str).str.lower().isin(["true", "1"])]
    rows = []
    for i, r in bc.iterrows():
        level = str(r.get("nivel", "")).upper()
        if level not in LEVEL_VALUE:
            continue
        text = normalize(r.get("texto", ""))
        ok, _ = continuous_prose(text)
        if not ok:
            continue
        for block in fixed_blocks(text):
            rows.append({"doc_id": str(r.get("archivo", i)), "level": level,
                         "y": LEVEL_VALUE[level], "text": block, "weight": 1.0})
    if not rows:
        return {"available": True, "n_documents": 0}
    loader = make_loader(rows, tokenizer, False)
    pred = predict_rows(model, loader, rows, device)
    metrics, docs = document_metrics(rows, pred)
    docs.to_csv(BC_OUT, index=False)
    means = docs.groupby("level")["score_0_2"].mean().round(4).to_dict()
    ordered = all(means[a] < means[b] for a, b in zip(
        [x for x in ANCHORS if x in means], [x for x in ANCHORS if x in means][1:]))
    return {"available": True, **metrics, "mean_score_0_2_by_level": means,
            "adjacent_means_strictly_ordered": bool(ordered)}


def main():
    seed_everything()
    from google.colab import drive
    drive.mount("/content/drive", force_remount=False)
    DRIVE.mkdir(parents=True, exist_ok=True)
    docs, rejected = load_documents()
    train_docs, val_docs = split_documents(docs)
    train_rows, val_rows = flatten(train_docs, True), flatten(val_docs, False)
    print("Documentos aceptados:", len(docs), "rechazos:", dict(rejected))
    print("Entrenamiento:", len(train_docs), "docs /", len(train_rows), "bloques")
    print("Validacion:", len(val_docs), "docs /", len(val_rows), "bloques")
    print("Distribucion:", dict(Counter(d["level"] for d in docs)))

    model, tokenizer, history, device = train_model(train_rows, val_rows)
    val_loader = make_loader(val_rows, tokenizer, False)
    val_pred = predict_rows(model, val_loader, val_rows, device)
    val_metrics, val_docs_frame = document_metrics(val_rows, val_pred)
    val_docs_frame.to_csv(PRED_PATH, index=False)
    bc_metrics = validate_british_council(model, tokenizer, device)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(OUT_DIR)
    tokenizer.save_pretrained(OUT_DIR)
    metadata = {
        "version": "LiteraLevel V4 transformer candidate",
        "created": pd.Timestamp.utcnow().isoformat(),
        "base_model": MODEL_NAME,
        "design": {
            "scope": "continuous English prose only",
            "block_words": BLOCK_WORDS,
            "minimum_words": MIN_WORDS,
            "maximum_blocks_sampled": MAX_BLOCKS_PER_DOC,
            "document_aggregation": "unweighted mean of block predictions",
            "uses_total_document_length": False,
            "split_unit": "document",
            "public_scale": "0..2; basic <0.8, intermediate <1.6, advanced otherwise",
            "cefr_claim": "research alignment only; not an official CEFR assessment",
        },
        "data": {
            "source": "ELG CEFR English, CC BY-NC-SA 4.0",
            "documents_accepted": len(docs),
            "documents_rejected": dict(rejected),
            "train_documents": len(train_docs),
            "validation_documents": len(val_docs),
            "train_blocks": len(train_rows),
            "validation_blocks": len(val_rows),
        },
        "validation": val_metrics,
        "british_council_development_validation": bc_metrics,
        "training_history": history,
    }
    METRICS_PATH.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\nRESULTADO FINAL V4")
    print(json.dumps(metadata, indent=2, ensure_ascii=False))
    print("\nGuardado en:", OUT_DIR)
    print("Metricas:", METRICS_PATH)
    print("Predicciones:", PRED_PATH)


if __name__ == "__main__":
    main()
