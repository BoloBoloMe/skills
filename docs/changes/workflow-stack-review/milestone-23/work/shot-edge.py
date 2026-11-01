# 一次性脚本 (milestone-23): 依赖视图 + 选中建筑触发边渲染, 像素取证. 非产品实现.
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

    # 切 Dependencies 视图
    try:
        page.get_by_role("button", name="Dependencies").first.click(timeout=5000)
    except Exception:
        page.evaluate("() => { const el=[...document.querySelectorAll('button,a,[role=tab],div')].find(e=>e.textContent.trim()==='Dependencies'); if(el) el.click(); }")
    page.wait_for_timeout(8000)

    # 找依赖面板里的可点行 (edge 列表), 若有点第一个
    panel = page.evaluate("""() => {
        const t=document.body.innerText;
        return t.slice(0,1500);
    }""")
    print("面板文本片段:", panel[:400].replace(chr(10),' | '))

    # 点击 3D 画布中央 (选中一个建筑)
    page.mouse.click(960, 540)
    page.wait_for_timeout(500)
    page.mouse.click(960, 540)  # 双击习惯: 单击两次模拟选中
    page.wait_for_timeout(12000)
    page.screenshot(path=shot, full_page=False)

    counts = page.evaluate("""() => {
        const cs=[...document.querySelectorAll('canvas')];
        const out=[];
        for(const c of cs){
          const gl=c.getContext('webgl2')||c.getContext('webgl');
          if(!gl){out.push({kind:'2d',w:c.width,h:c.height});continue;}
          const w=gl.drawingBufferWidth,h=gl.drawingBufferHeight;
          const px=new Uint8Array(w*h*4);
          gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,px);
          let blue=0,red=0,opaque=0,colors=new Set();
          for(let i=0;i<px.length;i+=4){
            const r=px[i],g=px[i+1],b=px[i+2],a=px[i+3];
            if(a>0){opaque++;
              if(i%9973<4){colors.add(r+','+g+','+b);}
            }
            if(Math.abs(r-37)<40&&Math.abs(g-99)<40&&Math.abs(b-235)<40)blue++;
            else if(Math.abs(r-220)<40&&Math.abs(g-38)<40&&Math.abs(b-38)<40)red++;
          }
          out.push({kind:'webgl',w,h,blue,red,opaque,sampleColors:[...colors].slice(0,24)});
        }
        return out;
    }""")
    body_after = page.evaluate("() => document.body.innerText.slice(0,600)")
    browser.close()

result = {"url": url, "canvas_scan": counts, "body_after": body_after,
          "console_errors": [m for m in console_msgs if m["type"] == "error"],
          "console_warning_count": sum(1 for m in console_msgs if m["type"] == "warning")}
with open(out_json, "w") as f:
    json.dump(result, f, indent=1)
print(json.dumps(result, indent=1))
