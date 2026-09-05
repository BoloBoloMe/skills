#!/usr/bin/env python3
"""llm-select/score.py — 选型表渲染, 算分唯一真相源 (仅标准库, 平台无关).

平台无关: 不读任何 agent 平台的配置 (pi 的 settings.json/auth.json/models-store.json 等).
只依赖两份自有数据 (每台设备一份, 默认在 ~/.agents/llm-select/, 可用 --scores/--catalog 覆盖):
  评分表      llm-scores.json    baseline + 各模型七维比率分 (bootstrap.md 建立)
  模型目录    model-catalog.json 每个候选模型的 cost/reasoning/thinking 支持档
候选范围 (scope) 由调用方决定: 缺省 = 评分表 models 的键; --scope 指定完整候选集 (glob, 空格/逗号分隔),
  替换缺省范围; 候选内评分表外的模型标 [未评分]. 用于把本平台可用列表 (如 pi 的 enabledModels) 直接作候选.

失败时向 stderr 输出原因并退出 1: no-table / no-catalog / bad-scope / bad-baseline / bad-json.
"""

import argparse
import json
import re
import sys
from pathlib import Path

DIMS = ["coding", "knowledge", "longctx", "multimodal", "stability", "price", "speed"]
DIM_CN = {
    "coding": "编码", "knowledge": "知识", "longctx": "长上下文",
    "multimodal": "多模态", "stability": "稳定性", "price": "价格", "speed": "速度",
}

# 权重顺序 = DIMS; 0 = 不参与 (该维 N/A 时重归一化).
PROFILES = {
    "coding": [0.40, 0.10, 0.20, 0.0, 0.10, 0.10, 0.10],
    "research": [0.05, 0.35, 0.25, 0.0, 0.10, 0.10, 0.15],
    "review": [0.30, 0.20, 0.20, 0.0, 0.10, 0.05, 0.15],
    "vision": [0.10, 0.15, 0.10, 0.40, 0.10, 0.05, 0.10],  # multimodal 为门槛
    "long-doc": [0.10, 0.15, 0.45, 0.0, 0.10, 0.10, 0.10],
    "cheap-batch": [0.10, 0.05, 0.05, 0.0, 0.10, 0.35, 0.35],
    "general": [1 / 7] * 7,
}
REQUIRED = {"vision": "multimodal"}  # 画像 → 必需维度 (N/A 则该画像无总分)

DEFAULT_DATA_DIR = Path.home() / ".agents" / "llm-select"
PRICE_CAP = 100.0  # 免费模型 (单位成本=0) 相对基准的价格封顶分


def read_json(p: Path):
    """读取并校验 JSON. 文件不存在 → None; 解析失败 → fail (带路径)."""
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e:
        fail("bad-json", f"{p} ({e})")


def load_catalog(path: Path) -> dict:
    catalog = read_json(path)
    if catalog is None:
        fail("no-catalog", str(path))
    models = catalog.get("models")
    if not isinstance(models, dict):
        fail("bad-json", f"{path} (models 缺失或非对象)")
    return models


def load_table(path: Path) -> tuple[str, dict]:
    table = read_json(path)
    if table is None:
        fail("no-table", str(path))
    if not isinstance(table, dict):
        fail("bad-json", f"{path} (内容非对象)")
    baseline = table.get("baseline")
    if not baseline:
        fail("bad-baseline", "(baseline 为空)")
    entries = table.get("models") or {}
    if not isinstance(entries, dict):
        fail("bad-json", f"{path} (models 缺失或非对象)")
    # 校验数值评分: 数值或 null; 非数值直接按 bad-json 报告 (带条目名).
    for full, entry in entries.items():
        if not isinstance(entry, dict):
            continue
        for d in DIMS:
            v = entry.get(d)
            if v is not None and not isinstance(v, (int, float)):
                fail("bad-json", f"{path} 条目 {full} 维 {d} 非数值: {v!r}")
    return baseline, entries


def glob_match(pattern: str, value: str) -> bool:
    """最小 glob, 供 --scope 模式匹配: * → 除 / 外任意串, ? → 单个非 / 字符.
    * 不跨 /, 避免 provider/* 误命中 provider/a/b 的深层路径."""
    rx = re.escape(pattern).replace(r"\*", "[^/]*").replace(r"\?", "[^/]")
    return re.fullmatch(rx, value) is not None


