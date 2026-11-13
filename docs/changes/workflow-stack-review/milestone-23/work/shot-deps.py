# 一次性脚本 (milestone-23): 切到 Dependencies 视图并截图. 非产品实现.
import json
import sys
from playwright.sync_api import sync_playwright

url = sys.argv[1]
shot = sys.argv[2]
out_json = sys.argv[3]

console_msgs = []
page_errors = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    page.on("console", lambda m: console_msgs.append({"type": m.type, "text": m.text[:300]}))
    page.on("pageerror", lambda e: page_errors.append(str(e)[:300]))
    resp = page.goto(url, wait_until="networkidle", timeout=45000)
    page.wait_for_timeout(18000)

    # 点击依赖页签 (L1 失败则用 JS 兜底找按钮)
    clicked = False
    for desc in ["Dependencies"]:
        try:
            btn = page.get_by_role("button", name=desc).first
            btn.click(timeout=5000)
            clicked = True
            break
        except Exception as e:
            print("click role failed:", str(e)[:200])
    if not clicked:
        r = page.evaluate("""() => {
            const els=[...document.querySelectorAll('button,a,[role=tab],div')];
            const el=els.find(e=>e.textContent.trim()==='Dependencies');
            if(el){el.click();return 'clicked '+el.tagName;}return 'not found';
        }""")
        print("js fallback:", r)
        clicked = "clicked" in str(r)
    page.wait_for_timeout(15000)
    page.screenshot(path=shot, full_page=False)
    state = page.evaluate("""() => ({
        url: location.href,
        bodyTextSample: document.body.innerText.slice(0, 500),
        canvases: document.querySelectorAll('canvas').length
    })""")
    browser.close()

result = {
    "url": url, "http_status": resp.status if resp else None, "clicked": clicked,
    "page_state": state, "console_errors": [m for m in console_msgs if m["type"] == "error"],
    "console_warnings": [m for m in console_msgs if m["type"] == "warning"],
    "page_errors": page_errors, "console_count": len(console_msgs),
}
with open(out_json, "w") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
print("OK", shot, "clicked:", clicked, "errors:", len(result["console_errors"]), "pageErrors:", len(page_errors))
