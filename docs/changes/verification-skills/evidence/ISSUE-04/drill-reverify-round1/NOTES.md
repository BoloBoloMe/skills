# drill-reverify-round1: 首次验收发现真实缺陷 (绿, AC-007 前置)

## 目的

在带真实缺陷的版本上跑一次首次验收, 为复验提供"上一轮失败"的真实起点, 并留下修复前的原始证据.

## 待测版本与加载方式

- 源文件: 工作树 `workflow/verify-change/SKILL.md` md5 `82cb7913d710dfaf3b898c56d17c618c`, 原件 `../logs/SKILL-v3-green.md`.
- 加载: `/tmp/orchestra-04/reverify/.agents/skills/verify-change/` + `/skill:verify-change`; 指挥者会话首条消息含 `<skill name=... location=...>`.
- 夹具: `/tmp/orchestra-04/reverify`, 目标提交 `cd087542b4610c49ded0a1278fe8065726b62d9d` (含 `report` 状态写死为 `loading` 的缺陷), 产品标准 4 个场景 + 1 条审计 BR.

## 会话

| 角色 | 会话名 | pi session id | 创建 (CST) |
| --- | --- | --- | --- |
| 指挥者 | `i04-v1` | `01a1548b-5e2b-...` (见 `../sessions/` 对应文件) | 22:22:04 |
| 场景组 | `i04-a1-ac` | `01a1548b-b975-7213-9d28-db1121880578` | 22:23:25 |
| 静态审计 | `i04-a1-br` | `01a1548b-a33f-7791-ba88-2ec069ae42e4` | 22:23:19 |

## 实际结果

- `VERIFY-REPORT.md`: 5 项必验, 4 通过, 1 失败; `AC-003-1` 实跑 3 次加一次 raw HTTP, 全部 `state=loading`, 期望 `state=ready`; 失败项是产品行为不符判据.
- 报告写明验收者未修复缺陷; 场景组与静态审计组各自独立结论.
- 该失败是本 ISSUE 复验演练的真实起点; 修复由 `i04-a1-ac` 在验收结束后承担, 见 `../drill-reverify-round2/NOTES.md`.
