"""H08: cuantas ventanas se salen de [0,5] antes del recorte, y cuanto cambia."""
import os, sys, glob, numpy as np
sys.path.insert(0, "app")
import scoring, reader, ficha

p = scoring.Puntuador(os.environ.get("LITERALEVEL_MODELO", "modelo_v4"))
torch = p._torch

def crudos(bloques):
    fuera = []
    for i in range(0, len(bloques), 64):
        ent = p.tokenizer(bloques[i:i+64], truncation=True,
                          max_length=scoring.MAX_LENGTH, padding=True,
                          return_tensors="pt")
        if p.dispositivo == "cuda":
            ent = {k: v.to("cuda") for k, v in ent.items()}
        with torch.no_grad():
            s = p.modelo(**ent).logits.squeeze(-1).float().cpu().numpy()
        fuera.extend(float(v) for v in np.atleast_1d(s))
    return fuera

rutas = sys.argv[1:]
tot = neg = alto = 0
maxdif = 0.0
for r in rutas:
    try:
        libro = reader.cargar(r)
    except Exception as e:
        print("  no se pudo abrir", r, e); continue
    bloques = []
    for _, c in ficha.capitulos_de_cuerpo(libro):
        bloques.extend(scoring.fixed_blocks(scoring.normalize(ficha.sin_licencia(c.texto))))
    if not bloques:
        continue
    cr = np.array(crudos(bloques))
    tot += len(cr); neg += int((cr < 0).sum()); alto += int((cr > 5).sum())
    antes = 0.4 * float(np.clip(cr.mean(), 0, 5))          # formula publicada
    despues = 0.4 * float(np.mean(np.clip(cr, 0, 5)))      # lo que hace el codigo
    maxdif = max(maxdif, abs(antes - despues))
    print(f"  {libro.titulo[:38]:<38} ventanas {len(cr):>5}  "
          f"min {cr.min():.3f}  max {cr.max():.3f}  "
          f"formula {antes:.4f}  codigo {despues:.4f}  dif {abs(antes-despues):.4f}")

if tot:
    print(f"\ntotal ventanas: {tot:,} | por debajo de 0: {neg} ({100*neg/tot:.3f} %)"
          f" | por encima de 5: {alto} ({100*alto/tot:.3f} %)")
    print(f"maxima diferencia entre las dos formulas: {maxdif:.4f}")
