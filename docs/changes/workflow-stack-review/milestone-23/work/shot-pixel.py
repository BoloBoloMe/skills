# 一次性脚本 (milestone-23): 加载真实数据, 切依赖视图, 用 WebGL readPixels 扫描全帧找边颜色. 非产品实现.
import json
import sys
from playwright.sync_api import sync_playwright

url = sys.argv[1]
shot = sys.argv[2]
out_json = sys.argv[3]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    console_msgs = []
    page.on("console", lambda m: console_msgs.append({"type": m.type, "text": m.text[:300]}))
    page.goto(url, wait_until="networkidle", timeout=45000)
    page.wait_for_timeout(18000)

    # 点 Dependencies 页签
    try:
        page.get_by_role("button", name="Dependencies").first.click(timeout=5000)
    except Exception as e:
        page.evaluate("() => { const el=[...document.querySelectorAll('button,a,[role=tab],div')].find(e=>e.textContent.trim()==='Dependencies'); if(el) el.click(); }")
    page.wait_for_timeout(15000)
    page.screenshot(path=shot, full_page=False)

    # 全帧像素扫描
    counts = page.evaluate("""() => {
        const cs=[...document.querySelectorAll('canvas')];
        const out=[];
        for(const c of cs){
          const gl=c.getContext('webgl2')||c.getContext('webgl');
          if(!gl){out.push({kind:'2d',w:c.width,h:c.height});continue;}
          const w=gl.drawingBufferWidth,h=gl.drawingBufferHeight;
          const px=new Uint8Array(w*h*4);
          gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,px);
          let blue=0,red=0,orange=0,opaque=0;
          for(let i=0;i<px.length;i+=4){
            const r=px[i],g=px[i+1],b=px[i+2],a=px[i+3];
            if(a>0)opaque++;
            if(Math.abs(r-37)<40&&Math.abs(g-99)<40&&Math.abs(b-235)<40)blue++;
            else if(Math.abs(r-220)<40&&Math.abs(g-38)<40&&Math.abs(b-38)<40)red++;
            if(Math.abs(r-162)<30&&Math.abs(g-17)<30&&Math.abs(b-17)<30)orange++;
          }
          out.push({kind:'webgl',w,h,blue,red,orange,opaque,total:w*h});
        }
        return out;
    }""")
    browser.close()

result = {"url": url, "canvas_scan": counts,
          "console_errors": [m for m in console_msgs if m["type"] == "error"],
          "console_warning_count": sum(1 for m in console_msgs if m["type"] == "warning")}
with open(out_json, "w") as f:
    json.dump(result, f, indent=1)
print(json.dumps(result, indent=1))
