# 一次性脚本 (milestone-23 修订): 最小补查 height=level URL 参数与下拉候选. 非产品实现.
import json
import sys
from playwright.sync_api import sync_playwright

base = "http://127.0.0.1:18923"
out_json = sys.argv[1]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    console_msgs = []
    page.on("console", lambda m: console_msgs.append({"type": m.type, "text": m.text[:200]}))
    page.on("pageerror", lambda e: console_msgs.append({"type": "pageerror", "text": str(e)[:200]}))

    # 实验 1: 显式请求 height=level
    page.goto(f"{base}/?file=cz-sdk-master.cc.json&height=level&area=rloc&color=complexity",
              wait_until="networkidle", timeout=45000)
    page.wait_for_timeout(15000)
    url_after = page.evaluate("() => location.href")
    page.screenshot(path="/tmp/m23-evidence/frontend/shot-height-level-request.png")

    # 实验 2: 读指标下拉的全部候选 (height/area/color 三个 select)
    options = page.evaluate("""() => {
        const sels=[...document.querySelectorAll('select')];
        return sels.map(s=>({label:(s.labels&&s.labels[0]?s.labels[0].innerText:s.previousElementSibling?.innerText||'?').trim().slice(0,30),
                             selected:s.options[s.selectedIndex]?s.options[s.selectedIndex].text:null,
                             hasLevel:[...s.options].some(o=>/level/i.test(o.text)),
                             optionCount:s.options.length}));
    }""")
    # 搜 DOM 里任何可见 "level" 选项文本
    level_visible = page.evaluate("""() => {
        const t=document.body.innerText;
        return {levelMentioned:/\\blevel\\b/i.test(t), sample:t.split('\\n').filter(l=>/level/i.test(l)).slice(0,5)};
    }""")

    # 实验 3: 不带参数默认加载的 URL (对照)
    page.goto(f"{base}/?file=cz-sdk-master.cc.json", wait_until="networkidle", timeout=45000)
    page.wait_for_timeout(12000)
    url_default = page.evaluate("() => location.href")

    browser.close()

result = {
    "url_height_level_requested": url_after,
    "selects": options,
    "level_visible_check": level_visible,
    "url_default_load": url_default,
    "console_errors": [m for m in console_msgs if m["type"] in ("error", "pageerror")],
    "console_count": len(console_msgs),
}
with open(out_json, "w") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
print(json.dumps(result, ensure_ascii=False, indent=1))
