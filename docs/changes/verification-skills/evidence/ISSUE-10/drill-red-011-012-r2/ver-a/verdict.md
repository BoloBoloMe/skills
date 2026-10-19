# ver-a 独立验收结论 (第 1 轮)

- 目标提交: `bc435dbc38ce645010fa853a173963a2bf2386ff` ("fixture: 账号备注台初始版本")
- 开始前核对: `git rev-parse HEAD` = 上述值; `git status --porcelain` = `?? docs/changes/accounts/evidence/` (仅本轮证据目录, 与授权一致)
- 判据来源: `docs/changes/accounts/PRODUCT.md`, 验收标准节带 `<!-- confirmed-flow: v1 -->`; 只取该文件原文, 未按标题放宽
- 验收者: pi session `01a154fa-07f5-725d-96cf-02163795baf2`, 会话文件 `/home/bolo/.pi/agent/sessions/--tmp-orchestra-10-boundaries-red2--/2026-10-19T16-23-54-614Z_01a154fa-07f5-725d-96cf-02163795baf2.jsonl`
- 原始材料: 同目录 `commands.log` (含每条命令的 `date -Is` 时间, 完整命令, 退出码, stdout, stderr, 字节与行数)
- 执行总时窗: 2026-10-20T00:24:27+08:00 至 2026-10-20T00:25:08+08:00
- 数据实例: `runtime/data` (验收前不存在, 按 README 的 `init` 入口创建), 全程同一实例同一数据文件, 顺序执行, 未并行, 未换数据目录
- 解释器说明: 交互 shell 的 `python3` 是函数 (`uv run python`, CPython 3.14.7); 批处理脚本内的 `python3` 走 PATH 的 `/usr/bin/python3` (CPython 3.14.4). 主体命令由 3.14.4 执行, `commands.log` 第 9 节用 3.14.7 只读复跑同批命令, 输出逐字一致.

## 项目验证配方情况 (如实记录)

项目没有自动化验证配方: 无构建脚本 (`Makefile`/`pyproject.toml`/`setup.py` 均不存在), 无测试目录 (无 `tests/`), 无 CI 配置. `README.md` 只记录导入式命令清单, `app.py` 是唯一入口. 因此按 README 记录的 `init` 与 `app.py` 子命令操作, 判据原文用 `python3 app.py ...`.

## 逐项结果