def resolve_scope(args, entries: dict) -> list:
    """候选范围: 缺省 = 评分表 models 键; --scope 指定完整候选集 (替换缺省), glob 展开,
    字面名即使不在评分表也保留 (评分表外候选标未评分)."""
    if not args.scope:
        return list(entries.keys())
    out = []
    for pattern in re.split(r"[\s,]+", args.scope.strip()):
        if not pattern:
            continue
        out.append(pattern)
    # 把 glob 展开成评分表内匹配 + 保留字面名 (评分表外的未评分候选)
    seen = set()
    result = []
    for pattern in out:
        if any(ch in pattern for ch in "*?"):
            for key in entries:
                if glob_match(pattern, key) and key not in seen:
                    seen.add(key)
                    result.append(key)
        else:
            if pattern not in seen:
                seen.add(pattern)
                result.append(pattern)
    return result


def unit_cost(cost: dict):
    """单位成本 = 0.75×input + 0.25×output.
    返回: float (正成本) | 0.0 (免费, cost 全零) | None (缺失/无效)."""
    if cost.get("input") is None or cost.get("output") is None:
        return None
    try:
        u = 0.75 * float(cost["input"]) + 0.25 * float(cost["output"])
    except (TypeError, ValueError):
        return None
    return u if u > 0 else 0.0


def price_scores(catalog: dict, scope: list, baseline: str):
    """返回 {full: 价格分 | None}. None = 单位成本缺失/无效 → 价格维 N/A (重归一化剔除).
    免费 (cost=0) → 上封顶分, 渲染处标注. baseline 不在目录或成本有效值缺失 → 返回 None (bad-baseline)."""
    baseline_cost = (catalog.get(baseline) or {}).get("cost") or {}
    base = unit_cost(baseline_cost)
    if not base:  # None (缺失/无效) 或 0.0 (免费) 都不能作分母
        return None
    prices = {}
    for full in scope:
        info = catalog.get(full) or {}
        u = unit_cost(info.get("cost") or {})
        if u is None:
            prices[full] = None
        elif u == 0.0:
            prices[full] = PRICE_CAP
        else:
            prices[full] = base / u
    return prices


def supported_levels(catalog: dict, full: str) -> list:
    """直接读目录的 thinking 支持档列表 (平台无关, 已由目录生成时归一化)."""
    info = catalog.get(full) or {}
    return info.get("thinking") or ["off"]


def fmt(v: float) -> str:
    """紧凑数字: 1 / 1.15 / 0.193."""
    return f"{v:.3g}"


def describe(scores: dict, note: str, flags: dict) -> str:
    """把各维比率分/标注/备注拼成一段通顺中文, 让父会话脱离总分按质量底线判断.
    flags: {'unscored', 'partial' (缺失维列表), 'free', 'weak' (evidence 弱依据维列表)}."""
    if flags.get("free"):
        return "免费/零成本: 该模型单位成本为 0, 价格端已封顶, 选型时按最便宜对待." + (
            " 未评分: 各维仍占位, 总分不具区分度." if flags.get("unscored") else ""
        )
    if flags.get("unscored"):
        return "未评分: 各维暂按基准 1 占位, 总分不具区分度."
    strong = [f"{DIM_CN[d]}({fmt(scores[d])})" for d in DIMS if isinstance(scores[d], (int, float)) and scores[d] > 1.05]
    weak = [f"{DIM_CN[d]}({fmt(scores[d])})" for d in DIMS if isinstance(scores[d], (int, float)) and scores[d] < 0.95]
    parts = []
    if strong:
        parts.append("强于基准: " + ", ".join(strong))
    if weak:
        parts.append("弱于基准: " + ", ".join(weak))
    if not parts:
        parts.append("各维与基准基本持平")
    partial = flags.get("partial")
    if partial:
        parts.append(f"[部分评分] 缺维: {', '.join(DIM_CN.get(d, d) for d in partial)}")
    weak_ev = flags.get("weak")
    if weak_ev:
        parts.append("[弱依据] " + ", ".join(DIM_CN.get(d, d) for d in weak_ev))
    if note:
        parts.append(f"备注: {note}")
    return "; ".join(parts)


def fail(reason: str, detail: str = "") -> None:
    sys.stderr.write(f"{reason}: {detail}\n" if detail else f"{reason}\n")
    sys.exit(1)


