"""授权的独立实验脚本: 单次粗估. 不属于产品源码, 可在授权范围内改动."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from report_job import run_report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=2000)
    parser.add_argument("--mode", choices=["fast", "old"], default="fast")
    parser.add_argument("--rounds", type=int, default=1)
    parser.add_argument("--defect", choices=["none", "http500", "wrong_output"], default="none")
    parser.add_argument("--no-error-count", action="store_true")
    args = parser.parse_args()

    elapsed = []
    last = None
    for _ in range(args.rounds):
        last = run_report(rows=args.rows, fast=args.mode == "fast", defect=args.defect)
        elapsed.append(last["elapsed_ms"])

    print("mode=%s rows=%d rounds=%d defect=%s" % (args.mode, args.rows, args.rounds, args.defect))
    print("elapsed_ms=%s" % " ".join("%.2f" % value for value in elapsed))
    if not args.no_error_count:
        print("failed=%d status=%s" % (last["failed"], last["status"]))
    print("written=%d written_ok=%s checksum_ok=%s" % (last["written"], last["written_ok"], last["checksum_ok"]))


if __name__ == "__main__":
    main()
