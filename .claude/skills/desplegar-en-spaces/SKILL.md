---
name: desplegar-en-spaces
description: Publicar un modelo y una aplicación de Gradio en Hugging Face desde esta máquina — qué cuesta dinero y qué no, cómo se sube sin perder la clave de OpenAI, y las trampas que ya nos costaron tiempo. Úsala al desplegar LiteraLevel o cualquier app de Gradio, al publicar pesos de un modelo, o al tocar secretos y variables de un Space.
---

# Desplegar en Hugging Face

Todo lo de aquí está **hecho y verificado** el 8 de septiembre de 2026 con la
cuenta `MikeMaki1763`.

---

## 1. El token

Va en `C:\Users\laura\.hf_token`, **fuera del repositorio**. Tiene que ser de
tipo **Write**: uno de lectura no sube nada y hay que rehacerlo.

Para pedírselo a Miguel: créale el archivo con la herramienta de escritura y
ábreselo con `code C:\Users\laura\.hf_token`. Pega y guarda, sin pasar por el
chat — un token con permiso de escritura no debe quedar escrito en el
historial de la conversación.

**Si está por AnyDesk desde el móvil no puede pulsar Ctrl+S.** Actívale el
guardado automático de VS Code (`files.autoSave: afterDelay`) o dile que use
Archivo → Guardar con el ratón.

Comprobar sin imprimirlo nunca:

```python
urllib.request.Request("https://huggingface.co/api/whoami-v2",
                       headers={"Authorization": "Bearer " + tok})
# devuelve name, y auth.accessToken.role -> tiene que decir "write"
```

---

## 2. Qué cuesta dinero

- **Repositorios de modelos: gratis.** Publicar los pesos no cuesta nada.
- **Spaces de Gradio sobre CPU: requieren PRO**, 9 USD/mes en cuentas
  personales. Hay una excepción —hasta 2 Spaces de Gradio sobre ZeroGPU en
  cuentas gratuitas— pero exige **cuenta con más de 30 días**, así que no sirve
  para una cuenta recién creada.
- CPU Basic da **2 vCPU y 16 GB**, de sobra para una app que mide 1,05 GB.

---

## 3. Publicar un modelo

```python
api.create_repo(REPO, repo_type="model", private=False, exist_ok=True)
api.upload_folder(folder_path="modelo_v4", repo_id=REPO, repo_type="model")
```

**Verifica siempre la descarga anónima después**, que es lo que hará quien lo
use:

```python
AutoModelForSequenceClassification.from_pretrained(REPO, cache_dir=tmp, token=False)
```

Escribe una ficha de modelo de verdad: las escalas, el troceado, las métricas
con su *n* y **los límites sin adornos**. Va con el nombre del autor.

---

## 4. Publicar la app

Estructura del Space: `app.py` en la raíz (es lo que busca Hugging Face), el
paquete `app/` al lado, y los datos que la app espera en la raíz del
repositorio, porque `RAIZ = Path(__file__).parent.parent` resuelve ahí.

El `app.py` solo debe **arrancar** lo que ya existe. Nada de una versión «de la
nube» que se desincronice de la de casa.

**Trampas que ya nos mordieron:**

- `short_description` del README **no puede pasar de 60 caracteres**, o
  `upload_folder` falla con un 400 de `validate-yaml` que no dice dónde.
- **El modelo de spaCy no se instala solo.** Hay que ponerlo en
  `requirements.txt` por URL:
  `en_core_web_sm @ https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl`
- Los pesos no se suben al Space: se ponen como **variable**
  (`add_space_variable`) apuntando al repositorio del modelo, y se bajan al
  arrancar.
- Los archivos grandes (un `.db` de 233 MB) sí van en el Space; `upload_folder`
  los pasa por LFS solo.

---

## 5. Secretos y variables

```python
api.add_space_variable(REPO, "LITERALEVEL_MODELO", "usuario/modelo")   # publico
api.add_space_secret(REPO, "OPENAI_API_KEY", clave)                    # secreto
```

**Antes de poner una clave de pago en un Space público, para y piensa.**
Cualquiera que abra el enlace gasta el saldo del dueño. La solución que
funcionó aquí no fue cerrar la app con `auth=` —eso mata lo que la hace útil de
enseñar— sino **códigos de acceso que se canjean dentro** (`app/cuentas.py`):
la app entera libre, y con llave solo lo que llama a la API.

---

## 6. Comprobar que arrancó

```python
api.get_space_runtime(REPO).stage   # BUILDING -> APP_STARTING -> RUNNING
```

`RUNNING` y un 200 en `https://<usuario>-<space>.hf.space` no bastan: la página
puede servirse y la app estar rota. Ábrela de verdad antes de dar el enlace.

---

## 7. Por qué esto es mejor que el túnel

El enlace de `gradio.live` **muere al reiniciar el proceso**, y cada reinicio da
una dirección nueva — en esta máquina llegaron a acumularse catorce túneles
vivos de intentos sucesivos. La dirección del Space **no cambia nunca**, aunque
se siga desarrollando: cada subida reconstruye en un par de minutos sobre la
misma URL, con historial y vuelta atrás.
