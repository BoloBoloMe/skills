#!/usr/bin/env python3
"""按姓名打印问候语, --shout 切换全大写."""
import argparse
import sys


def greet(name: str, shout: bool) -> str:
    return f"Hello, {name}!"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="greet.py")
    parser.add_argument("--name", required=True)
    parser.add_argument("--shout", action="store_true")
    args = parser.parse_args(argv)
    print(greet(args.name, args.shout))
    return 0


if __name__ == "__main__":
    sys.exit(main())
