#!/usr/bin/env python3
"""CodeCharta 汉化产物渲染冒烟 (D014): 临时静态服务 + 无头浏览器截图 + 关键元素断言.

用法: python3 smoke.py --dist <dist/bundler/browser> --out <报告目录> [--base-url http://127.0.0.1:8090]
任一断言失败 exit 1 (冒烟失败即构建失败).

断言:
  1. 指标视图: 3D canvas 渲染出建筑 (webgl readPixels: 非主导色不透明像素超阈值);
     顶部页签出现 指标/依赖, 底栏出现 面积/高度/颜色;
  2. 依赖视图 (#/dependencies): 画布渲染出方块 (非主导色像素超阈值), 文本含 依赖/边;
  3. pageerror = 0 (console error 只记录进报告不强断).
  条件渲染的 [领域] 页签与 [层级] 段只记 note 不硬断 (冒烟样例无 domain lens/packages).

驱动: 优先 playwright (宿主实测路径), 缺席回退 CDP+websockets (容器实测路径, 需
CC_SMOKE_PYTHON="uv run --with websockets python"; chrome 二进制用 CC_CHROME 覆盖).
样例数据: 内置合成 cc.json 2.x (metrics rloc/complexity + dependency lens level/环/向上依赖),
确定性字节, 不依赖外部数据.
"""

import argparse
import base64
import functools
import hashlib
import http.server
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time

VIEWPORT = (1400, 900)
MIN_BUILDING_PIXELS = 800
MIN_DEP_PIXELS = 500


# ---------------------------------------------------------------- 样例数据

FILES = [("app", ["Main.java", "Router.java", "Api.java"]), ("util", ["MathUtil.java", "DateUtil.java"]), ("db", ["Dao.java", "Connection.java"])]


def _ident(path):
    return hashlib.sha256(path.encode()).hexdigest()[:16]


def build_sample():
    metrics_attrs, dep_nodes = {}, {}
    children = []
    for folder, files in FILES:
        kids = []
        for f in files:
            path = "root/%s/%s" % (folder, f)
            fid = _ident(path)
            rloc = 120.0 + (len(path) % 7) * 30.0
            kids.append({"id": fid, "name": f, "type": "File"})
            metrics_attrs[fid] = {"rloc": rloc, "loc": rloc + 20.0, "complexity": 5.0 + (len(path) % 5)}
            dep_nodes[fid] = {"level": len(path) % 3}
        children.append({"id": _ident("root/" + folder), "name": folder, "type": "Folder", "children": kids})
    edges = [
        {"fromId": _ident("root/app/Main.java"), "toId": _ident("root/app/Router.java"), "attributes": {"dependencies": 3}},
        {"fromId": _ident("root/app/Router.java"), "toId": _ident("root/app/Api.java"), "attributes": {"dependencies": 2}},
        {"fromId": _ident("root/util/DateUtil.java"), "toId": _ident("root/util/MathUtil.java"), "attributes": {"dependencies": 1}, "isCyclic": True},
        {"fromId": _ident("root/util/MathUtil.java"), "toId": _ident("root/util/DateUtil.java"), "attributes": {"dependencies": 1}, "isCyclic": True},
        {"fromId": _ident("root/db/Dao.java"), "toId": _ident("root/app/Main.java"), "attributes": {"dependencies": 1}, "isPointingUpwards": True},
    ]
    return {
        "meta": {"apiVersion": "2.1", "projectName": "smoke-sample"},
        "files": [{"id": _ident("root"), "name": "root", "type": "Folder", "children": children}],
        "lenses": {
            "metrics": {
                "attributes": metrics_attrs,
                "attributeTypes": {"rloc": "absolute", "loc": "absolute", "complexity": "absolute"},
                "attributeDescriptors": {},
            },
            "dependency": {"nodes": dep_nodes, "edges": edges, "attributeTypes": {}, "attributeDescriptors": {}},
        },
    }


# ---------------------------------------------------------------- 静态服务

class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def start_server(root):
    handler = functools.partial(_QuietHandler, directory=root)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


# ---------------------------------------------------------------- 断言用的页面 JS

