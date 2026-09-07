"""Punto de entrada de LiteraLevel, para ejecutar en local y para desplegar.

`app/` no es un paquete: sus modulos se importan planos entre si
("import config", "from scoring import public_band"), y eso solo funciona si
`app/` esta en `sys.path`. Este envoltorio lo pone y arranca la interfaz, de
modo que la app se lanza desde la raiz del repositorio -que es lo que espera
cualquier plataforma de despliegue- sin tener que tocar los imports de los
siete modulos.

**No renombrar esto a `app.py`.** Chocaria con la carpeta `app/`: Python
resolveria `import app` al modulo y no al directorio, y a un humano le costaria
distinguirlos. En un Space de Hugging Face hay que declararlo en el front
matter del README, que por defecto busca `app.py`:

    app_file: main.py

Variables de entorno que reconoce:

    LITERALEVEL_MODELO       carpeta del modelo v4   (por defecto ./modelo_v4)
    LITERALEVEL_DICCIONARIO  SQLite de Kaikki        (por defecto ./kaikki_diccionario.db)
    OPENAI_API_KEY           opcional; sin ella la app degrada con elegancia
    PORT / SPACE_ID          los pone la plataforma; si aparecen, se sirve en 0.0.0.0

Uso:  python -X utf8 main.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "app"))

from ui import RUTAS_PERMITIDAS, TEMA, construir   # noqa: E402

# Nombre convencional: algunas plataformas importan el modulo y buscan `demo`
# en vez de ejecutarlo. Construirlo es barato: no carga ninguno de los tres
# recursos pesados, que siguen siendo perezosos.
demo = construir()


def _en_la_nube() -> bool:
    return bool(os.environ.get("SPACE_ID") or os.environ.get("PORT"))


if __name__ == "__main__":
    nube = _en_la_nube()
    demo.launch(
        theme=TEMA,
        server_name="0.0.0.0" if nube else "127.0.0.1",
        server_port=int(os.environ.get("PORT", 7860)),
        inbrowser=not nube,
        # Sin esto, los audios de tts-1 que viven en ~/.literalevel/audio no
        # llegan al navegador: Gradio los rechaza con InvalidPathError.
        allowed_paths=RUTAS_PERMITIDAS,
    )
