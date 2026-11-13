#!/usr/bin/env python3
"""CodeCharta .ts / 绑定表达式 文案替换: 只按 (文件路径, 整条字符串字面量) 白名单做精确替换.

用法:
  python3 localize_ts.py --apply|--report|--check
词表 (i18n/zh-ts.txt) 每行三列, TAB 分隔:
  相对 visualization/app 的路径 <TAB> 英文原文 (整条字面量) <TAB> 中文

在 milestone-13 原型基础上的受控扩展 (milestone-21, 其余纪律不变):
1. 模板字面量 (反引号串) 支持: 词表键里每个 ${...} 表达式写成占位符 ⟦0⟧ ⟦1⟧ (按出现顺序),
   译文必须恰好含每个占位符一次, 允许重排位置 (中文语序); 表达式本体原样保留, 不做任何改写.
   真实换行在词表键/译文里写成 \\n (两个字符), 匹配时与字面量里的真实换行对齐.
   含 ` 或 \\${ 等转义的模板字面量仍一律跳过并报告.
2. 译文列写 (空) 表示替换为空字符串: 仅用于拼接句的可译前段/尾段 (例: 'Show ' + word + ' again').
3. 两轮替换, 各按最新文本定位: 第一轮处理普通字面量与不含 ${} 的反引号串 (含模板字面量内层),
   第二轮处理含 ${} 的模板字面量 (重建时表达式取自当前文本, 因此外层会保留内层已译的中文).
   除这两轮外不做任何子串/正则替换; 同一轮内嵌套命中外层优先, 内层放弃并告警.

其余纪律 (承袭原型):
  * 只替换"整条字面量完全相等"的字符串, 绝不做子串替换或正则;
  * 只在该行所属文件命中时替换, 并逐条打印 (file:line) 供人工复核;
  * 同一字面量在同一文件命中多次 -> 报 ERROR 要求人看 (仍全部替换, 需人工确认都该翻);
  * 跳过 *.spec.ts / *.e2e.ts / *.po.ts / mocks;
  * --allow-any: 同样的纪律用于 .html 里的绑定表达式 ({{ }} 与 [attr]="..." 中的字面量);
  * 幂等: 配合构建脚本先 git checkout 还原再 apply; 对已含 CJK 的字面量不再命中.
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
QUOTED_RE = re.compile(r'"((?:[^"\\\n]|\\.)*)"|\'((?:[^\'\\\n]|\\.)*)\'')
PLACEHOLDER_RE = re.compile(r"\$\{([^{}]*)\}")
EMPTY_MARKER = "(空)"


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
    """产出字符串字面量 (start, end, body, is_backtick).

    任意字面量体内部再扫一层引号字面量并逐个产出 (backtick=False):
    覆盖 .html 绑定里的混合表达式 (如 [label]="a ? 'x' : 'y'") 与模板字面量内层;
    各层区间可嵌套, 由调用方做重叠取舍.
    """
    work = []
    for m in LIT_RE.finditer(src):
        for g in (1, 2, 3):
            if m.group(g) is not None:
                work.append((m.start(g), m.group(g), g == 3))
                break
    while work:
        st, bd, bt = work.pop()
        yield st, st + len(bd), bd, bt
        for m2 in QUOTED_RE.finditer(bd):
            g2 = 1 if m2.group(1) is not None else 2
            work.append((st + m2.start(g2), m2.group(g2), False))


def normalize(body):
    """把字面量体变成词表键: ${...} -> ⟦n⟧, 真实换行 -> \\n (两个字符)."""
    counter = {"n": 0}

    def repl(_m):
        token = "⟦%d⟧" % counter["n"]
        counter["n"] += 1
        return token

    return PLACEHOLDER_RE.sub(repl, body).replace("\n", "\\n")


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
            zh = "" if parts[2] == EMPTY_MARKER else parts[2]
            entries.append({"file": parts[0], "en": parts[1], "zh": zh, "line": lineno})
    return entries


def validate_entry(e, errors):
    """词表行的静态校验: 占位符成对出现, 模板字面量才允许占位符, 译文必须含中文 (除 (空))."""
    en, zh, lineno = e["en"], e["zh"], e["line"]
    is_template = "⟦" in en
    phs_en = sorted(re.findall(r"⟦(\d+)⟧", en))
    phs_zh = sorted(re.findall(r"⟦(\d+)⟧", zh))
    if is_template != ("⟦" in zh):
        errors.append("词表第 %d 行: 占位符必须成对出现在键和译文中: %r" % (lineno, en))
        return False
    if phs_en != phs_zh:
        errors.append("词表第 %d 行: 译文占位符与键不一致: %r -> %r" % (lineno, en, zh))
        return False
    if not is_template and phs_en:
        errors.append("词表第 %d 行: 非模板字面量不允许占位符: %r" % (lineno, en))
        return False
    if "`" in zh or "${" in zh:
        errors.append("词表第 %d 行: 译文里不允许反引号或 ${ : %r" % (lineno, zh))
        return False
    if zh != "" and not CJK_RE.search(zh):
        errors.append("词表第 %d 行: 译文不含中文 (空翻译请写 (空)): %r" % (lineno, en))
        return False
    return True


def render_template(zh, body):
    """按当前模板体提取 ${...} 表达式 (可能已含内层译文), 按译文 ⟦n⟧ 顺序重建."""
    exprs = ["${%s}" % m.group(1) for m in PLACEHOLDER_RE.finditer(body)]
    return re.sub(r"⟦(\d+)⟧", lambda m: exprs[int(m.group(1))], zh)


def pass_edits(src, items, pass_no, report, rel):
    """单轮: 找当前轮允许的字面量并产出编辑 (start, end, new_body).

    轮 1: 普通字面量与不含 ${} 的反引号串; 轮 2: 含 ${} 的模板字面量.
    """
    edits = []
    for e in items:
        for start, _end, body, backtick in iter_literals(src):
            if normalize(body) != e["en"]:
                continue
            in_pass = (not backtick or "${" not in body) if pass_no == 1 else (backtick and "${" in body)
            if not in_pass:
                continue
            if backtick and re.search(r"(?<!\\)\\[`${}]", body):
                report["skipped_template"].append("%s: 含转义的模板字面量, 需人工: %r" % (rel, body[:80]))
                continue
            if backtick:
                new_body = render_template(e["zh"], body)
            else:
                new_body = e["zh"]
            edits.append({"start": start, "end": start + len(body), "new": new_body, "en": e["en"], "zh": e["zh"]})
    return edits


def resolve_overlaps(edits, report, rel):
    """同一轮内嵌套命中外层优先: 内层放弃并告警; 部分重叠视为异常丢弃."""
    kept, last_end = [], -1
    for edit in sorted(edits, key=lambda x: (x["start"], -(x["end"] - x["start"]))):
        if edit["start"] >= last_end:
            kept.append(edit)
            last_end = edit["end"]
        elif edit["end"] <= last_end:
            report["skipped_template"].append(
                "%s: 嵌套字面量随外层一起替换, 内层词条本轮不单独改: %r" % (rel, edit["en"])
            )
        else:
            report["errors"].append("%s: 字面量部分重叠, 丢弃需人工检查: %r" % (rel, edit["en"]))
    return kept


def apply_entries(raw, items, pass_no, report, hits):
    """单轮替换: 逐文件收集编辑 -> 重叠取舍 -> 按位置倒序写回."""
    by_file = {}
    for e in items:
        by_file.setdefault(e["file"], []).append(e)
    for rel, file_items in by_file.items():
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            report["errors"].append("文件不存在: %s" % rel)
            continue
        if re.search(r"\.(spec|e2e|po)\.ts$", rel) or re.search(r"(^|/)(mocks|mock)\.ts$", rel) or "/mocks/" in rel:
            report["errors"].append("拒绝改测试/夹具文件: %s" % rel)
            continue
        src = strip_comments(raw)
        edits = pass_edits(src, file_items, pass_no, report, rel)
        kept = resolve_overlaps(edits, report, rel)
        for edit in kept:
            hits[(rel, edit["en"])] += 1
            report["replaced"].append(
                {"file": rel, "line": raw.count("\n", 0, edit["start"]) + 1, "en": edit["en"], "zh": edit["zh"]}
            )
        if kept:
            new_raw = raw
            for edit in sorted(kept, key=lambda x: -x["start"]):
                new_raw = new_raw[: edit["start"]] + edit["new"] + new_raw[edit["end"] :]
            raw = new_raw
    return raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--allow-any", action="store_true", help="允许在任意文本文件(如 .html 模板)里按整条字面量精确替换")
    args = ap.parse_args()

    entries = load_dict(DICT)
    report = {"replaced": [], "missing": [], "errors": [], "skipped_template": [], "hits": Counter()}
    hits = Counter()

    static_errors = []
    valid_entries = []
    for e in entries:
        if validate_entry(e, static_errors):
            valid_entries.append(e)
    for err in static_errors:
        print("ERROR", err)
    report["errors"].extend(static_errors)

    allowed_files = set(e["file"] for e in valid_entries)
    files = {}
    for rel in allowed_files:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            report["errors"].append("文件不存在: %s" % rel)
            continue
        if not args.allow_any and not rel.endswith(".ts"):
            report["errors"].append("不是 .ts 文件 (加 --allow-any 才允许): %s" % rel)
            continue
        if re.search(r"\.(spec|e2e|po)\.ts$", rel) or re.search(r"(^|/)(mocks|mock)\.ts$", rel) or "/mocks/" in rel:
            report["errors"].append("拒绝改测试/夹具文件: %s" % rel)
            continue
        files[rel] = open(path, encoding="utf-8").read()

    for rel in list(files):
        raw = files[rel]
        rel_items = [e for e in valid_entries if e["file"] == rel]
        raw = apply_entries(raw, rel_items, pass_no=1, report=report, hits=hits)
        raw = apply_entries(raw, rel_items, pass_no=2, report=report, hits=hits)
        if args.apply and raw != files[rel]:
            with open(os.path.join(ROOT, rel), "w", encoding="utf-8") as fh:
                fh.write(raw)

    for e in valid_entries:
        total = hits.get((e["file"], e["en"]), 0)
        if total == 0:
            report["missing"].append({"file": e["file"], "en": e["en"]})
        elif total > 1:
            report["errors"].append(
                "%s: 同一字面量命中 %d 次, 请人工确认是否都该翻: %r" % (e["file"], total, e["en"])
            )

    report["hits"] = {"%s :: %s" % k: v for k, v in hits.items()}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)

    print(
        "词表 %d 条, 命中 %d 条 (%d 处), 未命中 %d 条"
        % (len(entries), len(hits), sum(hits.values()), len(report["missing"]))
    )
    for r in report["replaced"]:
        print("  %s:%d %r -> %r" % (r["file"], r["line"], r["en"], r["zh"]))
    for e in report["errors"]:
        print("ERROR", e)
    for e in report["missing"]:
        print("MISS", e["file"], "::", e["en"])
    for s in report["skipped_template"]:
        print("SKIP", s)
    if args.check:
        return 1 if (report["errors"] or report["missing"]) else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
