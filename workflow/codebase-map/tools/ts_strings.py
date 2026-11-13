#!/usr/bin/env python3
"""统计 .ts 里面向用户的字符串 (可能的文案), 供汉化词表评估.

用法: python3 ts_strings.py [--out file.json]
扫描范围: ROOT 下所有 .ts, 默认排除 *.spec.ts / *.e2e.ts (测试断言不是界面文案).
分类方法: 取字面量前面最近的 `名字:` 属性名作为上下文, 按属性名分桶;
对字面量做黑名单过滤 (路径/CSS 类/图标/单位/URL/单 token 标识符等).
"""

import json
import os
import re
import sys
from collections import Counter

ROOT = os.environ.get("CC_ROOT", "/tmp/cc-build/src/visualization/app")
OUT = os.environ.get("CC_TS_REPORT", "/tmp/cc-build/ts-report.json")

# 这些属性名在 CodeCharta 里几乎总是界面文案
TEXT_PROPS = {
    "title",
    "label",
    "message",
    "text",
    "description",
    "hint",
    "tooltip",
    "placeholder",
    "header",
    "heading",
    "help",
    "tooltipText",
    "buttonText",
    "emptyText",
    "confirmText",
    "caption",
    "subtitle",
    "summary",
    "errorMessage",
    "successMessage",
    "ariaLabel",
    "name",
}

BLACKLIST_RE = [
    re.compile(r"^[.#\[\]>~+*]"),  # CSS 选择器
    re.compile(r"^[a-z0-9-]+$"),  # kebab / 小写单词 / id
    re.compile(r"^[a-z]+[A-Z]"),  # camelCase 标识符
    re.compile(r"^[A-Z][A-Za-z0-9]*$"),  # 单个 PascalCase 词
    re.compile(r"^(fa[srbl]?|fas|far|fab) "),  # 字体图标
    re.compile(r"^(https?|data|file):"),
    re.compile(r"^[\w.@/-]+\.(ts|js|json|html|scss|css|svg|png|cc)$"),
    re.compile(r"^(px|em|rem|%|deg|s|ms)$"),
    re.compile(r"^[0-9]"),
    re.compile(r"^-?\d+(\.\d+)?(px|em|rem|%|deg)?$"),
    re.compile(r"^(rgb|rgba|hsl|var|calc)\("),
    re.compile(r"^#[0-9a-fA-F]{3,8}$"),
    re.compile(r"^\{\{"),
    re.compile(r"^[a-z]+\.[a-z]"),  # 属性路径 / 文件名
    re.compile(r"^[A-Za-z-]+/[A-Za-z-]+"),  # 路径
    re.compile(r"^\.[a-z]"),  # 扩展名
    re.compile(r"^(true|false|null|undefined|inherit|auto|none|initial|flex|block|grid)$"),
]

STR_LIT_RE = re.compile(r'"(?:[^"\\\n]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\'|`(?:[^`\\]|\\.)*`')
PROP_CTX_RE = re.compile(r"([A-Za-z_$][\w$]*)\s*:\s*$")


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


TAILWIND_RE = re.compile(r"^[a-z0-9\-:/\[\].!%&*+= ]+$")


def looks_user_facing(text):
    if len(text) < 3 or "{{" in text:
        return False
    if TAILWIND_RE.match(text) and " " in text:
        return False  # 纯 Tailwind/CSS class 列表 (全小写, 空格分隔)
    if " " not in text and len(text) < 12:
        return False
    for rx in BLACKLIST_RE:
        if rx.match(text):
            return False
    return bool(re.search(r"[A-Za-z]{2,}", text))


def scan(path):
    raw = open(path, encoding="utf-8").read()
    src = strip_comments(raw)
    found = []
    for m in STR_LIT_RE.finditer(src):
        lit = m.group(0)
        quote = lit[0]
        body = lit[1:-1]
        if quote == "`":
            body = re.sub(r"\$\{[^}]*\}", "{}", body)
        if not looks_user_facing(body):
            continue
        before = src[max(0, m.start() - 60) : m.start()]
        pm = PROP_CTX_RE.search(before)
        prop = pm.group(1) if pm else None
        in_throw = bool(re.search(r"(throw new \w*Error|\bnew Error|console\.\w+)\([^()]*$", before))
        found.append(
            {
                "file": os.path.relpath(path, ROOT),
                "line": raw.count("\n", 0, m.start()) + 1,
                "prop": prop,
                "text": body,
                "in_throw": in_throw,
            }
        )
    return found


def main():
    files = []
    for dirpath, _, names in os.walk(ROOT):
        if "node_modules" in dirpath.split(os.sep):
            continue
        for fn in names:
            if fn.endswith(".ts") and not fn.endswith((".spec.ts", ".e2e.ts", ".po.ts", ".mock.ts")):
                if "mocks" in dirpath.split(os.sep) or "testdata" in dirpath.split(os.sep):
                    continue
                files.append(os.path.join(dirpath, fn))
    all_found = []
    for f in sorted(files):
        all_found.extend(scan(f))

    # 去掉枚举/对象重复: 用 (prop, text) 去重统计
    uniq = {}
    for it in all_found:
        uniq.setdefault((it["prop"], it["text"]), 0)
        uniq[(it["prop"], it["text"])] += 1

    by_prop = Counter()
    for (prop, _), n in uniq.items():
        by_prop[prop or "(无属性名上下文)"] += 1
    text_props = {k: v for k, v in by_prop.items() if k in TEXT_PROPS}
    report = {
        "ts_files_scanned": len(files),
        "literals_total": len(all_found),
        "literals_unique": len(uniq),
        "in_throw_or_log": sum(1 for it in all_found if it["in_throw"]),
        "by_prop": dict(by_prop.most_common()),
        "text_props_total": sum(text_props.values()),
        "samples": sorted(
            ({**{"count": n}, "prop": p, "text": t} for (p, t), n in uniq.items() if p in TEXT_PROPS),
            key=lambda x: -x["count"],
        )[:200],
        "samples_by_file": {},
    }
    per_file = Counter(it["file"] for it in all_found)
    report["files_by_count"] = per_file.most_common(20)
    # 分目录桶 (只统计去重后的种数), 用于判断哪些是生产界面代码
    buckets = Counter()
    for (prop, text), n in uniq.items():
        pass
    for it in all_found:
        buckets[it["file"].split("/features/")[-1].split("/")[0] if "/features/" in it["file"] else it["file"].split("/")[0]] += 1
    report["buckets"] = buckets.most_common()
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)

    print("扫描 .ts %d 个, 疑似用户文案字面量 %d 处 / %d 种" % (len(files), len(all_found), len(uniq)))
    print("其中文案类属性(title/label/message/...) %d 种" % report["text_props_total"])
    print("throw/console 里的 %d 处 (开发向, 一般不用翻)" % report["in_throw_or_log"])
    print("属性名分布 (前 12):", list(by_prop.most_common(12)))
    print("报告:", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