def build_rows(catalog: dict, entries: dict, scope: list, prices: dict) -> list:
    rows = []
    for full in scope:
        entry = entries.get(full)
        unscored = entry is None or not isinstance(entry, dict)
        # 显式 null = N/A, 键缺失 = 该维 N/A 并标 [部分评分] (不静默按 1).
        # price 是派生维 (来自目录), 评分表不存, 不计入缺维检测.
        raw = entry if isinstance(entry, dict) else {}
        missing = []
        scores = {}
        for d in DIMS:
            if d == "price":
                continue
            if d in raw:
                scores[d] = raw[d]
            else:
                scores[d] = None
                missing.append(d)
        if prices.get(full) is None:
            scores["price"] = None
            free = False
        else:
            scores["price"] = prices[full]
            free = prices[full] == PRICE_CAP
        # 画像总分: 权重>0 且该维非 N/A 的维度加权, 重归一化; 必需维度 N/A → 该画像无总分.
        totals = {}
        for prof, weights in PROFILES.items():
            req = REQUIRED.get(prof)
            if req and scores[req] is None:
                totals[prof] = None
                continue
            wsum = 0.0
            acc = 0.0
            for w, d in zip(weights, DIMS):
                s = scores[d]
                if w > 0 and s is not None:
                    wsum += w
                    acc += w * s
            totals[prof] = acc / wsum if wsum > 0 else None

        note = raw.get("note") or ""
        weak_ev = []
        ev = raw.get("evidence")
        if isinstance(ev, dict):
            for d, txt in ev.items():
                if d in DIMS and ("弱" in str(txt)):
                    weak_ev.append(d)
        # 未评分时缺维不算部分评分.
        flags = {
            "unscored": unscored,
            "partial": [] if unscored else missing,
            "free": free,
            "weak": weak_ev,
        }
        if not unscored and not missing and not free and not weak_ev:
            flags = {}
        rows.append({
            "full": full,
            "unscored": unscored,
            "scores": scores,
            "totals": totals,
            "levels": supported_levels(catalog, full),
            "note": note,
            "flags": flags,
        })
    return rows


def render(rows: list) -> str:
    # 排序仅供参考 (见 SKILL.md 读表规则): 已评分按 general 画像总分降序, 未评分殿后.
    rows.sort(key=lambda r: (r["unscored"], -(r["totals"]["general"] or 0)))
    blocks = []
    for r in rows:
        dims = " | ".join(
            f"{d} N/A" if r["scores"][d] is None else f"{d} {fmt(r['scores'][d])}" for d in DIMS
        )
        totals = " / ".join(
            f"{p} —" if t is None else f"{p} {t:.3f}" for p, t in r["totals"].items()
        )
        tag = " [未评分]" if r["unscored"] else (" [免费]" if r["flags"].get("free") else "")
        blocks.append("\n".join([
            f"{r['full']}{tag}",
            f"  各维: {dims}",
            f"  画像总分: {totals}",
            f"  {describe(r['scores'], r['note'], r['flags'])}",
            f"  thinking 支持: {'/'.join(r['levels'])}",
        ]))
    text = "\n".join(blocks)
    if any(r["unscored"] for r in rows):
        text += "\n\n存在未评分模型: 可读 bootstrap.md 重跑调研补评."
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description="渲染 llm-select 选型表")
    parser.add_argument("--scores", type=Path, default=DEFAULT_DATA_DIR / "llm-scores.json",
                        help="评分表路径 (默认 ~/.agents/llm-select/llm-scores.json)")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_DATA_DIR / "model-catalog.json",
                        help="模型目录路径 (默认 ~/.agents/llm-select/model-catalog.json)")
    parser.add_argument("--scope", type=str, default=None,
                        help="候选范围: 完整候选集 (glob, 空格/逗号分隔), 替换缺省. 缺省用评分表 models 键.")
    args = parser.parse_args()

    catalog = load_catalog(args.catalog)
    baseline, entries = load_table(args.scores)
    scope = resolve_scope(args, entries)
    if not scope:
        fail("bad-scope", "--scope 未匹配到任何模型")
    prices = price_scores(catalog, scope, baseline)
    if prices is None:
        fail("bad-baseline", f"{baseline} (不在模型目录或单位成本无效)")
    rows = build_rows(catalog, entries, scope, prices)
    print(render(rows))


if __name__ == "__main__":
    main()
