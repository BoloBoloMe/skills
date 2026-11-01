#!/usr/bin/env python3
"""CodeCharta visualization 模板汉化替换脚本 (构建期使用, 不改上游仓库历史).

用法:
  python3 localize.py --report     # 只扫描统计, 不写文件, 输出 stat-report.json
  python3 localize.py --apply      # 按词表替换 .html (幂等)
  python3 localize.py --check      # 校验词表: 空翻译/双引号/未用词条, 有问题 exit 1

纪律:
  * 只处理 .html 的文本段与白名单属性值;
  * Angular 控制流块头 (@if/@for/@else/@empty/...) 视为语法, 原样保留, 只翻其中的文案;
  * {{ }} 插值整段作为不可变占位符 {{0}} {{1}} ..., 译文可以重排占位符位置;
  * 跳过 Angular 绑定属性 ([x]/[attr.x]/(x)/*x/#ref), 跳过 <script>/<style>/注释;
  * 幂等: 目标已含 CJK 视为已翻;
  * 属性值里禁止出现包裹用的双引号, 出现即报错不改写.
"""

import argparse
import json
import os
import re
import sys
from collections import Counter

ROOT = os.environ.get("CC_ROOT", "/tmp/cc-build/src/visualization/app")
DICT = os.environ.get("CC_DICT", "/tmp/cc-build/i18n/zh.txt")
OUT = os.environ.get("CC_REPORT", "/tmp/cc-build/stat-report.json")

# 视为"用户可见"的字面量属性 (小写比较). 组件 input 用普通属性传值, 也算可见文案.
TEXT_ATTRS = {
    "title",
    "placeholder",
    "aria-label",
    "aria-placeholder",
    "aria-description",
    "arialabel",
    "alt",
    "label",
    "data-tip",
    "data-tooltip",
    "tooltip",
    "emptylabel",
    "emptymessage",
    "buttonlabel",
}
BINDING_PREFIX = ("[", "(", "*", "#", "bind-", "on-", "let-")
SKIP_ELEMENTS = {"script", "style"}
VOID_ELEMENTS = {"br", "hr", "img", "input", "meta", "link", "path", "circle", "source", "use"}

CJK_RE = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]")
WORD_RE = re.compile(r"[A-Za-z]{2,}")
PH_RE = re.compile(r"\{\{.*?\}\}", re.S)
WS_RE = re.compile(r"\s+")
ATTR_RE = re.compile(r"([^\s=<>\"'/]+)\s*=\s*(\"([^\"]*)\"|'([^']*)')")

CTRL_KEYWORDS = (
    "if",
    "else",
    "for",
    "empty",
    "switch",
    "case",
    "default",
    "defer",
    "placeholder",
    "loading",
    "error",
    "let",
)


def split_prose(text):
    """把文本节点切成 (语法, 文案) 交替片段, 返回文案片段的 (start, end) 列表.

    Angular 17+ 控制流块头 (@if (...) {, @for (...; track ...) {, @else {, @empty { ...)
    和 @let 声明被当作语法跳过; 其余位置算作文案.
    """
    ranges = []
    i, n = 0, len(text)
    seg_start = 0
    while i < n:
        if text[i] != "@":
            i += 1
            continue
        j = i + 1
        while j < n and text[j].isalpha() and text[j].islower():
            j += 1
        if text[i + 1 : j] not in CTRL_KEYWORDS:
            i += 1
            continue
        if i > seg_start:
            ranges.append((seg_start, i))
        depth = 0
        while j < n:
            c = text[j]
            if c in "([":
                depth += 1
            elif c in ")]":
                depth -= 1
            elif depth <= 0 and c == "{":
                j += 1
                break
            elif depth <= 0 and c in ";\n":
                break
            j += 1
        i = seg_start = j
    if n > seg_start:
        ranges.append((seg_start, n))
    return ranges


def norm_key(text):
    """把一段文案变成词表 key: 插值换成 {{n}}, 空白折叠."""
    phs = []

    def repl(m):
        phs.append(m.group(0))
        return "{{%d}}" % (len(phs) - 1)

    body = PH_RE.sub(repl, text)
    return WS_RE.sub(" ", body).strip(), phs


