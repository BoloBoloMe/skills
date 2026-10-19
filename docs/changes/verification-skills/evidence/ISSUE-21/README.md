# ISSUE-21 证据: create / maintain 的视角与重复批准规则

- 分支 `issue/21`, 起点提交 `711b463` (主仓库 `v2` 顶端 `ec9d55f`).
- 待改文件: `workflow/create-verification-skill/SKILL.md`, `workflow/maintain-verification-skill/SKILL.md`.
- 权威依据: `../code-review/STANDARDS-2.md` 的 N1 (硬性, 叙述视角倒退) 与 N3 (判断性, 重复指令).
- 环境: Linux 7.0.0-31-generic x86_64, Python 3.14.7, pi 1.3.0, herdr 0.9.4.

本 ISSUE 是纯写作面修订, 不改批准语义, 不改运行时加载行为, 所以按任务书"通常不需要真会话演练"处理: 未开 herdr 会话, 未建临时项目, 没有需要清理的运行期资源. 演练证据仍以机械扫描与 diff 为主, 见下.

## 材料

| 文件 | 内容 |
| --- | --- |
| `check-issue21.py` | 本次的机械审计脚本 (视角 / 逐字重复 / 单一真相源与指针 / 资源清单保留) |
| `TS-001-voice-dedupe.md` | 唯一 TDD 切片: 判据, 红绿对照, 差异要点, 语义保持说明 |
| `red-voice-dedupe.log` | 红轮: 起点提交上跑扫描, `hits=10`, 退出码 1 |
| `green-voice-dedupe.log` | 绿轮: 修订后跑扫描, `hits=0`, 退出码 0 |
| `diff-skills.log` | 两份 SKILL.md 的 `git diff` (重复段并入一处, 视角改写) |
| `machine-checks.log` | `check_skill.py` 两份退出 0, 全角标点扫描无命中, 英文残留清单 |
| `full-suite.log` | 全量快层 `pytest -m "not e2e" -q` 结果 |
| `HANDOFF.md` | 收工报告 |

## 复跑方式

```bash
uv run python docs/changes/verification-skills/evidence/ISSUE-21/check-issue21.py \
  workflow/create-verification-skill/SKILL.md workflow/maintain-verification-skill/SKILL.md
```

退出码 0 表示视角与去重两项都过, 1 表示有命中并逐条打印位置.
