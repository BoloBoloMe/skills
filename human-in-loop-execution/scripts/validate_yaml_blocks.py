#!/usr/bin/env python3
"""Validate Markdown fenced YAML blocks, duplicate keys, fence balance, and common routing shapes."""
import argparse
import re
import sys
from pathlib import Path
try:
    import yaml
except Exception as exc:
    print(f"PyYAML is required: {exc}", file=sys.stderr)
    sys.exit(2)

YAML_FENCE_RE = re.compile(r"```(?:yaml|yml)\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)
FENCE_LINE_RE = re.compile(r"^\s*```")

class UniqueKeyLoader(yaml.SafeLoader):
    pass

def construct_mapping_no_duplicates(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            mark = key_node.start_mark
            raise yaml.YAMLError(f"duplicate key {key!r} at line {mark.line + 1}, column {mark.column + 1}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping

UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping_no_duplicates)

def markdown_files(root: Path):
    if root.is_file():
        if root.suffix.lower() == ".md":
            yield root
        return
    for path in root.rglob("*.md"):
        yield path

def clean_path_string(x):
    return isinstance(x, str) and "\n" not in x and " - " not in x and x.strip() == x and bool(x)

def list_of_strings(value):
    return isinstance(value, list) and all(clean_path_string(x) for x in value)

def check_fence_balance(text, md, errors):
    stack = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if FENCE_LINE_RE.match(line):
            if not stack:
                stack.append((lineno, line.strip()))
            else:
                stack.pop()
    if stack:
        lineno, fence = stack[-1]
        errors.append(f"{md}: unbalanced markdown fence opened at line {lineno}: {fence}")

def check_directory_shape(data, md, idx, errors):
    if not isinstance(data, dict):
        return
    if "always_read_minimal" in data and not list_of_strings(data["always_read_minimal"]):
        errors.append(f"{md}: yaml block {idx}: always_read_minimal must be list[str]")
    if "read_next_by_intent" in data:
        r = data["read_next_by_intent"]
        if not isinstance(r, dict):
            errors.append(f"{md}: yaml block {idx}: read_next_by_intent must be mapping")
        else:
            for key, value in r.items():
                if not list_of_strings(value):
                    errors.append(f"{md}: yaml block {idx}: read_next_by_intent.{key} must be list[str]")
    if "examples" in data and isinstance(data["examples"], dict):
        for key, value in data["examples"].items():
            if not list_of_strings(value):
                errors.append(f"{md}: yaml block {idx}: examples.{key} must be list[str]")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="Markdown file or directory to scan")
    ap.add_argument("--shape", action="store_true", help="Validate common routing YAML shapes in addition to parseability")
    args = ap.parse_args()
    root = Path(args.path)
    errors = []
    count = 0
    for md in markdown_files(root):
        text = md.read_text(encoding="utf-8")
        check_fence_balance(text, md, errors)
        for idx, block in enumerate(YAML_FENCE_RE.findall(text), start=1):
            count += 1
            try:
                data = yaml.load(block, Loader=UniqueKeyLoader) if block.strip() else None
            except Exception as exc:
                errors.append(f"{md}: yaml block {idx}: {exc}")
                continue
            if args.shape:
                check_directory_shape(data, md, idx, errors)
    if errors:
        print("MARKDOWN_YAML_ERRORS")
        print("\n".join(errors))
        sys.exit(1)
    print(f"markdown fences and yaml blocks ok: {count}")

if __name__ == "__main__":
    main()