def has_prose(text):
    """是否像用户可见英文文案 (排除纯插值/纯符号/纯数字)."""
    stripped = PH_RE.sub(" ", text)
    if not re.sub(r"[\s{};:,.]", "", stripped):
        return False
    return bool(WORD_RE.search(stripped))


def load_dict(path):
    entries, dups = {}, []
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if "\t" not in line:
                raise SystemExit("词表第 %d 行缺少 TAB 分隔: %r" % (lineno, line))
            en, zh = line.split("\t", 1)
            if en in entries:
                dups.append(en)
            entries[en] = (zh, lineno)
    return entries, dups


def find_tag_end(text, i):
    """返回 < 起始标签的结束位置(含 >), 处理引号内的 > ."""
    n = len(text)
    j = i + 1
    quote = None
    while j < n:
        ch = text[j]
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == ">":
            return j + 1
        elif ch == "<":
            return j
        j += 1
    return n


def iter_tokens(text):
    i, n = 0, len(text)
    while i < n:
        lt = text.find("<", i)
        if lt < 0:
            yield ("text", i, n, text[i:n])
            return
        if lt > i:
            yield ("text", i, lt, text[i:lt])
        if text.startswith("<!--", lt):
            end = text.find("-->", lt)
            end = n if end < 0 else end + 3
            yield ("raw", lt, end, text[lt:end])
            i = end
            continue
        end = find_tag_end(text, lt)
        body = text[lt:end]
        m = re.match(r"</?\s*([A-Za-z][\w:-]*)", body)
        name = m.group(1).lower() if m else ""
        yield ("tag", lt, end, body, name)
        i = end


def scan_file(path):
    """返回 [(kind, value, start, end, attr, quote, line)] 形式的候选列表."""
    text = open(path, encoding="utf-8").read()
    items = []
    stack = []
    for tok in iter_tokens(text):
        kind = tok[0]
        if kind == "tag":
            _, start, end, body, name = tok
            closing = body.startswith("</")
            selfclose = body.rstrip(">").rstrip().endswith("/")
            if closing:
                if stack:
                    stack.pop()
                continue
            if not selfclose and name not in VOID_ELEMENTS:
                stack.append(name)
            if not name:
                continue
            for m in ATTR_RE.finditer(body):
                aname = m.group(1)
                if aname.lower().startswith(BINDING_PREFIX):
                    continue
                if aname.lower() not in TEXT_ATTRS:
                    continue
                quote = '"' if m.group(3) is not None else "'"
                value = m.group(3) if m.group(3) is not None else m.group(4)
                if PH_RE.search(value) or not has_prose(value):
                    continue
                a_start = start + m.start(2) + 1
                items.append(
                    ("attr", value, a_start, a_start + len(value), aname, quote, text.count("\n", 0, start) + 1)
                )
        elif kind == "text":
            _, start, end, value = tok
            if any(s in SKIP_ELEMENTS for s in stack):
                continue
            for s0, s1 in split_prose(value):
                seg = value[s0:s1]
                if not seg.strip() or not has_prose(seg):
                    continue
                items.append(
                    ("text", seg, start + s0, start + s1, None, None, text.count("\n", 0, start + s0) + 1)
                )
    return text, items


def html_files(root):
    for dirpath, _, filenames in os.walk(root):
        if "node_modules" in dirpath.split(os.sep):
            continue
        for fn in sorted(filenames):
            if fn.endswith(".html"):
                yield os.path.join(dirpath, fn)