PIXEL_SCAN_JS = """
() => {
  const out = [];
  for (const c of document.querySelectorAll('canvas')) {
    let w = c.width, h = c.height, data = null;
    const gl = c.getContext('webgl2') || c.getContext('webgl');
    if (gl) {
      w = gl.drawingBufferWidth; h = gl.drawingBufferHeight;
      const px = new Uint8Array(w * h * 4);
      gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, px);
      data = px;
    } else {
      const ctx = c.getContext('2d');
      if (!ctx) continue;
      data = ctx.getImageData(0, 0, w, h).data;
    }
    const counts = {};
    let opaque = 0;
    for (let i = 0; i < data.length; i += 4) {
      if (data[i+3] === 0) continue;
      opaque++;
      const key = (data[i] >> 4) + ',' + (data[i+1] >> 4) + ',' + (data[i+2] >> 4);
      counts[key] = (counts[key] || 0) + 1;
    }
    const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    const dominant = sorted.length ? sorted[0][1] : 0;
    out.push({w, h, opaque, dominant, nonDominant: opaque - dominant});
  }
  return out;
}
"""

CLICK_EXACT_JS = """
(t) => {
  const els = [...document.querySelectorAll('a,button,[role=tab]')];
  const el = els.find(e => e.textContent.trim() === t);
  if (!el) return false;
  el.click();
  return true;
}
"""


class Checks:
    def __init__(self):
        self.fails = []
        self.notes = []

    def expect(self, ok, what):
        print(("PASS " if ok else "FAIL ") + what)
        if not ok:
            self.fails.append(what)

    def note(self, what):
        print("INFO " + what)
        self.notes.append(what)


def run_flow(d, base_url, out, checks):
    # 1. 指标视图
    d.goto(base_url + "/?file=smoke-sample.cc.json", wait_ms=1000)
    # 等 3D 画布就绪 (冷启动可能慢于 10s, 轮询上限 30s), 再等渲染稳定
    canvases = 0
    for _ in range(30):
        canvases = d.eval("() => document.querySelectorAll('canvas').length") or 0
        if canvases:
            break
        time.sleep(1)
    checks.expect(canvases > 0, "3D 画布挂载 (canvas x%d)" % canvases)
    time.sleep(4)
    text = d.text()
    for word in ("指标", "依赖"):
        checks.expect(word in text, "页签出现 [%s]" % word)
    if "领域" in text:
        checks.note("页签出现 [领域]")
    else:
        checks.note("页签无 [领域] (领域页签随 domain lens 数据条件渲染, 冒烟样例无 domain lens, 预期行为)")
    for word in ("面积", "高度", "颜色"):
        checks.expect(word in text, "底栏出现 [%s]" % word)
    scans = d.eval(PIXEL_SCAN_JS) or []
    buildings = max([s.get("nonDominant", 0) for s in scans if s.get("w", 0) > 400] or [0])
    checks.expect(buildings >= MIN_BUILDING_PIXELS, "3D canvas 渲染出建筑 (非主导色像素 %d >= %d)" % (buildings, MIN_BUILDING_PIXELS))
    checks.note("canvas 扫描: %s" % json.dumps(scans))
    checks.note("页面文本样例: %r" % text[:300])
    d.screenshot(os.path.join(out, "shot-01-map.png"))

    # 2. 依赖视图 (hash 路由, F011)
    ok = d.click_exact("依赖")
    checks.expect(ok, "点击页签 [依赖]")
    time.sleep(2)
    dep_ready = 0
    for _ in range(15):
        dep_ready = d.eval("() => document.querySelectorAll('canvas').length") or 0
        if dep_ready:
            break
        time.sleep(1)
    time.sleep(4)
    checks.expect("#/dependencies" in d.url(), "URL 进入 hash 路由 #/dependencies")
    text = d.text()
    for word in ("依赖", "边"):
        checks.expect(word in text, "依赖视图出现 [%s]" % word)
    if "层级" in text:
        checks.note("依赖视图出现 [层级] (层级段随 packages 数据渲染)")
    else:
        checks.note("依赖视图无 [层级] 段 (dependencyBar 仅在有 packages 数据时渲染层级段, 冒烟样例无 packages, 预期行为)")
    scans = d.eval(PIXEL_SCAN_JS) or []
    boxes = max([s.get("nonDominant", 0) for s in scans] or [0])
    checks.expect(boxes >= MIN_DEP_PIXELS, "依赖视图渲染出方块 (非主导色像素 %d >= %d)" % (boxes, MIN_DEP_PIXELS))
    d.screenshot(os.path.join(out, "shot-02-dependencies.png"))

    checks.expect(len(d.page_errors) == 0, "pageerror 为 0 (%s)" % d.page_errors[:3])
    checks.note("console error %d 条: %s" % (len(d.console_errors), d.console_errors[:5]))


