# ISSUE-19 交接报告

## 状态

完成. 分支 `issue/19`, 实现提交 `2e12584` (`feat: ISSUE-19: 恢复粗估例外范围并强制微基准旁附端到端占比`), 证据与本文档在后续 docs 提交里, 工作树干净.

## 交付了什么

只改 `workflow/benchmark-checklist/SKILL.md`:

1. 粗估例外恢复原范围 (评审发现 4, `TECHNICAL.md:54`): 单次粗估只强制第 4 问 (失败计数与输出正确性) 与第 7 问 (工作在计时区), 其余五问不额外强制, 并写明粗估不动用调优 / 重复 / 上限 / 基线四节的完成标准; 选型仍不算粗估. 完成标准同步改写.
2. 微结果旁必须附端到端 (评审发现 5, AC-030-3): 走真实入口, 带真实数据规模与并发, 给出整条路径占比; 授权内补不齐就列缺口, 结论停在函数层, 不写成路径收益. 完成标准同步改写.
3. 引用与文风 (H1/H2/H4): 新增七问与节的对照行, "第 4/7 问" 因此可解析; 去掉 U+2014; 9 处被动改主动, 2 处第三人称 "用户" 改 "我", 2 处超长句拆开.

未改: `PRODUCT.md` / `TECHNICAL.md` / `DECISIONS.md` / 既有 Spec / `reference/PROVENANCE.md` / 其他技能. 未运行 `sync-to-pi.py`, 未写任何全局部署副本, 未做远端 Git 动作.

## AC 与证据

| 验收标准 | 证据文件 | 结论 |
| --- | --- | --- |
| 粗估例外范围恢复, 有演练证据 | `TS-001-estimate.md`; `outputs/red1-ts001.log`, `outputs/red1b-ts001.log`, `outputs/red1c-ts001.log`, `outputs/red3-mutant-ts001.log`, `outputs/green1-ts001.log` | 修前版三次真实场景无偏离; 变异版 (缺陷写显) 出现偏离; 交付版按"只强制第 4/7 问"行事 |
| 微基准旁必附端到端实测或缺口, 有演练证据 | `TS-002-e2e.md`; `outputs/red2-ts002.log`, `outputs/red2b-ts002.log`, `outputs/red4-mutant-ts002.log`, `outputs/red5-mutant-ts002.log`, `outputs/green2-ts002.log`, `outputs/green3-ts002.log` | 变异版只在函数层发结论, 端到端未跑无占比; 交付版补跑成品入口并给占比, 只留真实规模与并发为缺口 |
| 悬空引用与文风问题已修正, 有扫描证据 | `TS-003-references-style.md`; `red-style-scan.log`, `machine-checks.log` | 修前版 20 处命中, 交付版 0 处, 扫描器自检通过 |

## 跑过的命令与退出码

- `uv run python general/writing-for-llm/check_skill.py workflow/benchmark-checklist/SKILL.md` → 0 (`machine-checks.log`).
- 全角标点 rg 扫描 → 1 (无命中); U+2014 rg 扫描 → 1 (无命中).
- `uv run python check-issue19.py --selftest` → 0; 对交付版 → 0; 对修前版 → 1 (20 处); 对变异版 → 1 (与修前版同一批文风项).
- `uv run --with pytest python -m pytest general/writing-for-llm/tests -q` → 0 (7 passed, 18 subtests).
- `uv run --with pytest python -m pytest -m "not e2e" -q` → 1, `6 failed, 659 passed, 2 skipped`, 与开工基线同为 6 条 (`general/present` 浏览器与 `tests/test_mailbox_admin.py` 超时, 与本改动无关, 见 `full-suite.log`).
- 三个权威输入字节未变: `PRODUCT.md` / `TECHNICAL.md` / `DECISIONS.md` 与主仓库同名文件 sha256 一致.

## 演练现场

- 宿主: Ubuntu 26.04 LTS, 16 核, load average 0.1 到 0.5; pi 1.3.0; herdr 0.9.4; Python 3.14.7.
- 加载: 临时项目 `.agents/skills/benchmark-checklist/` + `/skill:benchmark-checklist` 点名; 会话转录带 `location="/tmp/orchestra-19/<项目>/.agents/skills/benchmark-checklist/SKILL.md"`, 转录在 `sessions/`.
- 临时项目与起始提交: `red-lab` `ab5356f`, `red2-lab` `6c4ed75`, `red3-lab` `64e27c9`, `green-lab` `12d37b0`, `green2-lab` `7554825`; 夹具脚本 `setup-fixture.sh` 可重跑.
- 会话与 tab: `bm19-red1` (t3W), `bm19-red2` (t3X), `bm19-red3` (t47), `bm19-red4` (t48), `bm19-g1` (t49), `bm19-g2` (t4A), `bm19-g3` (t4D), `bm19-red5` (t4E). 全部已关闭, 关闭后 `herdr agent list` 无 `bm19*`, 见 `cleanup.log`.
- 清理: 临时项目在证据抄完后删除; 会话自写脚本已抄到 `drill-artifacts/`.

## 缺口 / 风险 / 未验证项

- 红轮在交付前文本上没有跑出行为偏离 (三次不同场景都照粗估规则行事). 为拿到可对照的红, 加跑一轮变异版, 把评审发现 4 与 5 描述的缺陷写显. 变异版偏离, 交付版无偏离, 但"原文本本身会误导多少模型"没有量化, 只证明缺陷一旦写清就会改变行为.
- 用同一模型 (`deepseek-v4.1-flash-expires-on-0910`) 与 thinking high 跑全部会话, 没有跨模型复验; 文风项只用扫描与通读判定, 没有单开文风会话.
- 端到端实测都在受控夹具上 (200000 行, 37 个 key, 单线程), 没有真实生产并发; 这条缺口在演练记录里如实保留, 未写成已验证.
- `reference/PROVENANCE.md` 里"编号引用改为按节名加原编号"与实际是否一致归 ISSUE-20, 本 ISSUE 未动该文件; 交付版新增了编号到节的对照行, 使该表那句在 benchmark 侧成立, 但差异表的复核仍由 ISSUE-20 负责.
- 全量快层仍有 6 条既有失败, 与基线一致, 未处理也不属本 ISSUE 范围.
