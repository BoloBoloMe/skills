#!/usr/bin/env python3
"""llm-select/score.py — 子代理选型表渲染, 算分唯一真相源 (仅标准库).

无画像入参: 判画像是 LLM 的判断, 程序输出七画像全矩阵 + 各维明细 + thinking 支持档, 一次给全决策材料.
数据源 (评分表 ~/.agents/llm-select/llm-scores.json, 每台设备一份, bootstrap.md 建立;
  其余在 agent 目录 = PI_CODING_AGENT_DIR, 默认 ~/.pi/agent):
  模型目录/价格/thinking 支持 models-store.json (+ models.json 覆盖同名 provider),
  候选范围 = settings.json enabledModels (glob) ∩ 有凭证 provider (auth.json / apiKey).
失败时向 stderr 输出原因并退出 1: no-table / no-scoped / bad-baseline / bad-json.
"""

import json
import os
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

LEVELS = ["off", "minimal", "low", "medium", "high", "xhigh", "max"]

SKILL_DIR = Path(__file__).resolve().parent
BOOTSTRAP_PATH = SKILL_DIR / "bootstrap.md"


def agent_dir() -> Path:
    return Path(os.environ.get("PI_CODING_AGENT_DIR") or Path.home() / ".pi" / "agent")


def scores_path() -> Path:
    """评分表固定在 ~/.agents/llm-select/ 下, 不随 agent 目录移动."""
    return Path.home() / ".agents" / "llm-select" / "llm-scores.json"


def read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_store() -> dict:
    store = read_json(agent_dir() / "models-store.json") or {}
    custom = read_json(agent_dir() / "models.json") or {}
    # 自定义 provider (如网关) 合并入目录, 覆盖同名.
    store.update(custom.get("providers") or {})
    return store


def authed_providers(store: dict) -> set:
    """有凭证 = auth.json 有条目, 或 apiKey 非空 (字面量, 或 $ENV 引用的环境变量存在)."""
    out = set((read_json(agent_dir() / "auth.json") or {}).keys())
    for provider, spec in store.items():
        key = (spec or {}).get("apiKey")
        if not key:
            continue
        if key.startswith("$"):
            if os.environ.get(key[1:]):
                out.add(provider)
        else:
            out.add(provider)
    return out


def glob_match(pattern: str, value: str) -> bool:
    """最小 glob: * → 任意串, ? → 任意字符; 够用 enabledModels 模式 (如 provider/* 或裸 model id)."""
    return re.fullmatch(re.escape(pattern).replace(r"\*", ".*").replace(r"\?", "."), value) is not None


def load_scoped(store: dict) -> list:
    """候选 = enabledModels (glob) 匹配目录 ∩ 有凭证 provider."""
    patterns = (read_json(agent_dir() / "settings.json") or {}).get("enabledModels") or []
    authed = authed_providers(store)
    out = []
    for provider, spec in store.items():
        if provider not in authed:
            continue
        for m in (spec or {}).get("models") or []:
            full = f"{provider}/{m['id']}"
            if any(glob_match(p, full) or glob_match(p, m["id"]) for p in patterns):
                out.append(full)
    return out


def price_scores(store: dict, scoped: list, baseline: str):
    """单位成本 = 0.75×input + 0.25×output; 价格分 = 基准单位成本 ÷ 该模型单位成本.
    基准不在目录或成本为零 → None (响亮失败, 不静默降级)."""
    units = {}
    for provider, spec in store.items():
        for m in (spec or {}).get("models") or []:
            full = f"{provider}/{m['id']}"
            if full in scoped or full == baseline:
                cost = m.get("cost") or {}
                units[full] = 0.75 * (cost.get("input") or 0) + 0.25 * (cost.get("output") or 0)
    base = units.get(baseline)
    if not base:
        return None
    return {m: base / u for m, u in units.items() if u > 0}


def find_model(store: dict, full: str):
    provider, _, mid = full.partition("/")
    for m in (store.get(provider) or {}).get("models") or []:
        if m.get("id") == mid:
            return m
    return None


def supported_levels(store: dict, full: str) -> list:
    """reasoning=false 仅 off; thinkingLevelMap 键存在且值为 null → 不支持; 键缺失 → 支持, 但 xhigh/max 须显式映射."""
    model = find_model(store, full)
    if not model or not model.get("reasoning"):
        return ["off"]
    tmap = model.get("thinkingLevelMap")
    if tmap is None:
        return LEVELS[:5]
    out = []
    for level in LEVELS:
        if level in tmap:
            if tmap[level] is not None:
                out.append(level)
        elif level not in ("xhigh", "max"):
            out.append(level)
    return out


def fmt(v: float) -> str:
    """紧凑数字: 1 / 1.15 / 0.193."""
    return f"{v:.3g}"


def describe(scores: dict, note: str, unscored: bool) -> str:
    """把各维比率分与备注拼成一段通顺中文, 让父会话能脱离总分按质量底线自行判断."""
    if unscored:
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
    if note:
        parts.append(f"备注: {note}")
    return "; ".join(parts)


def fail(reason: str, detail: str = "") -> None:
    sys.stderr.write(f"{reason}: {detail}\n" if detail else f"{reason}\n")
    sys.exit(1)


def main() -> None:
    sp = scores_path()
    if not sp.exists():
        fail("no-table", str(sp))
    try:
        table = json.loads(sp.read_text(encoding="utf-8"))
        if not isinstance(table, dict):
            raise ValueError("内容为空或非对象")
    except SystemExit:
        raise
    except Exception as e:
        fail("bad-json", f"{sp} ({e})")
    baseline = table.get("baseline")
    if not baseline:
        fail("bad-baseline", "(baseline 为空)")
    entries = table.get("models") or {}

    store = load_store()
    scoped = load_scoped(store)
    if not scoped:
        fail("no-scoped")
    prices = price_scores(store, scoped, baseline)
    if prices is None:
        fail("bad-baseline", baseline)

    rows = []
    for full in scoped:
        entry = entries.get(full)
        unscored = entry is None
        # 显式 null = N/A, 键缺失 = 按基准 1 占位.
        scores = {d: (entry or {}).get(d, 1) for d in DIMS}
        scores["price"] = prices.get(full, 1.0)
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
        rows.append({
            "full": full,
            "unscored": unscored,
            "scores": scores,
            "totals": totals,
            "levels": supported_levels(store, full),
            "note": (entry or {}).get("note") or "",
        })
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
        blocks.append("\n".join([
            f"{r['full']}{' [未评分]' if r['unscored'] else ''}",
            f"  各维: {dims}",
            f"  画像总分: {totals}",
            f"  {describe(r['scores'], r['note'], r['unscored'])}",
            f"  thinking 支持: {'/'.join(r['levels'])}",
        ]))
    text = "\n".join(blocks)
    if any(r["unscored"] for r in rows):
        text += f"\n\n存在未评分模型: 可读 {BOOTSTRAP_PATH} 重跑调研补评."
    print(text)


if __name__ == "__main__":
    main()