# ---------------------------------------------------------------- 驱动

class PlaywrightDriver:
    name = "playwright"

    def __init__(self):
        from playwright.sync_api import sync_playwright

        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.launch(headless=True)
        self.page = self.browser.new_page(viewport={"width": VIEWPORT[0], "height": VIEWPORT[1]})
        self.console_errors, self.page_errors = [], []
        self.page.on("console", lambda m: self.console_errors.append(m.text[:300]) if m.type == "error" else None)
        self.page.on("pageerror", lambda e: self.page_errors.append(str(e)[:300]))

    def goto(self, url, wait_ms):
        self.page.goto(url, wait_until="networkidle", timeout=45000)
        self.page.wait_for_timeout(wait_ms)

    def text(self):
        return self.page.evaluate("() => document.body.innerText")

    def eval(self, js):
        return self.page.evaluate(js)

    def click_exact(self, text):
        return self.page.evaluate(CLICK_EXACT_JS, text)

    def screenshot(self, path):
        self.page.screenshot(path=path, full_page=False)

    def url(self):
        return self.page.url

    def close(self):
        self.browser.close()
        self._pw.stop()


class CdpDriver:
    """无 playwright 时的回退: CDP over websockets (m13 probe 同配方)."""

    name = "cdp-websockets"

    def __init__(self):
        import asyncio
        import urllib.request

        import websockets

        chrome = os.environ.get("CC_CHROME")
        if not chrome:
            for cand in (
                "/home/bolo/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome",
                "/usr/bin/google-chrome",
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
            ):
                if os.path.exists(cand):
                    chrome = cand
                    break
        if not chrome:
            raise RuntimeError("找不到 chrome 二进制, 请设 CC_CHROME")
        port = self._free_port()
        self._proc = subprocess.Popen(
            [chrome, "--headless=new", "--no-sandbox", "--hide-scrollbars",
             "--enable-unsafe-swiftshader", "--use-gl=angle", "--use-angle=swiftshader",
             "--remote-debugging-port=%d" % port,
             "--window-size=%d,%d" % VIEWPORT, "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        info = None
        for _ in range(100):
            try:
                info = json.load(urllib.request.urlopen("http://127.0.0.1:%d/json/version" % port, timeout=1))
                break
            except Exception:
                time.sleep(0.3)
        if info is None:
            raise RuntimeError("chrome devtools 未就绪")

        self.console_errors, self.page_errors = [], []
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()
        fut = asyncio.run_coroutine_threadsafe(self._session(info["webSocketDebuggerUrl"], websockets), self._loop)
        fut.result(timeout=30)

    @staticmethod
    def _free_port():
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    async def _session(self, ws_url, websockets):
        import asyncio

        self._ws = await websockets.connect(ws_url, max_size=48 * 1024 * 1024)
        self._id = 0
        self._futures = {}
        self._loop = asyncio.get_running_loop()
        asyncio.ensure_future(self._reader())
        t = await self._cmd("Target.createTarget", {"url": "about:blank"}, sid=None)
        sid = (await self._cmd("Target.attachToTarget", {"targetId": t["result"]["targetId"], "flatten": True}, sid=None))["result"]["sessionId"]
        self._sid = sid
        await self._cmd("Page.enable")
        await self._cmd("Runtime.enable")
        await self._cmd("Emulation.setDeviceMetricsOverride",
                        {"width": VIEWPORT[0], "height": VIEWPORT[1], "deviceScaleFactor": 1, "mobile": False})

    async def _reader(self):
        import asyncio

        while True:
            try:
                data = json.loads(await self._ws.recv())
            except Exception:
                return
            if "id" in data and data["id"] in self._futures:
                self._futures.pop(data["id"]).set_result(data)
            elif data.get("method") == "Runtime.consoleAPICalled" and data["params"].get("type") == "error":
                args = data["params"].get("args", [])
                self.console_errors.append(" ".join(str(a.get("value", a.get("description", "")))[:200] for a in args))
            elif data.get("method") == "Runtime.exceptionThrown":
                self.page_errors.append(str(data["params"].get("exceptionDetails", {}).get("text", ""))[:300])

    async def _cmd(self, method, params=None, sid="__default__"):
        import asyncio

        self._id += 1
        mid = self._id
        msg = {"id": mid, "method": method, "params": params or {}}
        use_sid = self._sid if sid == "__default__" else sid
        if use_sid:
            msg["sessionId"] = use_sid
        fut = self._loop.create_future()
        self._futures[mid] = fut
        await self._ws.send(json.dumps(msg))
        return await asyncio.wait_for(fut, timeout=60)

    def _run(self, coro):
        import asyncio

        return asyncio.run_coroutine_threadsafe(coro, self._loop).result(timeout=90)

    def goto(self, url, wait_ms):
        self._run(self._cmd("Page.navigate", {"url": url}))
        time.sleep(wait_ms / 1000.0)

    def text(self):
        res = self._run(self._cmd("Runtime.evaluate", {"expression": "document.body.innerText", "returnByValue": True}))
        return res.get("result", {}).get("result", {}).get("value", "")

    def eval(self, js):
        # Runtime.evaluate 只求值表达式; 传入 "() => {...}" 时需要显式调用
        expr = "(%s)()" % js if js.lstrip().startswith("(") else js
        res = self._run(self._cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True}))
        return res.get("result", {}).get("result", {}).get("value")

    def click_exact(self, text):
        res = self._run(self._cmd("Runtime.evaluate", {
            "expression": "(%s)(%s)" % (CLICK_EXACT_JS, json.dumps(text)),
            "returnByValue": True,
        }))
        return res.get("result", {}).get("result", {}).get("value")

    def screenshot(self, path):
        res = self._run(self._cmd("Page.captureScreenshot", {"format": "png"}))
        with open(path, "wb") as fh:
            fh.write(base64.b64decode(res["result"]["data"]))

    def url(self):
        res = self._run(self._cmd("Runtime.evaluate", {"expression": "location.href", "returnByValue": True}))
        return res.get("result", {}).get("result", {}).get("value", "")

    def close(self):
        try:
            self._proc.terminate()
        except Exception:
            pass


