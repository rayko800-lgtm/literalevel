"""Un solo comando al terminar la medicion: catalogar, contar, probar y comparar.

    python -X utf8 tools/cerrar_corpus.py

1. Comprueba que `tools/medir_corpus.py` termino (ninguna unidad pendiente): si
   no, se para y dice cuantas faltan, en vez de medir horas aqui sin avisar.
2. `tools/catalogar_corpus.py`: catalogo_externo.csv, corpus_abierto.parquet y
   el .npy de embeddings del externo, reutilizando lo medido.
3. Recuentos frente al catalogo anterior: filas, reparto por fuente y por letra.
4. `pruebas_corpus.py`.
5. `tools/desplegar_app.py --seco --solo catalogo_externo.csv corpus_abierto.parquet`
   (sin subir nada). El .npy va a mano con upload_file, como siempre.
"""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "app"))
sys.path.insert(0, str(RAIZ / "tools"))


def correr(*args):
    print("\n$ " + " ".join(args), flush=True)
    r = subprocess.run([sys.executable, "-X", "utf8", *args], cwd=RAIZ)
    if r.returncode:
        sys.exit(f"PARO: {' '.join(args)} salio con {r.returncode}")


def main():
    import pandas as pd
    import catalogar_corpus as cc
    import medir_corpus as mc
    import scoring

    df = cc.cargar(None)
    hechas = mc.leer_hechas()
    solos = df[df["palabras"] >= scoring.MIN_WORDS]
    faltan = sum(1 for i, t in zip(solos["id"], solos["texto"]) if mc.clave("texto", [i], t) not in hechas)
    if faltan:
        sys.exit(f"PARO: faltan {faltan} textos por medir. Sigue: python -X utf8 tools/medir_corpus.py")
    print(f"medicion completa en disco: {len(hechas)} unidades")

    anterior = pd.read_csv(RAIZ / "catalogo_externo.csv", dtype=str)
    correr("tools/catalogar_corpus.py")
    nuevo = pd.read_csv(RAIZ / "catalogo_externo.csv", dtype=str)
    print(f"\nfilas: {len(anterior)} -> {len(nuevo)}")
    print("por fuente:", anterior["fuente"].value_counts().to_dict(), "->", nuevo["fuente"].value_counts().to_dict())
    orden = ["A1", "A2", "B1", "B2", "C1", "C2"]
    print("por letra:", anterior["nivel_cefr"].value_counts().reindex(orden).fillna(0).astype(int).to_dict(),
          "->", nuevo["nivel_cefr"].value_counts().reindex(orden).fillna(0).astype(int).to_dict())
    print("medida:", nuevo["medida"].value_counts().to_dict())
    npy = sorted(RAIZ.glob("catalogo_emb_ext_*.npy"), key=lambda p: p.stat().st_mtime)
    print("embeddings del externo:", npy[-1].name if npy else "NINGUNO")

    correr("pruebas_corpus.py")
    correr("tools/desplegar_app.py", "--seco", "--solo", "catalogo_externo.csv", "corpus_abierto.parquet")
    print("\nListo para el reinicio: commit de catalogo_externo.csv y corpus_abierto.parquet, "
          "desplegar_app.py --solo con esos dos y el .npy con upload_file.")


if __name__ == "__main__":
    main()
