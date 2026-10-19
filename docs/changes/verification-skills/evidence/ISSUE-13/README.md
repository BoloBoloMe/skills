# ISSUE-13 证据索引

本目录是 ISSUE-13 "两个复刻包的许可, 来源与行为保真" 的原始材料: 两个复刻包随附完整 MIT 文本, 固定 SHA 来源与逐项差异记录, translate-a-skill 第 7 节校验结果, 以及在临时项目里各跑一个代表场景的会话记录.

## 文件

- `TS-001.md`: 静态交付切片 (许可, 固定来源, 逐项差异记录, 校验命令), 含红轮与绿轮.
- `TS-002-drill.md`: 行为保真切片, 两个复刻各一个代表场景, 红轮变异版与会话结论.
- `HANDOFF.md`: 交付报告, 每条验收标准对应的证据, 命令与退出码, 缺口.
- `machine-checks.log`: 机械检查原始输出 (`check_skill.py`, 标点扫描, 残留英文, 标题结构, 两个核对脚本, writing-for-llm 测试).
- `full-suite.log`: 全量快层 `uv run --with pytest python -m pytest -m "not e2e" -q` 原始输出.
- `upstream-fetch.log`: 固定 SHA 的只读抓取命令, HTTP 返回码与 sha256.
- `upstream/`: 上游三份原文副本 (两个 SKILL.md 与 `pstack/LICENSE`), 未改字节.
- `sessions/`: 绿轮两个会话的 pi 转录 (jsonl).
- `red-round/`: 红轮两个会话的 pi 转录 (jsonl).
- `drill-artifacts/`: 会话写的证明脚本与测量脚本原件.
- `setup-fixture.sh`: 重建 `/tmp/orchestra-13/lab` 临时项目的夹具脚本.
- `check-provenance-artifacts.py`: 静态交付核对脚本 (TS-001), 退出码 0 表示许可与差异记录齐全.
- `check-drill-evidence.py`: 演练记录核对脚本 (TS-002), 退出码 0 表示记录可对照.
- `red-ts001-provenance-check.log`, `red-ts002-drill-check.log`: 两次红轮的失败输出.

## 环境

- 宿主: Ubuntu 26.04.1 LTS x86_64, 内核 7.0.0-31-generic, 16 核.
- pi 1.3.0, herdr 0.9.4, Python 3.14.7.
- 演练模型: `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`, 启动参数 `pi --model cli/deepseek-v4.1-flash-expires-on-0910 --thinking high -a`.
- 加载方式: 临时项目 `.agents/skills/<名>/` 副本加 `/skill:<名>` 点名加载, 转录里带实际 location.

## 复核入口

```bash
uv run python docs/changes/verification-skills/evidence/ISSUE-13/check-provenance-artifacts.py
uv run python docs/changes/verification-skills/evidence/ISSUE-13/check-drill-evidence.py
uv run python general/writing-for-llm/check_skill.py workflow/blast-radius/SKILL.md
uv run python general/writing-for-llm/check_skill.py workflow/benchmark-checklist/SKILL.md
```

## 边界

- 演练数字与行为都来自受控夹具, 不代表真实产品性能或真实仓库风险.
- 演练只在单一宿主与 pi 1.3.0 + herdr 0.9.4 上做过; 未运行 `sync-to-pi.py`, 未写任何全局部署副本, 结论不覆盖全局部署已生效.
- `*.jsonl` 与 `*.log` 里的全角标点是原始会话与原始输出, 按原样保存不改; 全角标点扫描的范围是两个技能包与本目录中文文档.
