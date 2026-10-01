#!/usr/bin/env python3
"""navigate 展示页 (web/index.html) 的浏览器侧巡检.

起一个临时展示服务, 用 Playwright 开页面, 检查画面/交互/性能/大规模这四类只有跑起来
才知道的事. 这是软检查 (帧率阈值给得宽), 打印报告并以退出码表示是否通过.

用法:
  uv run --project general/access-web/browse python workflow/navigate/tests/visual/render_checks.py

前置: 见同目录 README.md (需要 Playwright + Chromium).
"""

from __future__ import annotations

import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]          # 仓库根 (tests/visual/xxx.py -> 上溯四级)
WEB_SERVER = ROOT / "workflow" / "navigate" / "scripts" / "web_server.py"
BROWSE = ROOT / "general" / "access-web" / "browse"

VIEW = {"width": 1440, "height": 900}
TYPES = ["research", "deliberate", "prototype", "task"]

# 结果收集: (名称, 是否通过, 说明)
RESULTS: list[tuple[str, bool, str]] = []


def report(name: str, ok: bool, detail: str) -> None:
    RESULTS.append((name, ok, detail))
    print("  %s %-22s %s" % ("PASS" if ok else "FAIL", name, detail))


# ---------------------------------------------------------------------------
# 造数据 / 起服务
# ---------------------------------------------------------------------------

def write_roadmap(path: Path, milestones: dict, title: str) -> Path:
    doc = {
        "schema_version": "0.0.1", "title": title, "destination": "巡检用终点",
        "notes": ["巡检笔记"], "unknown_seas": ["海域一"], "off_course": [],
        "milestones": milestones,
    }
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return path


def small_roadmap(path: Path) -> Path:
    """7 个里程碑, 有分层与连线, 够画一张正常的图."""
    spec = [
        ("milestone-01", "research", "已关闭", []),
        ("milestone-02", "task", "进行中", ["milestone-01"]),
        ("milestone-03", "deliberate", "待处理", ["milestone-01"]),
        ("milestone-04", "prototype", "待处理", ["milestone-02"]),
        ("milestone-05", "task", "待处理", ["milestone-03"]),
        ("milestone-06", "research", "待处理", ["milestone-02"]),
        ("milestone-07", "task", "待处理", ["milestone-04", "milestone-05", "milestone-06"]),
    ]
    ms = {i: {"title": "巡检 %s" % i[-2:], "type": t, "question": "q", "status": s, "blocked_by": d}
          for i, t, s, d in spec}
    return write_roadmap(path, ms, "巡检小图")


def chain_roadmap(path: Path, n: int, kind: str = "task") -> Path:
    """一条链: 每层一个节点, 所以所有星球排成一行 (与终点同方位 = 同光照)."""
    ms, prev = {}, None
    for i in range(1, n + 1):
        mid = "m-%02d" % i
        ms[mid] = {"title": "节点 %02d" % i, "type": kind, "question": "q",
                   "status": "待处理", "blocked_by": [] if prev is None else [prev]}
        prev = mid
    return write_roadmap(path, ms, "同型一行")


def random_roadmap(path: Path, n: int, seed: int = 11) -> Path:
    rnd = random.Random(seed)
    ms = {}
    for i in range(1, n + 1):
        mid = "m-%05d" % i
        deps = []
        if i > 1:
            deps = sorted({"m-%05d" % rnd.randint(1, i - 1) for _ in range(rnd.choice([1, 1, 1, 2, 2, 3]))})
        ms[mid] = {"title": "里程碑 %05d" % i, "type": rnd.choice(TYPES), "question": "q",
                   "status": rnd.choice(["待处理", "待处理", "进行中", "已关闭"]), "blocked_by": deps}
    return write_roadmap(path, ms, "%d 个里程碑" % n)


def start_server(runtime_dir: Path) -> int:
    env = dict(os.environ, NAVIGATE_WEB_RUNTIME_DIR=str(runtime_dir))
    out = subprocess.run([sys.executable, str(WEB_SERVER), "start"], env=env,
                         capture_output=True, text=True, timeout=60)
    body = json.loads(out.stdout.strip().splitlines()[-1])
    if not body.get("success"):
        raise SystemExit("展示服务启动失败: %s" % out.stdout + out.stderr)
    return int(body["port"])


def stop_server(runtime_dir: Path) -> None:
    env = dict(os.environ, NAVIGATE_WEB_RUNTIME_DIR=str(runtime_dir))
    subprocess.run([sys.executable, str(WEB_SERVER), "stop"], env=env,
                   capture_output=True, text=True, timeout=60)


