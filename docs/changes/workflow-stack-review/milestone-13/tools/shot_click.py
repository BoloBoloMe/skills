import asyncio, base64, json, subprocess, sys, time, urllib.request
import websockets

# 用法: shot_click.py <url> <out.png> <wait> [x,y ...]   (按顺序点击给定坐标, 每点之间等 1.2s)
URL, OUT, WAIT = sys.argv[1], sys.argv[2], float(sys.argv[3])
CLICKS = [tuple(int(v) for v in a.split(",")) for a in sys.argv[4:]]
CHROME = "/home/bolo/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome"
proc = subprocess.Popen([CHROME, "--headless=new", "--no-sandbox", "--hide-scrollbars",
    "--enable-unsafe-swiftshader", "--use-gl=angle", "--use-angle=swiftshader",
    "--remote-debugging-port=9336", "--window-size=1400,900", "about:blank"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(60):
        try:
            info = json.load(urllib.request.urlopen("http://127.0.0.1:9336/json/version", timeout=1)); break
        except Exception: time.sleep(0.3)
    ws_url = info["webSocketDebuggerUrl"]
    async def main():
        async with websockets.connect(ws_url, max_size=20*1024*1024) as ws:
            i = 0
            async def cmd(method, params=None, session=None):
                nonlocal i
                i += 1
                msg = {"id": i, "method": method, "params": params or {}}
                if session: msg["sessionId"] = session
                await ws.send(json.dumps(msg))
                while True:
                    data = json.loads(await ws.recv())
                    if data.get("id") == i: return data
            t = await cmd("Target.createTarget", {"url": "about:blank"})
            tid = t["result"]["targetId"]
            a = await cmd("Target.attachToTarget", {"targetId": tid, "flatten": True})
            sid = a["result"]["sessionId"]
            await cmd("Page.enable", {}, sid)
            await cmd("Runtime.enable", {}, sid)
            await cmd("Emulation.setDeviceMetricsOverride",
                      {"width": 1400, "height": 900, "deviceScaleFactor": 1, "mobile": False}, sid)
            await cmd("Page.navigate", {"url": URL}, sid)
            await asyncio.sleep(WAIT)
            for (x, y) in CLICKS:
                for typ in ("mousePressed", "mouseReleased"):
                    await cmd("Input.dispatchMouseEvent",
                              {"type": typ, "x": x, "y": y, "button": "left", "clickCount": 1}, sid)
                await asyncio.sleep(1.2)
            res = await cmd("Runtime.evaluate", {"expression": "document.body.innerText.replace(/\\n+/g,' | ').slice(0,600)"}, sid)
            print("TEXT:", res.get("result", {}).get("result", {}).get("value"))
            shot = await cmd("Page.captureScreenshot", {"format": "png"}, sid)
            open(OUT, "wb").write(base64.b64decode(shot["result"]["data"]))
            print("screenshot:", OUT)
    asyncio.run(main())
finally:
    proc.terminate()