def render(zh, phs):
    out = zh
    for idx, ph in enumerate(phs):
        out = out.replace("{{%d}}" % idx, ph)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--restore", action="store_true")
    args = ap.parse_args()

    if args.restore:
        import subprocess

        subprocess.run(["git", "-C", ROOT, "checkout", "--", "."], check=True)
        print("已用 git checkout 恢复模板到上游原样")
        return 0

    entries, dups = load_dict(DICT)
    stats = {
        "files_total": 0,
        "files_with_text": 0,
        "brand_new": 0,
        "segments": Counter(),
        "with_interpolation": 0,
        "per_file": {},
        "untranslated": Counter(),
        "errors": [],
        "keys_used": set(),
        "applied": 0,
    }

    for path in html_files(ROOT):
        stats["files_total"] += 1
        text, items = scan_file(path)
        if not items:
            continue
        stats["files_with_text"] += 1
        hits = 0
        edits = []
        for kind, value, start, end, aname, quote, line in items:
            stats["segments"]["text" if kind == "text" else "attr:" + aname] += 1
            key, phs = norm_key(value)
            if phs:
                stats["with_interpolation"] += 1
            zh = entries.get(key, (None, 0))[0]
            if zh is not None:
                if not zh.strip():
                    stats["errors"].append("%s:%d 空翻译 key=%r" % (path, line, key))
                    continue
                new_body = render(zh, phs)
                if kind == "attr" and quote == '"' and '"' in new_body:
                    stats["errors"].append("%s:%d 译文含双引号, 但属性值用双引号包裹 key=%r" % (path, line, key))
                    continue
                if kind == "attr" and quote == "'" and "'" in new_body:
                    stats["errors"].append("%s:%d 译文含单引号, 但属性值用单引号包裹 key=%r" % (path, line, key))
                    continue
                if not CJK_RE.search(new_body):
                    stats["errors"].append("%s:%d 译文不含中文 key=%r" % (path, line, key))
                    continue
                # 占位符必须齐全: 漏一个就等于把界面数据吞掉
                bad_ph = [p for p in range(len(phs)) if zh.count("{{%d}}" % p) != 1]
                if bad_ph:
                    stats["errors"].append(
                        "%s:%d 占位符不全或重复 %s key=%r" % (path, line, ["{{%d}}" % i for i in bad_ph], key)
                    )
                    continue
                # 中文里禁止裸 < > & (会破坏模板/属性), 实体要写成 &amp; 之类
                if re.search(r"<|>|&(?!#?\w+;)", zh):
                    stats["errors"].append("%s:%d 译文含裸 < > & , 请用实体 key=%r" % (path, line, key))
                    continue
                if kind == "text":
                    lead = re.match(r"^\s*", value).group(0)
                    trail = re.search(r"\s*$", value).group(0)
                    new = lead + new_body + trail
                else:
                    new = new_body
                edits.append((start, end, new))
                stats["keys_used"].add(key)
                hits += 1
            else:
                stats["untranslated"][key] += 1
        rel = os.path.relpath(path, ROOT)
        stats["per_file"][rel] = {"segments": len(items), "translated": hits}
        if args.apply and edits:
            out = text
            for start, end, new in sorted(edits, key=lambda e: -e[0]):
                out = out[:start] + new + out[end:]
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(out)
            stats["applied"] += len(edits)
            print("localized %s (segments %d, replaced %d)" % (rel, len(items), len(edits)))

    unused = [k for k in entries if k not in stats["keys_used"]]
    report = {
        "files_total": stats["files_total"],
        "files_with_text": stats["files_with_text"],
        "segments": dict(stats["segments"]),
        "segments_total": sum(stats["segments"].values()),
        "with_interpolation": stats["with_interpolation"],
        "applied": stats["applied"],
        "dict_size": len(entries),
        "dict_unused": unused,
        "dict_duplicates": dups,
        "keys_used": sorted(stats["keys_used"]),
        "untranslated": stats["untranslated"].most_common(),
        "untranslated_unique": len(stats["untranslated"]),
        "untranslated_total": sum(stats["untranslated"].values()),
        "per_file": stats["per_file"],
        "errors": stats["errors"],
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)

    print(
        "templates %d/%d 含候选文案; 候选片段 %d (text %d, attr %d); 含插值 %d; 本次替换 %d"
        % (
            stats["files_with_text"],
            stats["files_total"],
            report["segments_total"],
            stats["segments"]["text"],
            report["segments_total"] - stats["segments"]["text"],
            stats["with_interpolation"],
            stats["applied"] if args.apply else len(stats["keys_used"]),
        )
    )
    print("词典 %d 条, 未用 %d, 重复 %d" % (len(entries), len(unused), len(dups)))
    print(
        "未命中 %d 种 / %d 次, 报告 %s"
        % (report["untranslated_unique"], report["untranslated_total"], OUT)
    )
    for err in stats["errors"]:
        print("ERROR", err)
    if args.check:
        if unused:
            print("未使用词条 %d 条 (在未汉化的原始模板上跑才准: 上游改了文案则需清理)" % len(unused))
            for k in unused[:20]:
                print("  -", k)
        if stats["errors"]:
            return 1
        return 1 if dups else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
