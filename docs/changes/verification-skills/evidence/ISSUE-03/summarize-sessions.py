#!/usr/bin/env python3
"""整理 ISSUE-03 演练会话记录: 每个 pi 会话的启动时间, 工具调用与"谁运行了成品".

只读 sessions/ 下的原始 JSONL, 输出 SUMMARY.md. 不替任何会话决定结论.
用法: uv run python summarize-sessions.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import re

BASE = Path(__file__).resolve().parent
SESSIONS = BASE / "sessions"
CST = timezone(timedelta(hours=8))


def first_user_text(entries: list[dict]) -> str:
    for entry in entries:
        if entry.get("type") != "message":
            continue
        msg = entry.get("message") or {}
        if msg.get("role") != "user":
            continue
        parts = msg.get("content") or []
        chunks = []
        for part in parts:
            if isinstance(part, dict) and part.get("type") == "text":
                chunks.append(part.get("text") or "")
            elif isinstance(part, str):
                chunks.append(part)
        text = "\n".join(chunks)
        text = re.sub(r"<skill[^>]*>", "", text)
        text = text.replace("</skill>", "")
        text = re.sub(r"\s+", " ", text).strip()
        return text[:120]
    return ""


def main() -> None:
    rows = []
    for path in sorted(SESSIONS.glob("*/*.jsonl")):
        entries = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        meta = next(e for e in entries if e.get("type") == "session")
        cwd = meta.get("cwd", "")
        sid = meta.get("id", "")
        started = datetime.fromisoformat(meta["timestamp"].replace("Z", "+00:00"))
        bash = product = prep = herdr = commit = writes = edits = 0
        samples: list[str] = []
        exec_product = re.compile(r"python3?\s+(?:[^\s/]+/)*tool\.py\b")
        exec_prepare = re.compile(r"(?:bash|sh)\s+(?:[^\s/]+/)*prepare\.sh\b")
        herdr_control = re.compile(r"herdr\s+(?:tab|agent|pane)\s+")
        for entry in entries:
            if entry.get("type") != "message":
                continue
            msg = entry.get("message") or {}
            for part in msg.get("content") or []:
                if not isinstance(part, dict) or part.get("type") != "toolCall":
                    continue
                name = part.get("name")
                args = part.get("arguments") or {}
                if name == "bash":
                    cmd = args.get("command") or ""
                    bash += 1
                    forwarded = "herdr pane send-text" in cmd or "herdr agent prompt" in cmd
                    if exec_product.search(cmd) and not forwarded:
                        product += 1
                        if len(samples) < 2:
                            samples.append(cmd.replace("\n", " ; ")[:100])
                    if exec_prepare.search(cmd):
                        prep += 1
                    if herdr_control.search(cmd):
                        herdr += 1
                    if re.search(r"git\s+commit", cmd):
                        commit += 1
                elif name == "write":
                    writes += 1
                elif name == "edit":
                    edits += 1
        last = entries[-1].get("timestamp")
        rows.append(
            {
                "cwd": cwd,
                "session": sid,
                "start_cst": started.astimezone(CST).strftime("%Y-%m-%d %H:%M:%S"),
                "start_utc": started.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "last": last,
                "bash": bash,
                "product_runs": product,
                "prep_runs": prep,
                "herdr_calls": herdr,
                "commits": commit,
                "writes": writes,
                "edits": edits,
                "samples": " / ".join(samples) if samples else "-",
                "first_user": first_user_text(entries),
                "file": str(path.relative_to(BASE)),
            }
        )

    lines = [
        "# 演练会话记录摘要 (机械统计)",
        "",
        "本文件由 `summarize-sessions.py` 从 `sessions/` 下的原始 pi 会话 JSONL 统计得出, 只数工具调用次数与启动时间, 不判断结论. 原始记录见同目录 `sessions/`. 时间为启动时刻 (CST 与 UTC).",
        "",
        "`product_runs` 统计命令里出现 `python3 tool.py ...` 的 bash 调用, 并排除 `herdr pane send-text` / `herdr agent prompt` 这种把命令文本转交给验收者的转发调用; 只读源码, 在文档里 grep 或写任务书提及 `tool.py` 都不计入. 该列是线索, 不是判定: 少数写任务书的 heredoc 可能仍被计入, 逐条人工复核结论见 `README.md` 的指挥者操作审计; `prep_runs` 统计真正执行 `prepare.sh` 的次数; `herdr_calls` 统计 `herdr tab|agent|pane` 控制调用. 指挥者应有的特征是 `product_runs=0` 且 `herdr_calls>0`; 验收者反之. `执行样例` 列出前两段真正执行成品的命令原文, 便于复核计数口径.",
        "",
        "| 工作目录 | 会话 ID | 启动 (CST) | 启动 (UTC) | bash | product_runs | prep_runs | herdr_calls | git commit | write | edit | 执行样例 | 第一条用户文本 (截断) |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {cwd} | `{session}` | {start_cst} | {start_utc} | {bash} | {product_runs} | {prep_runs} | {herdr_calls} | {commits} | {writes} | {edits} | {samples} | {first_user} |".format(
                **row
            )
        )
    (BASE / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"已写 SUMMARY.md, 共 {len(rows)} 个会话")


if __name__ == "__main__":
    main()
