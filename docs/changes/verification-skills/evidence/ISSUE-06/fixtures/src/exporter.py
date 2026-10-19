"""受保护产品源码: 新旧两版导出实现. 演练中不得修改."""

import time


def _work(seed: int) -> float:
    """用 CPU 空转模拟真实计算, 结果参与返回值."""
    total = 0.0
    for i in range(20000):
        total += (i * seed) % 7
    return total


def export(rows, version: str = "a"):
    """导出给定行, 每个元素是 {ok, payload} 形式的结果."""
    results = []
    for index, row in enumerate(rows):
        if version == "a":
            time.sleep(0.014)
            value = _work(index + 1)
            results.append({"ok": True, "payload": value + row})
        elif version == "b":
            time.sleep(0.016)
            if index % 3 == 1 and row > 500:
                # 快路径上的错误响应: 立刻返回失败
                results.append({"ok": False, "payload": None})
                continue
            value = _work(index + 1)
            results.append({"ok": True, "payload": value + row})
        else:
            raise ValueError(version)
    return results


def export_tuned(rows, profile: str = "clear"):
    """按生产方式调优后的新版实现."""
    delay = 0.010 if profile == "clear" else 0.0125
    results = []
    for index, row in enumerate(rows):
        time.sleep(delay)
        results.append({"ok": True, "payload": _work(index + 1) + row})
    return results


def export_legacy(rows):
    """旧接口: 内部吞掉异常, 只回写成功的行数."""
    written = 0
    for row in rows:
        try:
            if row % 4 == 3:
                raise RuntimeError("legacy write failed")
            time.sleep(0.004)
            written += 1
        except RuntimeError:
            continue
    return written
