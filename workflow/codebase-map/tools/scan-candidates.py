#!/usr/bin/env python3
"""升级上游 tag 后, 重新发现需要翻译的文案候选 (词表维护辅助, 不参与构建).

用法: CC_ROOT=<上游 app 目录> python3 scan-candidates.py <ts|lit> [输出.tsv]
  ts  : .ts 里疑似用户文案的字面量 (milestone-13 ts_strings.py 同一启发式 + 噪音过滤),
        输出 (文件, 次数, 属性名, 是否throw, 文本), 人工过筛后补进 i18n/zh-ts.txt
  lit : .html 绑定/插值内的整条字面量, 人工过筛后补进 i18n/zh-lit.txt
模板通道 A 的候选直接看 localize.py --report 的 untranslated 字段, 不用本脚本.
"""

import os
import re
import sys
from collections import Counter

ROOT = os.environ.get("CC_ROOT")
if not ROOT:
    raise SystemExit("用法: CC_ROOT=<上游 visualization/app 目录> python3 scan-candidates.py <ts|lit> [输出.tsv]")

TS_NOISE = [
    re.compile(r"^@[\w-]+/"), re.compile(r"^[<]."),
    re.compile(r"^document:"), re.compile(r"^window:"),
    re.compile(r"^-?mouse(enter|leave|down|up|move)$"), re.compile(r"^(contextmenu|click|wheel|keydown|keyup|input|change)$"),
    re.compile(r"^\(.*\)$"), re.compile(r"^[a-z]+[-:][a-z-]"),
    re.compile(r"^(fa[srbl]?|fa) "), re.compile(r"^fa-"),
    re.compile(r"^rgba?\(|^hsl|^#[0-9a-fA-F]{3,8}$"),
    re.compile(r"^translate\(|^rotate|^scale|^matrix"), re.compile(r"^linear-gradient"), re.compile(r"^var\("),
    re.compile(r"^:"), re.compile(r"^[A-Z_]{4,}$"),
    re.compile(r"^-?\d+(\.\d+)?(%|px|deg|s|ms|rem|em|vh|vw|fr)?$"),
    re.compile(r"^(px|em|rem|%|deg|s|ms|vh|vw|fr|none|auto|inherit|initial|flex|block|grid|center|true|false|null|undefined)$"),
]


def strip_comments(src):
    out = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            j = src.find("\n", i)
            i = n if j < 0 else j
        elif c == "/" and i + 1 < n and src[i + 1] == "*":
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append(re.sub(r"[^\n]", " ", src[i:j]))
            i = j
        elif c in "\"'`":
            j = i + 1
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == c:
                    j += 1
                    break
                j += 1
            out.append(src[i:j])
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


def scan_ts():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import ts_strings

    pair, prop_of, throw_of = Counter(), {}, {}
    for dirpath, _, names in os.walk(ROOT):
        if "node_modules" in dirpath.split(os.sep):
            continue
        for fn in sorted(names):
            if not fn.endswith(".ts") or fn.endswith((".spec.ts", ".e2e.ts", ".po.ts", ".mock.ts")):
                continue
            if "mocks" in dirpath.split(os.sep) or "testdata" in dirpath.split(os.sep):
                continue
            for it in ts_strings.scan(os.path.join(dirpath, fn)):
                key = (it["file"], it["text"])
                pair[key] += 1
                if it["prop"]:
                    prop_of.setdefault(key, set()).add(it["prop"])
                if it["in_throw"]:
                    throw_of[key] = True
    rows = []
    for (file, text), n in pair.items():
        if any(rx.match(text) for rx in TS_NOISE):
            continue
        props = ",".join(sorted(prop_of.get((file, text), []))) or "-"
        throw = "throw" if throw_of.get((file, text)) else "-"
        rows.append((file, n, props, throw, text.replace("\n", "\\n")))
    return sorted(rows)


LIT_RE = re.compile(r'"((?:[^"\\\n]|\\.)*)"|\'((?:[^\'\\\n]|\\.)*)\'')
WORD_RE = re.compile(r"[A-Za-z]{2,}")


def scan_lit():
    hits = Counter()
    ctx = {}
    for dirpath, _, names in os.walk(ROOT):
        if "node_modules" in dirpath.split(os.sep):
            continue
        for fn in sorted(names):
            if not fn.endswith(".html"):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, ROOT)
            text = open(path, encoding="utf-8").read()
            spans = [(m.start(), m.end(), m.group(0)) for m in re.finditer(r"\{\{.*?\}\}", text, re.S)]
            spans += [(m.start(2), m.end(2), m.group(2)) for m in re.finditer(r'([^\s=<>"\']+)="([^"]*)"', text)
                      if m.group(1).startswith(("[", "(", "*", "#", "bind-", "on-", "let-"))]
            for _s, _e, body in spans:
                for m in LIT_RE.finditer(body):
                    for g in (1, 2):
                        if m.group(g) is None:
                            continue
                        lit = m.group(g)
                        if not WORD_RE.search(lit) or "${" in lit:
                            break
                        if re.match(r"^[a-z0-9-]+(/[a-z0-9-]+)*$", lit):
                            break
                        hits[(rel, lit)] += 1
                        ctx.setdefault((rel, lit), body[:120])
                        break
    return [(rel, n, ctx[(rel, lit)].replace("\t", " "), "-", lit) for (rel, lit), n in sorted(hits.items())]


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "ts"
    rows = scan_ts() if mode == "ts" else scan_lit()
    out = sys.argv[2] if len(sys.argv) > 2 else None
    lines = ["\t".join(map(str, r)) for r in rows]
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print("written:", out)
    else:
        print("\n".join(lines))
    print("%s 候选: %d 条" % (mode, len(rows)))


if __name__ == "__main__":
    main()
