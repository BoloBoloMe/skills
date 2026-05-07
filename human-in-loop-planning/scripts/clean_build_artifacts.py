#!/usr/bin/env python3
"""Remove build artifacts that must never be packaged into a skill."""
import argparse
import shutil
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    args = ap.parse_args()
    root = Path(args.root)
    removed = 0
    for d in root.rglob("__pycache__"):
        shutil.rmtree(d)
        removed += 1
    for f in root.rglob("*.pyc"):
        f.unlink()
        removed += 1
    print(f"cleaned {removed} build artifacts")

if __name__ == "__main__":
    main()
