# LiteraLevel

App de lectura en inglés con estimación de dificultad. Proyecto integrador del
Módulo 5, Diplomado en Ciencia de Datos (Gen 34).

## Puesta en marcha

```bash
pip install -r requirements.txt
python validar_local.py     # reproduce la validación externa
```

El modelo v4 va en `modelo_v4/` (descargado de Drive `literalevel_bigdata/
modelo_literalevel_v4_transformer`). No se versiona: son 328 MB.

## Módulos

| Archivo | Qué hace |
|---|---|
| `app/scoring.py` | Puntuación de dificultad. Port fiel de `ll_v4_transformer.py` |
| `app/reader.py`  | Lector de epub, pdf y txt → capítulos |
| `app/perfil.py`  | Nivel del lector y rango de lectura recomendado |
| `validar_local.py` | Verifica que lo local reproduce lo de Colab |
| `tests_smoke.py` | Pruebas de la lógica de bloques y escala (sin modelo) |

`app/perfil.py` NO puede llamarse `profile.py`: taparía el módulo `profile` de
la biblioteca estándar y rompería `import cProfile` dentro de torch.

## El modelo

`distilroberta-base` en regresión. Bloques de 250 palabras, mínimo 150, hasta
8 por documento, media sin ponderar. La longitud total nunca es una señal.
Escala interna 0..5 (A1..C2); escala pública 0..2 = interna × 0.4.

Validación (144 docs): dentro de ±1 nivel 97.2%, Spearman 0.908.
British Council, corpus externo (38 docs): dentro de ±1 100%, Spearman 0.829.