def make_driver():
    try:
        import playwright  # noqa: F401

        return PlaywrightDriver()
    except ImportError:
        pass
    try:
        import websockets  # noqa: F401

        return CdpDriver()
    except ImportError:
        print("FATAL: 需要 playwright 或 websockets 之一.", file=sys.stderr)
        print("宿主: python3 自带 playwright (m23 实测); 容器: CC_SMOKE_PYTHON='uv run --with websockets python'", file=sys.stderr)
        raise SystemExit(2)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dist", required=True, help="构建产物目录 dist/bundler/browser")
    ap.add_argument("--out", required=True, help="报告输出目录 (截图/JSON)")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    root = os.path.join(args.out, "smoke-root")
    if os.path.isdir(root):
        shutil.rmtree(root)
    shutil.copytree(args.dist, root)
    with open(os.path.join(root, "smoke-sample.cc.json"), "w", encoding="utf-8") as fh:
        json.dump(build_sample(), fh, ensure_ascii=False, separators=(",", ":"))

    srv = start_server(root)
    port = srv.server_address[1]
    base_url = "http://127.0.0.1:%d" % port
    print("冒烟服务:", base_url, "(临时, 结束即停)")

    checks = Checks()
    driver = make_driver()
    try:
        run_flow(driver, base_url, args.out, checks)
    finally:
        driver.close()
        srv.shutdown()

    result = {
        "driver": driver.name,
        "base_url": base_url,
        "fails": checks.fails,
        "notes": checks.notes,
        "console_errors": driver.console_errors,
        "page_errors": driver.page_errors,
    }
    with open(os.path.join(args.out, "smoke.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1)
    print("冒烟结果:", "PASS" if not checks.fails else "FAIL (%d)" % len(checks.fails))
    return 0 if not checks.fails else 1


if __name__ == "__main__":
    sys.exit(main())
