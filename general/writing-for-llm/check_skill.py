"""检查 skill frontmatter 中不需要语言判断的硬约束. 仅依赖标准库."""

import argparse
import json
import re
import sys
from pathlib import Path


FIELD = re.compile(r"^(name|description|disable-model-invocation):\s*(.*)$")
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
PLAIN_NON_TEXT = re.compile(
    r"(?:~|null|true|false|yes|no|on|off|\d{4}-\d{2}-\d{2}|"
    r"[+-]?(?:0[xX][\da-fA-F_]+|0[oO][0-7_]+|0[bB][01_]+|"
    r"(?:\d[\d_]*(?:\.\d[\d_]*)?|\.\d[\d_]*)(?:[eE][+-]?\d[\d_]*)?|\.inf|\.nan))\Z",
    re.IGNORECASE,
)


def scalar(raw: str) -> str:
    """读取单行 YAML 标量; 不支持的写法明确报错, 避免漏检."""
    if raw.startswith('"'):
        match = re.fullmatch(r'("(?:[^"\\]|\\.)*")(?:\s+#.*)?', raw)
        if not match:
            raise ValueError("不支持的双引号标量")
        return json.loads(match.group(1))
    if raw.startswith("'"):
        match = re.fullmatch(r"'((?:[^']|'')*)'(?:\s+#.*)?", raw)
        if not match:
            raise ValueError("不支持的单引号标量")
        return match.group(1).replace("''", "'")
    value = re.split(r"\s+#", raw, maxsplit=1)[0].rstrip()
    if PLAIN_NON_TEXT.fullmatch(value) or value.startswith(("|", ">", "{", "[", "*", "&", "!")):
        raise ValueError("不是可确认的单行文本, 请改写或用引号标明字符串")
    return value


def check(path: Path) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [f"无法读取文件: {exc}"]
    if not lines or lines[0] != "---":
        return ["缺少开头的 frontmatter 分隔线"]
    try:
        end = lines.index("---", 1)
    except ValueError:
        return ["缺少结尾的 frontmatter 分隔线"]

    fields: dict[str, str] = {}
    errors: list[str] = []
    for line in lines[1:end]:
        match = FIELD.fullmatch(line)
        if not match:
            continue
        key, raw = match.groups()
        if key in fields:
            errors.append(f"重复字段: {key}")
            continue
        if key == "disable-model-invocation":
            if re.fullmatch(r"true(?:\s+#.*)?", raw.rstrip()):
                fields[key] = "true"
            else:
                errors.append("disable-model-invocation 只能写 true; 模型调用时省略此字段")
            continue
        try:
            fields[key] = scalar(raw)
        except ValueError as exc:
            errors.append(f"{key} 无法检查: {exc}")

    name = fields.get("name", "")
    if not NAME.fullmatch(name):
        errors.append("name 必须是小写 kebab-case")
    if name and name != path.parent.name:
        errors.append(f"name 与目录名不一致: {name} != {path.parent.name}")
    mode = fields.get("disable-model-invocation", "false")
    description = fields.get("description", "")
    if not description or description.startswith(("|", ">")):
        errors.append("description 必须是单行非空文本, 才能可靠检查")
    elif mode == "false" and ":" in description:
        errors.append("模型调用的 description 不能包含冒号")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", type=Path, help="待检查的 SKILL.md 路径")
    args = parser.parse_args()
    errors = check(args.skill)
    for error in errors:
        print(f"{args.skill}: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"{args.skill}: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
