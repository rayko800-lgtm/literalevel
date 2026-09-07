"""Puente CDP: controla el Chrome ya abierto (perfil real, sesion de Google activa).
Requiere Chrome lanzado con --remote-debugging-port=9222.
Uso:
    python cdp.py tabs
    python cdp.py eval  <indice_tab> "<expresion JS>"
    python cdp.py text  <indice_tab>
    python cdp.py key   <indice_tab> <ctrl|none> <F9|Enter|...>
"""
import sys, json, asyncio, requests, websockets

PORT = 9222

def tabs():
    r = requests.get(f"http://127.0.0.1:{PORT}/json", timeout=5).json()
    return [t for t in r if t.get("type") == "page"]

async def _send(ws_url, method, params=None):
    async with websockets.connect(ws_url, max_size=40*1024*1024) as ws:
        await ws.send(json.dumps({"id": 1, "method": method, "params": params or {}}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get("id") == 1:
                return msg

def evaluate(idx, expr):
    t = tabs()[idx]
    res = asyncio.run(_send(t["webSocketDebuggerUrl"], "Runtime.evaluate",
                            {"expression": expr, "returnByValue": True, "awaitPromise": True}))
    r = res.get("result", {}).get("result", {})
    return r.get("value", r)

def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    cmd = sys.argv[1]
    if cmd == "tabs":
        for i, t in enumerate(tabs()):
            print(f"[{i}] {t['title'][:70]}\n     {t['url'][:110]}")
    elif cmd == "eval":
        print(evaluate(int(sys.argv[2]), sys.argv[3]))
    elif cmd == "text":
        print(evaluate(int(sys.argv[2]), "document.body.innerText"))
    elif cmd == "key":
        idx, mod, key = int(sys.argv[2]), sys.argv[3], sys.argv[4]
        t = tabs()[idx]
        mods = {"ctrl": 2, "shift": 8, "alt": 1, "none": 0}[mod]
        for typ in ("rawKeyDown", "keyUp"):
            asyncio.run(_send(t["webSocketDebuggerUrl"], "Input.dispatchKeyEvent",
                              {"type": typ, "modifiers": mods, "key": key,
                               "windowsVirtualKeyCode": 120 if key == "F9" else 13}))
        print("enviado", mod, key)

if __name__ == "__main__":
    main()
