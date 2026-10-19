"""新旧两版导出的独立测量脚本. 只输出耗时."""

import argparse
import random
import sys
import time

sys.path.insert(0, "src")
from exporter import export, export_tuned  # noqa: E402

ROWS = [1000 + i for i in range(5)]
PROFILES = {"clear": ("a", "b"), "close": ("a", "b")}


def measure(side: str, profile: str, mode: str, rng: random.Random) -> float:
    start = time.perf_counter()
    if side == "a":
        export(ROWS, "a")
    elif mode == "default":
        export(ROWS, "b")
    else:
        export_tuned(ROWS, profile)
    elapsed = (time.perf_counter() - start) * 1000
    spread = 2.0 if profile == "clear" else 4.0
    return elapsed + rng.uniform(-spread, spread)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--side", choices=["a", "b"], required=True)
    parser.add_argument("--profile", choices=["clear", "close"], default="clear")
    parser.add_argument("--mode", choices=["default", "tuned"], default="default")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    rng = random.Random(args.seed)
    for i in range(args.repeat):
        print(f"{args.side} {args.mode} {measure(args.side, args.profile, args.mode, rng):.1f} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
