"""核对计时范围是否盖住工作: 生成器, 异步任务, 批次导出的有效行计数.

每个场景都同时给 "脚本里计时的那段" 与 "把工作真正做完的时间", 便于对比.
"""

import asyncio
import sys
import time

sys.path.insert(0, "src")
from exporter import export, export_legacy  # noqa: E402

ROWS_B = [120, 640, 810, 340, 990, 450, 700, 260]  # export_flow.py 的数据
ROWS_LEGACY = [1, 2, 3, 4, 5, 6, 7, 8]  # legacy_flow.py 的数据


def gen_case() -> None:
    def stream():
        for row in [1, 2, 3, 4]:
            yield export([row], "a")

    start = time.perf_counter()
    pending = stream()
    built = (time.perf_counter() - start) * 1000
    start = time.perf_counter()
    items = list(pending)
    consumed = (time.perf_counter() - start) * 1000
    print(f"gen: built={built:.2f} ms consumed={consumed:.1f} ms items={len(items)}")


async def async_case() -> None:
    async def job() -> int:
        await asyncio.to_thread(export, [1, 2, 3], "a")
        return 3

    start = time.perf_counter()
    task = asyncio.create_task(job())
    created = (time.perf_counter() - start) * 1000
    done_at_creation = task.done()
    start = time.perf_counter()
    result = await task
    awaited = (time.perf_counter() - start) * 1000
    print(
        f"async: create={created:.2f} ms done_when_created={done_at_creation} "
        f"await={awaited:.1f} ms result={result}"
    )


def flow_case() -> None:
    start = time.perf_counter()
    out = export(ROWS_B, "b")
    b_ms = (time.perf_counter() - start) * 1000
    ok = sum(1 for r in out if r["ok"])
    err = len(out) - ok
    start = time.perf_counter()
    written = export_legacy(ROWS_LEGACY)
    legacy_ms = (time.perf_counter() - start) * 1000
    print(
        f"flow: b rows={len(ROWS_B)} total={b_ms:.1f} ms returned={len(out)} ok={ok} "
        f"err={err} per_ok={b_ms / ok:.1f} ms"
    )
    print(
        f"flow: legacy rows={len(ROWS_LEGACY)} total={legacy_ms:.1f} ms written={written} "
        f"per_written={legacy_ms / written:.1f} ms"
    )
    same_written = export_legacy(ROWS_B)
    print(f"flow: legacy 跑 b 那批行 written={same_written} (8 行全成功, 数据集不同)")


if __name__ == "__main__":
    gen_case()
    asyncio.run(async_case())
    flow_case()
