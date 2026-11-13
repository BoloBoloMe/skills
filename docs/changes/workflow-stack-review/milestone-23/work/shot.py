# 一次性实验脚本: 加载 CodeCharta 前端, 采集 console 与截图. 非产品实现.
import json
import sys
from playwright.sync_api import sync_playwright

url = sys.argv[1]
shot = sys.argv[2]
out_json = sys.argv[3]
wait_ms = int(sys.argv[4]) if len(sys.argv) > 4 else 15000

console_msgs = []
page_errors = []
request_failures = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    page.on("console", lambda m: console_msgs.append({"type": m.type, "text": m.text[:500]}))
    page.on("pageerror", lambda e: page_errors.append(str(e)[:500]))
    page.on("requestfailed", lambda r: request_failures.append({"url": r.url[:200], "failure": str(r.failure)[:120]}))
    resp = page.goto(url, wait_until="networkidle", timeout=45000)
    page.wait_for_timeout(wait_ms)
    page.screenshot(path=shot, full_page=False)
    # 页面关键状态
    state = page.evaluate("""() => ({
        title: document.title,
        canvases: document.querySelectorAll('canvas').length,
        canvasSize: (() => { const c = document.querySelector('canvas'); return c ? [c.width, c.height] : null; })(),
        bodyTextSample: document.body.innerText.slice(0, 300),
        fileList: (window.location.search || '')
    })""")
    browser.close()

result = {
    "url": url,
    "http_status": resp.status if resp else None,
    "page_state": state,
    "console_count": len(console_msgs),
    "console_errors": [m for m in console_msgs if m["type"] in ("error",)],
    "console_warnings": [m for m in console_msgs if m["type"] == "warning"],
    "console_all": console_msgs[:80],
    "page_errors": page_errors,
    "request_failures": request_failures,
}
with open(out_json, "w") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
print("OK screenshot:", shot)
print("http:", result["http_status"], "canvases:", state["canvases"], "console:", len(console_msgs), "pageErrors:", len(page_errors), "reqFail:", len(request_failures))
if result["console_errors"]:
    print("console_errors:", json.dumps(result["console_errors"], ensure_ascii=False)[:1000])
