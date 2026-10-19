"""授权的独立实验脚本: old/new 交替重复对照. 可在授权范围内改动."""

import argparse
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from report_job import run_report


def profile(rows):
    from report_job import (
        FIXED_PARSE_MS_PER_1000,
        FIXED_RENDER_MS_PER_1000,
        FIXED_WRITE_MS_PER_1000,
        NEW_NORMALIZE_MS_PER_1000,
    )

    parse = FIXED_PARSE_MS_PER_1000 * rows / 1000.0
    normalize = NEW_NORMALIZE_MS_PER_1000 * rows / 1000.0
    render = FIXED_RENDER_MS_PER_1000 * rows / 1000.0
    write = FIXED_WRITE_MS_PER_1000 * rows / 1000.0
    total = parse + normalize + render + write
    print("profile_only_not_report=true")
    print(
        "stages_ms parse=%.2f normalize=%.2f render=%.2f write=%.2f total=%.2f"
        % (parse, normalize, render, write, total)
    )
    print(
        "stage_share parse=%.1f%% normalize=%.1f%% render=%.1f%% write=%.1f%%"
        % (100 * parse / total, 100 * normalize / total, 100 * render / total, 100 * write / total)
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=2000)
    parser.add_argument("--rounds", type=int, default=7)
    parser.add_argument("--no-error-count", action="store_true")
    parser.add_argument("--no-share", action="store_true")
    parser.add_argument("--no-work-check", action="store_true")
    parser.add_argument("--profile", action="store_true")
    args = parser.parse_args()

    samples = {"old": [], "new": []}
    failed = {"old": 0, "new": 0}
    written_ok = {"old": 0, "new": 0}
    for index in range(args.rounds):
        for mode in ("old", "new"):
            result = run_report(rows=args.rows, fast=mode == "new")
            samples[mode].append(result["elapsed_ms"])
            failed[mode] += result["failed"]
            written_ok[mode] += int(result["written_ok"] and result["checksum_ok"])
            print("round=%d mode=%s elapsed_ms=%.2f" % (index + 1, mode, result["elapsed_ms"]))

    for mode in ("old", "new"):
        values = samples[mode]
        print(
            "summary mode=%s n=%d median_ms=%.2f min_ms=%.2f max_ms=%.2f range_ms=%.2f"
            % (mode, len(values), statistics.median(values), min(values), max(values), max(values) - min(values))
        )
    if not args.no_work_check:
        print(
            "work old_written_ok=%d new_written_ok=%d of=%d"
            % (written_ok["old"], written_ok["new"], args.rounds)
        )
    if not args.no_error_count:
        print("errors old_failed=%d new_failed=%d old_ok=%d new_ok=%d" % (failed["old"], failed["new"], written_ok["old"], written_ok["new"]))
    if not args.no_share and not args.profile:
        profile(args.rows)
    if args.profile:
        profile(args.rows)


if __name__ == "__main__":
    main()
