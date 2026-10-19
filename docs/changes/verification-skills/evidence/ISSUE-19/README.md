# ISSUE-19 证据索引: 粗估例外范围, 微基准端到端, 引用与文风

## 交付了什么

只改 `workflow/benchmark-checklist/SKILL.md` 一份正文, 分三处:

- 粗估例外恢复原范围: 单次粗估只强制第 4 问 (失败计数与输出正确性) 与第 7 问 (工作在计时区), 其余五问不额外强制, 并写明粗估不动用调优 / 重复 / 上限 / 基线四节的完成标准. 覆盖评审发现 4 与 `TECHNICAL.md:54`.
- 微基准旁边必须附用户端到端实测与整条路径占比; 补不齐就列缺口, 结论停在函数层. 覆盖评审发现 5 与 `PRODUCT.md` AC-030-3.
- 引用可解析 (新增七问到节的对照行), 去掉 U+2014, 被动句与第三人称 "用户", 拆开超长句. 覆盖 STANDARDS H1/H2/H4 的 benchmark 部分.

未改 `PRODUCT.md` / `TECHNICAL.md` / `DECISIONS.md` / 既有 Spec / `reference/PROVENANCE.md` (后者归 ISSUE-20).

## 固定记录

- 待测源路径: `workflow/benchmark-checklist/SKILL.md`, 分支 `issue/19`.
- 交付版 sha256: `fdc3863c7015a0e62c92e496fc2779d0e3212b10a0302a80ef28f38edb3a7697`.
- 修前版 (红轮基准) sha256: `2cfac860e071d6e1050c60512ea3c961fe92bfd9079696dc7e26d11ede1f5e48` (分支顶端 `5c21b0b` 的内容).
- 变异版 (红轮二轮, 把缺陷写显) sha256: `fac014d0683b4a9f3c770ec6a9e1e3b37b3784288c956b3c408e22e97282383e`, 与修前版只差两行, `diff` 见 `mutant.diff`.
- 宿主: Ubuntu 26.04 LTS x86_64, 16 核; pi 1.3.0; herdr 0.9.4; Python 3.14.7.
- 加载方式: 临时项目 `.agents/skills/benchmark-checklist/` 放技能的源目录副本, 在项目 cwd 起新 pi 会话, 模型 `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`, 启动参数 `pi --model ... --thinking high -a`; `-a` 只信任本次临时项目, 未改全局配置. 任务用 `/skill:benchmark-checklist <任务>` 点名, 会话转录里带 `<skill name="benchmark-checklist" location="/tmp/orchestra-19/<项目>/.agents/skills/benchmark-checklist/SKILL.md">`, 见 `sessions/`.
- 提交渠道: `herdr pane send-text <pane> '<任务>'` + `herdr agent send-keys <名> "alt+\"`; 状态用 `herdr agent get` 与 `herdr pane read --source recent-unwrapped` 核对; 原始输出落在 `outputs/`.

## 临时项目

| 项目 | 起始提交 | 技能版本 | 用途 |
| --- | --- | --- | --- |
| `/tmp/orchestra-19/red-lab` | `ab5356f` (夹具 `229364b`) | 修前版 | 交付前文本的两次真实场景 |
| `/tmp/orchestra-19/red2-lab` | `6c4ed75` (夹具 `33649bd`) | 变异版 | 缺陷写显后的红轮 |
| `/tmp/orchestra-19/red3-lab` | `64e27c9` (夹具同源) | 变异版 | 同产出成品入口下的红轮 |
| `/tmp/orchestra-19/green-lab` | `12d37b0` (夹具 `15e4866`) | 交付版 | 绿轮 |
| `/tmp/orchestra-19/green2-lab` | `7554825` (夹具 `6647420`) | 交付版 | 同产出成品入口下的绿轮 |

夹具由 `setup-fixture.sh` 生成, 可重跑: 200000 行 `data/rows.csv`, `src/index_lite.py` 与 `src/index_fast.py` 两套索引, 成品入口 `src/report.py:export_report`, 只给内层函数计时的 `bench/micro.py`, 单次端到端 `bench/export_once.py`, 待核验主张 `docs/claim.md`. 所有数字都是受控材料, 不代表真实产品.

## AC 与证据对照

| 验收标准 | 证据 |
| --- | --- |
| 粗估例外范围恢复, 有演练证据 | `TS-001-estimate.md`, 原始输出 `outputs/red1-ts001.log`, `outputs/red3-mutant-ts001.log`, `outputs/green1-ts001.log` |
| 微基准旁必附端到端实测或缺口, 有演练证据 | `TS-002-e2e.md`, 原始输出 `outputs/red5-mutant-ts002.log`, `outputs/green3-ts002.log`, `outputs/red2-ts002.log`, `outputs/red4-mutant-ts002.log`, `outputs/red2b-ts002.log` |
| 悬空引用与文风问题已修正, 有扫描证据 | `TS-003-references-style.md`, `red-style-scan.log`, `machine-checks.log` |

## 机械检查

见 `machine-checks.log`, `skill-tests.log`, `full-suite.log`, `cleanup.log`.

- `check_skill.py`: 退出 0.
- 全角标点扫描与 U+2014 扫描: 无命中 (rg 退出 1).
- `check-issue19.py` 自检: 通过; 对交付版: 退出 0; 对修前版: 20 处命中 (见 `red-style-scan.log`). 自检里的违规样本故意带 U+2014 与全角内容, 是检测器的输入, 不是正文.
- `general/writing-for-llm/tests`: 7 passed.
- 全量快层: `6 failed, 659 passed`, 与开工基线同为 6 条 (浏览器与 mailbox 超时, 与本改动无关).
