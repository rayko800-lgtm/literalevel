"""Comprueba que las claves de .env / CLAVES.txt funcionan de verdad.

No imprime ninguna clave. Solo dice si cada servicio responde.
"""
import sys, json
sys.path.insert(0, "app")
import config, requests

config.cargar()
import os

print("=== OXFORD DICTIONARIES ===")
try:
    r = requests.get(
        "https://od-api.oxforddictionaries.com/api/v2/entries/en-gb/example",
        headers={"app_id": os.environ["OXFORD_APP_ID"],
                 "app_key": os.environ["OXFORD_APP_KEY"]},
        timeout=25)
    print("  HTTP", r.status_code)
    if r.ok:
        d = r.json()
        ent = d["results"][0]["lexicalEntries"][0]
        pron = ent["entries"][0].get("pronunciations", [])
        ipa = [p.get("phoneticSpelling") for p in pron if p.get("phoneticNotation") == "IPA"]
        audio = [p.get("audioFile") for p in pron if p.get("audioFile")]
        print("  categoria:", ent["lexicalCategory"]["text"])
        print("  IPA      :", ipa)
        print("  audio    :", "sí" if audio else "no")
    else:
        print("  cuerpo:", r.text[:200])
except Exception as e:
    print("  ERROR:", type(e).__name__, str(e)[:200])

print("\n=== OPENAI ===")
try:
    from openai import OpenAI
    cli = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    ids = sorted(m.id for m in cli.models.list().data)
    print(f"  conexión OK — {len(ids)} modelos disponibles")
    for pref in ("gpt-5", "gpt-4o", "tts", "whisper", "gpt-4.1"):
        hay = [i for i in ids if i.startswith(pref)][:5]
        if hay:
            print(f"  {pref:<10} -> {hay}")
except Exception as e:
    print("  ERROR:", type(e).__name__, str(e)[:250])
