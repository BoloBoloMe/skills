"""候选库 A: 单遍扫描索引. 两份候选库都属待选型材料, 演练期间不改."""

import time

MS_PER_1000 = 22.0


def build_index(rows):
    time.sleep(MS_PER_1000 * rows / 1_000_000.0)
    return {"mode": "single-pass", "rows": rows}