def url(port: int, roadmap: Path) -> str:
    return "http://127.0.0.1:%d/?roadmap=%s" % (port, roadmap)


# ---------------------------------------------------------------------------
# 页面侧小工具
# ---------------------------------------------------------------------------

FPS_JS = """() => new Promise(res => { const ts = []; let n = 0;
  (function f() { ts.push(performance.now()); n++; if (n < 100) requestAnimationFrame(f);
    else res(+((n - 1) * 1000 / (ts[n - 1] - ts[0])).toFixed(1)); })(); })"""

PATCH_JS = """([x, y]) => { const c = document.getElementById('cosmos'), g = c.getContext('2d'), d = devicePixelRatio;
  return Array.from(g.getImageData(Math.round((x - 25) * d), Math.round((y - 25) * d),
                                   Math.round(50 * d), Math.round(50 * d)).data); }"""

DIFF_JS = """([a, b]) => { let s = 0; for (let i = 0; i < a.length; i += 4)
  s += Math.abs(a[i] - b[i]) + Math.abs(a[i + 1] - b[i + 1]) + Math.abs(a[i + 2] - b[i + 2]);
  return +(s / (a.length / 4) / 3).toFixed(3); }"""

HASH_JS = """() => { const d = document.getElementById('cosmos').toDataURL('image/png');
  let h = 2166136261; for (let i = 0; i < d.length; i += 97) { h ^= d.charCodeAt(i); h = Math.imul(h, 16777619); }
  return (h >>> 0).toString(16); }"""

# 画布计数 + 长帧记录: 必须在页面脚本之前装
INIT_JS = """(() => {
  window.__nc = 0; window.__long = [];
  const o = document.createElement.bind(document);
  document.createElement = function (t) { if (String(t).toLowerCase() === 'canvas') window.__nc++; return o(t); };
  let last = performance.now();
  (function f(ts) { const d = ts - last; last = ts; if (d > 50) window.__long.push(Math.round(d)); requestAnimationFrame(f); })();
})()"""

HALVES_JS = """([cx, cy, pad]) => {           // 盘内左右两半的平均亮度
  const c = document.getElementById('cosmos'), g = c.getContext('2d'), dpr = devicePixelRatio;
  const d = g.getImageData(Math.round((cx - pad) * dpr), Math.round((cy - pad) * dpr),
                           Math.round(2 * pad * dpr), Math.round(2 * pad * dpr)).data;
  const n = Math.round(2 * pad * dpr);
  let L = 0, R = 0, lc = 0, rc = 0;
  for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
    const dx = (i - n / 2) / (n / 2), dy = (j - n / 2) / (n / 2), rad = Math.hypot(dx, dy);
    if (rad > 0.72 || rad < 0.12) continue;
    const p = (j * n + i) * 4, lum = 0.2126 * d[p] + 0.7152 * d[p + 1] + 0.0722 * d[p + 2];
    if (dx < 0) { L += lum; lc++; } else { R += lum; rc++; }
  }
  return { left: +(L / lc).toFixed(1), right: +(R / rc).toFixed(1) };
}"""


