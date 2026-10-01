#!/usr/bin/env python3
"""检查星空颜色是否按黑体色温表写实选取 (不需要浏览器).

做法: 从 web/index.html 里**抽出真实源码** (STAR_CLASSES / mixHex / buildStars / mulberry32),
在 node 里跑一遍, 统计各色温档占比、尺寸与亮度是否跟色温挂钩、色相覆盖范围.

用法:
  uv run python workflow/navigate/tests/visual/star_colors.py
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
INDEX = ROOT / "workflow" / "navigate" / "web" / "index.html"

ANALYSIS = r"""
function hex2hsl(h) {
  var n = parseInt(h.slice(1), 16), r = ((n >> 16) & 255) / 255, g = ((n >> 8) & 255) / 255, b = (n & 255) / 255;
  var mx = Math.max(r, g, b), mn = Math.min(r, g, b), l = (mx + mn) / 2, hh = 0, s = 0;
  if (mx !== mn) {
    var d = mx - mn;
    s = l > 0.5 ? d / (2 - mx - mn) : d / (mx + mn);
    hh = mx === r ? (g - b) / d + (g < b ? 6 : 0) : (mx === g ? (b - r) / d + 2 : (r - g) / d + 4);
    hh *= 60;
  }
  return [hh, s, l];
}
function dist(a, b) {
  var p = parseInt(a.slice(1), 16), q = parseInt(b.slice(1), 16);
  return Math.abs(((p >> 16) & 255) - ((q >> 16) & 255))
       + Math.abs(((p >> 8) & 255) - ((q >> 8) & 255))
       + Math.abs((p & 255) - (q & 255));
}
function classOf(c) {
  var best = 0, bd = 1e9;
  STAR_CLASSES.forEach(function (k, i) { var d = dist(k.c, c); if (d < bd) { bd = d; best = i; } });
  return best;
}
var stars = buildStars();
var ok = true;
console.log('星数 ' + stars.length + ' (1440x900)');
console.log('\n色温档            真实比例  实际占比  平均半径  平均亮度');
STAR_CLASSES.forEach(function (k, i) {
  var g = stars.filter(function (s) { return classOf(s.c) === i; });
  var ar = g.length ? (g.reduce(function (a, s) { return a + s.r; }, 0) / g.length) : 0;
  var aa = g.length ? (g.reduce(function (a, s) { return a + s.a; }, 0) / g.length) : 0;
  var share = 100 * g.length / stars.length;
  var near = Math.abs(share / 100 - k.p) < 0.05;           // 实际占比与设定比例偏差 < 5 个点
  if (!near) ok = false;
  console.log('  ' + k.c + '  ' + (100 * k.p).toFixed(0).padStart(6) + '%  ' +
              share.toFixed(1).padStart(7) + '%  ' + ar.toFixed(2).padStart(8) + '  ' + aa.toFixed(2).padStart(8) +
              (near ? '' : '   <- 偏离'));
});
// 尺寸/亮度应随色温单调递增 (越蓝越大越亮)
var byT = STAR_CLASSES.map(function (k, i) {
  var g = stars.filter(function (s) { return classOf(s.c) === i; });
  return { r: g.reduce(function (a, s) { return a + s.r; }, 0) / g.length,
           a: g.reduce(function (a, s) { return a + s.a; }, 0) / g.length };
});
// 设计值本身必须随色温单调递增 (每个色温档天生的相对大小/亮度系数)
var designMono = STAR_CLASSES.every(function (k, i) {
  return i === 0 || (k.s >= STAR_CLASSES[i - 1].s && k.b >= STAR_CLASSES[i - 1].b);
});
// 实测均值只看两端 (中间档每次抽样的样本不大, 均值会抖)
var mono = designMono && byT[byT.length - 1].a > byT[0].a * 1.2 && byT[byT.length - 1].r > byT[0].r * 1.2;
if (!designMono) console.log('色温档的设计系数不单调 <-');
var ends = byT[byT.length - 1].r > byT[0].r * 1.5 && byT[byT.length - 1].a > byT[0].a * 1.3;
console.log('\n越蓝越大越亮 (主序星规律): ' + (mono ? '成立' : '不成立') +
            '; 两端对比: 半径 ' + byT[0].r.toFixed(2) + ' -> ' + byT[byT.length - 1].r.toFixed(2) +
            ', 亮度 ' + byT[0].a.toFixed(2) + ' -> ' + byT[byT.length - 1].a.toFixed(2) +
            ' (' + (ends ? '两端差得开' : '两端没拉开') + ')');
if (!mono || !ends) ok = false;
// 色相覆盖与"没有绿色"
var hues = stars.map(function (s) { return hex2hsl(s.c)[0]; });
var lo = Math.min.apply(null, hues), hi = Math.max.apply(null, hues);
var green = hues.filter(function (h) { return h > 70 && h < 160; }).length;
console.log('色相范围 ' + lo.toFixed(0) + ' .. ' + hi.toFixed(0) + ' 度; 落在绿区 (70..160) 的星: ' + green +
            ' 颗 (黑体色不经过绿色, 期望 0)');
if (green !== 0 || lo > 30 || hi < 220) ok = false;
var colors = {}; stars.forEach(function (s) { colors[s.c] = 1; });
console.log('不同颜色 ' + Object.keys(colors).length + ' 种');
console.log('\n' + (ok ? 'PASS' : 'FAIL'));
process.exit(ok ? 0 : 1);
"""


def extract_blocks(src: str) -> list[str]:
    def match_end(text: str, start: int, oc: str, cc: str) -> int:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == oc:
                depth += 1
            elif text[i] == cc:
                depth -= 1
                if depth == 0:
                    return i
        raise SystemExit("括号不配对")

    def function(name: str) -> str:
        m = re.search(r"^function " + name + r"\s*\(", src, re.M)
        if not m:
            raise SystemExit("找不到函数 " + name)
        return src[m.start():match_end(src, src.index("{", m.start()), "{", "}") + 1]

    def variable(name: str) -> str:
        m = re.search(r"^var " + name + r"\s*=", src, re.M)
        if not m:
            raise SystemExit("找不到变量 " + name)
        seg = src[m.start():]
        candidates = [x for x in (seg.find("{"), seg.find("[")) if x >= 0]
        ob = min(candidates)
        oc, cc = ("{", "}") if seg[ob] == "{" else ("[", "]")
        return src[m.start():match_end(src, m.start() + ob, oc, cc) + 1] + ";"

    # buildStars 现在还依赖闪烁档表与 TAU, 一并抽出 (否则 node 里会 ReferenceError)
    return [variable("FLICK_TIERS"), variable("STAR_CLASSES"), variable("TAU"),
            function("mulberry32"), function("mixHex"), function("buildStars")]


def main() -> int:
    src = INDEX.read_text(encoding="utf-8")
    script = "var state = { cw: 1440, ch: 900 };\n" + "\n".join(extract_blocks(src)) + "\n" + ANALYSIS
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(script)
        path = fh.name
    proc = subprocess.run(["node", path], capture_output=True, text=True)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