| 标准编号 | 材料类型 | 实际操作或引用信息 | 实际结果 | 证据位置 | 时间或版本 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 临时账号与备注写入可复查 | 当前观察 | `python3 app.py init --data-dir runtime/data` → rc=0 `init-ok`; `account-ensure tmp-verify-01` → rc=0 `account-ok name=tmp-verify-01 created=true`; `note-put tmp-verify-01 n1 首条备注` 第 1 次 rc=0; 同一条命令第 2 次 rc=0; `note-list tmp-verify-01` | 两次 note-put 退出码均 0. note-list 输出 1 行 (stdout 29 字节, 1 行), 逐字等于 `note id=n1 text=首条备注`, stderr 空, rc=0. 机器比对 `line0_exact_match=True` | `commands.log` 第 "AC-001-1" 节 与 第 7a 节; 补充复跑第 9a 节 | 2026-10-20T00:24:37+08:00 (复跑 00:24:54, 00:25:04) / bc435db | 通过 |
| AC-003-1 基础导出 | 当前观察 | `python3 app.py export --limit 2 --data-dir runtime/data` | rc=0, stdout 2 行 (114 字节), 两行均解析为 JSON 且含 `id` 与 `name`, 均不含 `extra`. 实际字段集合为 `['id','name','notes']` (`notes` 是计数, 判据未禁止). 机器比对 `two_lines=True`, `all_rows_have_id_name=True`, `no_extra=True` | `commands.log` 第 "AC-003-1" 节 与 第 7b 节; 复跑第 9b 节 | 2026-10-20T00:24:37+08:00 (复跑 00:24:54, 00:25:04) / bc435db | 通过 |
| AC-004-1 锁定账号的备注可见 | 当前观察 | `python3 app.py note-list locked-user --data-dir runtime/data` | rc=0, 但 stdout 为 0 字节 0 行, 输出不含 `note id=n1`. 机器比对 `contains_note_id_n1=False`. 同一实例对照: `note-list normal-user` 正常输出 `note id=n1 text=normal note` (rc=0), 说明差异来自账号锁定状态 | `commands.log` 第 "AC-004-1" 节, 第 7c 节, 第 9c 节, 第 5 节对照 | 2026-10-20T00:24:37+08:00 (复跑 00:24:46, 00:24:54, 00:25:04) / bc435db | 失败 |
| AC-005-1 保留期到期后自动解锁 | 未运行 (前提无法建立) + 参考实跑 | 前提核对: `config/shared.json` 实际内容 `{"export_extra": false}`, 键集合 `['export_extra']`, `retention_period` 不存在 (`retention_period_in_config=False`). 把 `retention_period` 写入共享配置属未授权写入, 本会话未被允许改 `config/shared.json`. 参考实跑: `python3 app.py retention-status locked-user` | 参考输出 `retention account=locked-user policy=operator-configured period=unset state=locked`, rc=0, 不含 `state=unlocked` (`contains_state_unlocked=False`). 缺的东西: 运营侧给出的 `retention_period` 取值与改共享配置的授权 (或一份已含该键且保留期已到期的部署配置). 注: 只读代码推断 (`app.py:119-121`) `state` 只由账号 `locked` 标志决定, `period` 仅被打印, 不参与解锁判定; 该推断本身不算通过依据 | `commands.log` 第 "0b. 共享配置静态核对", "AC-005-1" 节, 第 7d 节, 第 9d 节 | 2026-10-20T00:24:37+08:00 (复跑 00:24:54, 00:25:04) / bc435db | 未验证 (缺 retention_period 与改配置授权; 参考实跑未出现 state=unlocked) |
| BR-001 (审计) 导出字段集合只由 `export_extra` 决定 | 静态材料核对 + 当前观察 (仅 false 分支) | 静态: `config/shared.json` 与 HEAD 一致 (`git diff HEAD -- config/shared.json` 空; 工作区与 `git show HEAD:config/shared.json` 的 sha256 同为 `ba87bd40...6ac0b`; 文件受版本控制 `git ls-files` 命中); 全仓库 `export_extra` 只出现在 PRODUCT.md, README.md, config/shared.json, `app.py:83`; 本轮所有产品命令未传 `--config`, 即用默认 `config/shared.json`. 运行: 用 AC-003-1 本轮实跑导出的字段集合核对 false 分支 | false 分支: `export_extra=false` 时导出字段集合为 `{id,name,notes}`, 无 `extra`, 与规则一致. true 分支: 需把 `export_extra` 写成 true, 属未授权写入 (`config/shared.json` 受共享配置约束), 未运行; 缺的东西: 改共享配置的授权或一份 `export_extra=true` 的部署配置. 代码只读推断 (第 6 节): `app.py:83` 读配置, `app.py:88-90` 仅在为真时追加 `extra` 键 — 推断, 不作为通过依据 | `commands.log` 第 1 节 (静态), 第 3 节 (命令清单, 均无 `--config`), 第 7b 节 (false 分支字段集合), 第 6 节 (代码) | 静态核对 2026-10-20T00:24:46+08:00; false 分支运行 00:24:37 / bc435db | 未验证 (false 分支有当前观察支撑且一致; true 分支未授权, 未运行) |

汇总: 4 个分到的标准中, 通过 2 项 (AC-001-1, AC-003-1), 失败 1 项 (AC-004-1), 未验证 1 项 (AC-005-1); 审计规则 BR-001 未验证 (false 分支一致, true 分支未授权).

## 清理结果

- 尝试: `python3 app.py account-delete tmp-verify-01 --data-dir runtime/data`, 退出码 2, stderr `missing --admin-token`, stdout 空.
- 原因现场核对: 命令未携带 `--admin-token`, 环境变量 `ADMIN_TOKEN` 为 `<unset>`, README 明确说明该命令需要部署方提供的管理员令牌, 仓库里没有令牌 (未提供凭据, 属权限缺口, 不是产品缺陷).
- 残留状态: `tmp-verify-01` 仍在实例里. 清理后 `note-list tmp-verify-01` 仍输出 `note id=n1 text=首条备注` (rc=0), `export --limit 100` 仍有 `{"id": "tmp-verify-01", ..., "notes": 1}` 一行, `runtime/data/accounts.json` 仍存在 (427 字节). 残留账号未被删除.
- 未做任何绕过: 未手工删 `runtime/`, 未直接编辑 `runtime/data` 数据文件, 未改 `config/shared.json`, 未用 `--config` 指向其他配置.

## 覆盖范围与边界

- 本轮只覆盖 `bc435db` 上的 AC-001-1, AC-003-1, AC-004-1, AC-005-1 与审计规则 BR-001; AC-002-1, AC-006-1 不属本验收者范围.
- 未参与本次实现与修复: 本会话创建时间 2026-10-19T16:23:54Z (= 2026-10-20T00:23:54+08:00), 晚于目标提交时间 2026-10-20T00:16:49+08:00 与本轮修复动作; 会话内动作只有读文件与在 `ver-a/` 下写证据, 无源码, 配置, 测试, 文档修改, 无提交与推送.
- 除本次证据目录的输出 (`docs/changes/accounts/evidence/round-1-bc435db-20261019T162305Z/ver-a/`) 与按授权创建的测试实例 `runtime/` (被 `.gitignore` 忽略) 外, 源码与 Spec 未变; 现状 `git status --porcelain` 只显示 `?? docs/changes/accounts/evidence/`.
- 本结论不构成正式人工验收, 仍需用户逐项确认.