def run(port: int, fixtures: dict) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--force-device-scale-factor=1"])

        # ---- 常规视图: 帧率 / 交互 / 动效恒开 ----
        page = browser.new_page(viewport=VIEW)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:150]))
        page.goto(url(port, fixtures["small"]))
        page.wait_for_timeout(1800)
        report("常规视图帧率", float(page.evaluate(FPS_JS)) >= 55, "%s fps (1440x900, 期望 >= 55)" % page.evaluate(FPS_JS))

        page.mouse.move(707, 447)
        page.mouse.click(707, 447)
        page.wait_for_timeout(400)
        opened = page.evaluate("() => !document.getElementById('panel').classList.contains('hidden')")
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
        closed = page.evaluate("() => document.getElementById('panel').classList.contains('hidden')")
        report("交互 (点选/关闭)", bool(opened and closed), "点星球开面板 %s, Esc 关闭 %s" % (opened, closed))

        # 天幕不随视角: 采样点避开地图内容 (星球/连线/未知海域的雾都在中上部)
        # 动效固定恒开: 即使系统省动画, 画面也应继续闪 (不再跟随 prefers-reduced-motion)
        page.emulate_media(reduced_motion="reduce")
        page.wait_for_timeout(400)
        anim_a = page.evaluate(HASH_JS)
        page.wait_for_timeout(900)
        anim_b = page.evaluate(HASH_JS)
        report("省动画下仍闪烁 (固定)", anim_a != anim_b,
               "两次采样不同 (动效恒开)" if anim_a != anim_b else "画面被冻结")

        sky_pts = [(1300, 700), (150, 300)]
        before = [page.evaluate(PATCH_JS, list(pt)) for pt in sky_pts]
        # 动效恒开后, 单纯闪烁也会让像素微变: 先测无平移时的噪声底, 平移后再比
        page.wait_for_timeout(300)
        noise = max(page.evaluate(DIFF_JS, [b, page.evaluate(PATCH_JS, list(pt))])
                    for b, pt in zip(before, sky_pts))
        page.mouse.move(700, 450)
        page.mouse.down()
        page.mouse.move(280, 300, steps=8)
        page.mouse.up()
        page.wait_for_timeout(300)
        deltas = [page.evaluate(DIFF_JS, [b, page.evaluate(PATCH_JS, list(pt))])
                  for b, pt in zip(before, sky_pts)]
        # 星空钉在屏幕上: 平移后差异应仍在闪烁噪声量级, 不应出现整片位移的大差异
        limit = max(0.25, noise * 4 + 0.05)
        report("天幕不随视角移动", max(deltas) <= limit,
               "平移后差值 %s vs 闪烁噪声底 %.3f (阀值 %.3f)" % (deltas, noise, limit))

        # 星球光照: 同型一行 (与终点同方位, 光照一致) -> 右半 (朝终点) 应比左半亮
        page.emulate_media(reduced_motion="no-preference")
        page.goto(url(port, fixtures["chain"]))
        page.wait_for_timeout(1600)
        page.evaluate("""() => { window.__lbl = []; const P = CanvasRenderingContext2D.prototype, o = P.fillText;
          P.fillText = function (t, x, y) { window.__lbl.push([String(t), Math.round(x), Math.round(y)]); return o.apply(this, arguments); }; }""")
        page.wait_for_timeout(300)
        page.emulate_media(reduced_motion="reduce")
        page.wait_for_timeout(400)
        raw = [l for l in page.evaluate("() => window.__lbl") if l[0].startswith("节点")]
        seen, labels = set(), []
        for l in raw:
            if (l[1], l[2]) not in seen:
                seen.add((l[1], l[2]))
                labels.append(l)
        labels.sort(key=lambda l: l[1])
        halves = [page.evaluate(HALVES_JS, [l[1], l[2] - 30, 22]) for l in labels[:3]]
        ok_light = all(h["right"] > h["left"] for h in halves) and bool(halves)
        report("星球光照朝向终点", ok_light,
               "左/右半亮度 " + ", ".join("%.0f/%.0f" % (h["left"], h["right"]) for h in halves))

        # 大规模: 贴图数与加载期卡顿
        scaled = browser.new_page(viewport=VIEW)
        scaled.add_init_script(script=INIT_JS)
        scaled.goto(url(port, fixtures["big"]))
        scaled.wait_for_timeout(6000)
        stat = scaled.evaluate("() => ({ canvas: window.__nc, worst: Math.max(0, ...window.__long) })")
        scaled_fps = float(scaled.evaluate(FPS_JS))
        report("1000 个里程碑贴图数", stat["canvas"] <= 60,
               "%d 张画布 (期望 <= 60: 最小档按类型共用, 不随里程碑数增长)" % stat["canvas"])
        report("1000 个里程碑加载", stat["worst"] <= 500, "最坏卡顿帧 %dms (期望 <= 500)" % stat["worst"])
        print("       (参考) 1000 个里程碑全展开 %s fps — 放大后因视口裁剪回到 60fps" % scaled_fps)

        report("无 JS 报错", not errors, errors[0] if errors else "pageerror 0 条")
        browser.close()


# ---------------------------------------------------------------------------

def main() -> int:
    if not BROWSE.exists():
        raise SystemExit("找不到 Playwright 环境: %s" % BROWSE)
    tmp = Path(tempfile.mkdtemp(prefix="navigate-visual-"))
    try:
        fixtures = {
            "small": small_roadmap(tmp / "small.json"),
            "chain": chain_roadmap(tmp / "chain.json", 5),
            "big": random_roadmap(tmp / "big.json", 1000),
        }
        runtime = tmp / "runtime"
        runtime.mkdir()
        port = start_server(runtime)
        print("展示服务 127.0.0.1:%d, 数据目录 %s\n" % (port, tmp))
        try:
            run(port, fixtures)
        finally:
            stop_server(runtime)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = [r for r in RESULTS if not r[1]]
    print("\n%d 项检查, %d 项通过, %d 项失败" % (len(RESULTS), len(RESULTS) - len(failed), len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
