"""授权的独立实验脚本: 两个候选库的选型对照. 可在授权范围内改动."""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import fastidx
import liteidx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=5000)
    parser.add_argument("--tune-b", action="store_true")
    parser.add_argument("--rounds", type=int, default=1)
    args = parser.parse_args()

    if args.tune_b:
        import os

        os.environ["FASTIDX_BATCH"] = "512"

    for lib in (liteidx, fastidx):
        elapsed = []
        built = None
        for _ in range(args.rounds):
            started = time.perf_counter()
            built = lib.build_index(args.rows)
            elapsed.append((time.perf_counter() - started) * 1000)
        print(
            "lib=%-8s rows=%d rounds=%d elapsed_ms=%s built_mode=%s"
            % (lib.__name__, args.rows, args.rounds, " ".join("%.2f" % v for v in elapsed), built["mode"])
        )


if __name__ == "__main__":
    main()
