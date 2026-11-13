#!/usr/bin/env python3
"""最小 .ts 文案替换: 只按 (文件路径, 整条字符串字面量) 白名单做精确替换.

用法:
  python3 localize_ts.py --apply|--report|--check
词表 (i18n/zh-ts.txt) 每行三列, TAB 分隔:
  相对 visualization/app 的 .ts 路径 <TAB> 英文原文 (整条字面量) <TAB> 中文

纪律:
  * 只替换"整条字面量完全相等"的字符串, 绝不做子串替换或正则;
  * 只在该行所属文件命中时替换, 并逐条打印 (file:line) 供人工复核;
  * 含 ${} 的模板字面量一律跳过并报告 (需要人工处理占位符顺序);
  * 跳过 *.spec.ts / *.e2e.ts / *.po.ts / mocks;
  * --allow-any: 同样的纪律用于 .html 里的绑定表达式 ({{ }} 与 [attr]="..." 中的字面量);
  * 幂等: 已含 CJK 的字面量跳过.
"""

import argparse
import json
import os
import re
import sys
from collections import Counter

ROOT = os.environ.get("CC_ROOT", "/tmp/cc-build/src/visualization/app")
DICT = os.environ.get("CC_TS_DICT", "/tmp/cc-build/i18n/zh-ts.txt")
OUT = os.environ.get("CC_TS_STAT", "/tmp/cc-build/ts-apply-report.json")

CJK_RE = re.compile(r"[\u3400-\u9fff]")
LIT_RE = re.compile(r'"((?:[^"\\\n]|\\.)*)"|\'((?:[^\'\\\n]|\\.)*)\'|`((?:[^`\\]|\\.)*)`')


def strip_comments(src):
    """注释替换为空格 (保留长度与换行), 字符串原样保留."""
    out = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            j = src.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
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


def iter_literals(src):
    """产出字符串字面量 (start, end, body). 遇到 '"\'...\'"' 这种嵌套再拆一层."""
    for m in LIT_RE.finditer(src):
        for g in (1, 2, 3):
            if m.group(g) is not None:
                start = m.start(g)
                body = m.group(g)
                break
        stack = [(start, body)]
        while stack:
            st, bd = stack.pop()
            yield st, st + len(bd), bd
            m2 = re.fullmatch(r"(['\"])(.*)\1", bd, re.S)
            if m2:
                stack.append((st + 1, m2.group(2)))


def load_dict(path):
    entries, dups = [], set()
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) != 3:
                raise SystemExit("词表第 %d 行必须是 3 列 TAB 分隔: %r" % (lineno, line))
            key = (parts[0], parts[1])
            if key in dups:
                raise SystemExit("词表第 %d 行重复: %r" % (lineno, line))
            dups.add(key)
            entries.append({"file": parts[0], "en": parts[1], "zh": parts[2], "line": lineno})
    return entries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--allow-any", action="store_true", help="允许在任意文本文件(如 .html 模板)里按整条字面量精确替换")
    args = ap.parse_args()

    entries = load_dict(DICT)
    by_file = {}
    for e in entries:
        by_file.setdefault(e["file"], []).append(e)

    report = {"replaced": [], "missing": [], "errors": [], "skipped_template": [], "hits": Counter()}
    touched = set()
    for rel, items in by_file.items():
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            report["errors"].append("文件不存在: %s" % rel)
            continue
        if not args.allow_any and not rel.endswith(".ts"):
            report["errors"].append("不是 .ts 文件 (加 --allow-any 才允许): %s" % rel)
            continue
        if re.search(r"\.(spec|e2e|po)\.ts$", rel) or "/mocks/" in rel:
            report["errors"].append("拒绝改测试/夹具文件: %s" % rel)
            continue
        raw = open(path, encoding="utf-8").read()
        src = strip_comments(raw)
        edits = []
        for e in items:
            want = e["en"]
            found = 0
            for start, _end, body in iter_literals(src):
                if body != want:
                    continue
                if "${" in body:
                    report["skipped_template"].append("%s: 含 ${} 的模板字面量, 需人工: %r" % (rel, body))
                    continue
                if CJK_RE.search(e["zh"]):
                    edits.append((start, start + len(body), e["zh"]))
                    report["hits"][(rel, want)] += 1
                    found += 1
                    report["replaced"].append({"file": rel, "line": raw.count("\n", 0, start) + 1, "en": want, "zh": e["zh"]})
            if found == 0:
                report["missing"].append({"file": rel, "en": want})
            elif found > 1:
                report["errors"].append("%s: 同一字面量命中 %d 次, 请人工确认是否都该翻: %r" % (rel, found, want))
        if args.apply and edits:
            out = raw
            for start, end, new in sorted(edits, key=lambda x: -x[0]):
                out = out[:start] + new + out[end:]
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(out)
            touched.add(rel)

    report["hits"] = {"%s :: %s" % k: v for k, v in report["hits"].items()}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)

    print(
        "词表 %d 条, 命中 %d 条 (%d 处), 未命中 %d 条, 已改文件 %d 个"
        % (len(entries), len(report["replaced"]), sum(report["hits"].values()), len(report["missing"]), len(touched))
    )
    for r in report["replaced"]:
        print("  %s:%d %r -> %r" % (r["file"], r["line"], r["en"], r["zh"]))
    for e in report["errors"]:
        print("ERROR", e)
    for e in report["missing"]:
        print("MISS", e["file"], "::", e["en"])
    if args.check:
        return 1 if (report["errors"] or report["missing"]) else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
