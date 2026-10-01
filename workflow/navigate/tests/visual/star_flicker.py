#!/usr/bin/env python3
"""检查背景星闪烁是否符合物理目标 (不需要浏览器).

做法: 从 web/index.html 里抽出真实源码 (FLICK_TIERS / STAR_CLASSES / mixHex / buildStars / TAU),
在 node 里跑一遍, 统计闪烁档比例、幅度区间、频率是否落在亚秒级、位置微抖的幅度与覆盖面,
以及每颗星每帧的 sin 调用次数 (性能红线).

用法:
  uv run python workflow/navigate/tests/visual/star_flicker.py
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
var stars = buildStars();
var ok = true;
function pct(v) { return (v * 100).toFixed(1) + '%'; }
function stat(arr) {
  var a = arr.slice().sort(function (x, y) { return x - y; });
  return [a[0], a[Math.floor(a.length / 2)], a[a.length - 1]];
}
function show(name, arr, unit, lo, hi) {
  var s = stat(arr);
  var inBand = s[0] >= lo - 1e-6 && s[2] <= hi + 1e-6;
  if (!inBand) ok = false;
  console.log('  ' + name + ' ' + s.map(function (v) { return v.toFixed(3); }).join(' .. ') + ' ' + unit +
              ' (期望 ' + lo + ' ~ ' + hi + ')' + (inBand ? '' : '   <- 越界'));
}
console.log('星数 ' + stars.length + ' (1440x900)\n');

// ---- 0. 设计表本身要符合任务书: 70/25/5 ----
var design = FLICK_TIERS.map(function (t) { return t.p; });
var dsum = design.reduce(function (a, v) { return a + v; }, 0);
var dnear = Math.abs(design[0] - 0.70) < 0.03 && Math.abs(design[1] - 0.25) < 0.03 && Math.abs(design[2] - 0.05) < 0.03;
if (!dnear || Math.abs(dsum - 1) > 1e-9) ok = false;
console.log('设计比例 ' + design.map(pct).join(' / ') + ' (任务书 70/25/5), 合计 ' + dsum.toFixed(3) +
            ' -> ' + (dnear && Math.abs(dsum - 1) < 1e-9 ? '符合' : '不符') + '\n');

// ---- 1. 幅度分层比例 (n=1/3/4 正好对应三档) ----
var t0 = stars.filter(function (s) { return s.n === 1; });
var t1 = stars.filter(function (s) { return s.n === 3; });
var t2 = stars.filter(function (s) { return s.n === 4; });
console.log('幅度分层 (按正弦分量数归组):');
[['几乎恒定', t0, FLICK_TIERS[0]], ['轻微', t1, FLICK_TIERS[1]], ['明显', t2, FLICK_TIERS[2]]]
  .forEach(function (row) {
    var share = row[1].length / stars.length;
    // 容差按样本量给: 825 颗星做三分类, 70% 那档的标准差就有 1.6 个点
    var near = Math.abs(share - row[2].p) < 0.04;
    if (!near) ok = false;
    console.log('  ' + row[0] + ' ' + pct(share) + ' (设计 ' + pct(row[2].p) + ')  ' +
                (near ? '' : '<- 偏离'));
  });

// ---- 2. 幅度区间 (绝对 alpha 摆幅) 与深度衰减 ----
// 期望区间 = 设计值 x 深度系数 (0.45~1.0): 摆幅是绝对量, 不随星自身亮度缩放
console.log('\n闪烁幅度 (绝对 alpha 摆幅 ta):');
show('几乎恒定', t0.map(function (s) { return s.ta; }), 'alpha', 0, 0.020);
show('轻微', t1.map(function (s) { return s.ta; }), 'alpha', 0.0135, 0.080);
show('明显', t2.map(function (s) { return s.ta; }), 'alpha', 0.045, 0.220);
// 同档内, 深远层 (z 小 -> 半径小) 的星摆幅应更小
var deep = t2.filter(function (s) { return s.r < 1.0; }).map(function (s) { return s.ta; });
var near = t2.filter(function (s) { return s.r > 1.6; }).map(function (s) { return s.ta; });
if (deep.length && near.length) {
  var dm = deep.reduce(function (a, v) { return a + v; }, 0) / deep.length;
  var nm = near.reduce(function (a, v) { return a + v; }, 0) / near.length;
  console.log('  深远层小星平均摆幅 ' + dm.toFixed(3) + ' vs 近层大星 ' + nm.toFixed(3) +
              ' -> 深远层更弱: ' + (dm < nm ? '成立' : '不成立'));
  if (!(dm < nm)) ok = false;
}

// ---- 3. 频率: 必须落在亚秒级 (Hz), 不是分钟级的呼吸 ----
console.log('\n频率 (Hz):');
var hz = function (w) { return w / TAU; };
show('主频 f1', t1.concat(t2).map(function (s) { return hz(s.f1); }), 'Hz', 0.55, 2.65);
show('次频 f2', t1.concat(t2).map(function (s) { return hz(s.f2); }), 'Hz', 0.70, 3.30);
show('三频 f3', t2.map(function (s) { return hz(s.f3); }), 'Hz', 0.90, 4.10);
show('慢包络 fe', t1.concat(t2).map(function (s) { return hz(s.fe); }), 'Hz', 0.07, 0.25);
var allFast = t1.concat(t2).map(function (s) { return hz(s.f1); }).concat(t1.map(function (s) { return hz(s.f2); }));
console.log('  最快分量 ' + Math.max.apply(null, allFast).toFixed(2) + ' Hz (旧版单频呼吸 0.03~0.22Hz)');

// ---- 4. 位置微抖: 只该出现在"明显"档 ----
var jit = stars.filter(function (s) { return s.ja; });
console.log('\n位置微抖: ' + jit.length + ' 颗 (应等于明显档 ' + t2.length + ' 颗)');
var ja = jit.map(function (s) { return s.ja; });
show('抖幅', ja, 'px', 0.13, 0.80);
var wrong = stars.filter(function (s) { return s.ja && s.n !== 4; }).length;
if (wrong) { console.log('  ' + wrong + ' 颗不该有抖动的星带了抖动 <-'); ok = false; }

// ---- 5. 性能: 每颗每帧的 sin 次数 ----
var sins = stars.reduce(function (acc, s) {
  return acc + (s.n === 1 ? 1 : (s.n === 3 ? 3 : 4 + 2));   // 亮度分量 + (明显档) 位置两项
}, 0) / stars.length;
console.log('\n每颗每帧平均 sin 次数 ' + sins.toFixed(2) + ' (旧版 1.00)');
if (sins > 2.2) { console.log('  <- 超出预算'); ok = false; }

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
        ob = min(x for x in (seg.find("{"), seg.find("[")) if x >= 0)
        oc, cc = ("{", "}") if seg[ob] == "{" else ("[", "]")
        return src[m.start():match_end(src, m.start() + ob, oc, cc) + 1] + ";"

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
