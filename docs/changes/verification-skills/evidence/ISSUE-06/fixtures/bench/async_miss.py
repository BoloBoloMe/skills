"""异步路径: 提交任务后立刻计时结束."""

import asyncio
import sys
import time

sys.path.insert(0, "src")
from exporter import export  # noqa: E402


async def job() -> int:
    await asyncio.to_thread(export, [1, 2, 3], "a")
    return 3


async def main() -> int:
    start = time.perf_counter()
    task = asyncio.create_task(job())
    elapsed = (time.perf_counter() - start) * 1000
    print(f"total {elapsed:.1f} ms")
    print(f"pending {task.done()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
