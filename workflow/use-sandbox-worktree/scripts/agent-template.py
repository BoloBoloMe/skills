#!/usr/bin/env -S uv run python
"""确定的模板入口: list/show/validate/render/install/check. 不调用镜像构建."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agent_config import template as templates
from agent_config.common import TemplateError, pretty


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    for action in ("show", "validate", "render"):
        command = sub.add_parser(action)
        command.add_argument("template")
        if action == "render":
            command.add_argument("--output", type=Path, required=True)
    for action in ("install", "check"):
        command = sub.add_parser(action)
        command.add_argument("--runtime-file", type=Path, required=True)
        command.add_argument("--name", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            print(pretty(templates.choices()), end="")
        elif args.command in ("show", "validate", "render"):
            bundle = templates.load(args.template)
            if args.command == "show":
                shown = {**bundle, "catalog": {**bundle["catalog"], "codex_catalog": {
                    "version": bundle["catalog"]["codex_catalog"]["version"],
                    "models": [{k: v for k, v in model.items() if k != "base_instructions"}
                               for model in bundle["catalog"]["codex_catalog"]["models"]]}}}
                print(pretty({**templates.summary(bundle), **shown}), end="")
            elif args.command == "render":
                value = templates.freeze(args.output, bundle)
                print(pretty({**templates.summary(bundle), "snapshot": str(args.output),
                              "snapshot-digest": value["snapshot-digest"]}), end="")
            else:
                print(pretty({**templates.summary(bundle), "valid": True}), end="")
        else:
            path = args.runtime_file.expanduser().resolve()
            if path.parent.name != "runtime" or path.suffix != ".json":
                raise TemplateError("须指定 records-root/runtime 下的创建记录")
            runtime = templates.read_json(path)
            from swt import acquire_lock, SwtError
            try:
                lock = acquire_lock(Path(runtime["repo"]), path.parent.parent)
            except SwtError as exc:
                raise TemplateError(exc.message) from None
            try:
                # 与 birth/resume/terminate 共用仓级锁. 锁内重读, 不用旧快照操作.
                runtime = templates.read_json(path)
                report = templates.operate(runtime, args.name, install=args.command == "install")
            finally:
                lock.close()
            print(json.dumps(report, separators=(",", ":")))
        return 0
    except TemplateError as exc:
        print("FAIL " + str(exc), file=sys.stderr)
        return 2
    except (KeyError, TypeError, ValueError, OSError):
        print("FAIL 模板/创建记录格式或权限错误, 原始内容不输出", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
