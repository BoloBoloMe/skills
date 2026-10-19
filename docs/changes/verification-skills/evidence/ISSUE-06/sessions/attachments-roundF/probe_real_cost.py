"""把 lazy_gen / async_miss / outside_timer 三条路径的真实工作包进计时区.

不是新增正式用例, 只是把原来漏掉的等待/迭代补回计时范围, 用于核查
"新版导出在这三条路径上几乎不花时间" 这个说法.
"""

import argparse
import asyncio
import sys
import time

sys.path.insert(0, "src")
from exporter import export  # noqa: E402


def timed(fn):
    start = time.perf_counter()
    result = fn()
    return (time.perf_counter() - start) * 1000, result


async def _job():
    return await asyncio.to_thread(export, [1, 2, 3], "a")


def lazy() -> float:
    def consume():
        return [item for row in [1, 2, 3, 4] for item in export([row], "a")]

    elapsed, out = timed(consume)
    print(f"lazy consumed {len(out)} items")
    return elapsed


def async_() -> float:
    async def main():
        start = time.perf_counter()
        task = asyncio.create_task(_job())
        result = await task
        return (time.perf_counter() - start) * 1000, result

    elapsed, out = asyncio.run(main())
    print(f"async awaited {len(out)} items")
    return elapsed


def outside() -> float:
    elapsed, out = timed(lambda: export([11, 22, 33, 44], "a"))
    print(f"outside exported {len(out)} items")
    return elapsed


PATHS = {"lazy": lazy, "async": async_, "outside": outside}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", choices=sorted(PATHS), required=True)
    args = parser.parse_args()
    print(f"total {PATHS[args.path]():.1f} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
