# ISSUE-01 演练记录 (verify-change 第一切片: 判据与目标版本)

## 待测对象

- 待测源文件: `workflow/verify-change/SKILL.md`, 本工作树, 分支 `issue/01`.
- 基线提交: `ec9d55f` (此时该目录尚不存在, 用于第一条失败演练).
- 演练实际加载的内容与最终提交一致, md5 `6851c67d67f1001a0c0d3d93a9e3418c`.
  失败演练另有一版只有判据规则、没有版本前提与证据目录规则的中间稿, md5 `f0e8aa0d4a396388708f9e55f1cae2e8`, 内容见 `incidents/frontmatter-conflict/SKILL-v1-broken-frontmatter.md` (该文件只有 description 行不同, 正文即本版 v1 正文).
- 宿主: Ubuntu 26.04 LTS (x86_64); herdr 0.9.4; pi 1.3.0; python3 3.14.7.
- 模型与深度: `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`.
- 启动命令: `herdr agent start <会话名> --kind pi --pane <窗格ID> -- --model cli/deepseek-v4.1-flash-expires-on-0910 --thinking high -a`.
  `-a` 只对本次会话做项目信任, 未改全局配置.
- 加载方式: 把待测目录复制到临时项目的 `.agents/skills/verify-change/`, 在项目 cwd 的新 pi 会话里用 `herdr pane send-text` 提交 `/skill:verify-change <任务>`, 再用 `herdr agent send-keys <名> "alt+\\"` 提交. 会话启动横幅 `[Skills]` 列表含 `verify-change`, 且无 `[Skill conflicts]` 段, 见各日志开头.

## 临时项目夹具

`setup-drills.sh` 在 `/tmp/orchestra-01/` 生成, 全部是临时 Git 项目, 未写入仓库其他位置.
PRODUCT.md 用 to-spec 的真实转正流程 (`ac-draft.py preview` 取 review_id, 再 `promote`) 生成, 因此带真实确认标记 `<!-- confirmed-flow: v1 -->`, 不是手写假标记; 转正后另跑 `check-ac.py` 通过.

| 夹具 | 起始提交 | 状态 | 用途 |
| --- | --- | --- | --- |
| `a-committed-clean` | `612f1ea907e9cda398b14a08faa80dbb48e49b6c` | 干净 | 产品含 2 个场景 (AC-001-1 通过, AC-002-1 稳定失败) 与 1 条审计 BR; 另放 TECHNICAL.md (要求拆 `lib/args.py`, 产品未提) 与全部 `[x]` 的 EXECUTION.md |
| `c-no-product` | `0c59f74c9207ec2c90414b70b5a3f873add0628d` | 干净 | 只有 TECHNICAL.md 与 EXECUTION.md, 无 PRODUCT.md |
| `d-dirty` | `612f1ea907e9cda398b14a08faa80dbb48e49b6c` | 脏 (` M greet.py`, 把 `Hello` 改成 `Hi`) | 脏工作区 |
| `e-checked-docs` | `2e868d17fa9c3f9d907546faa476db9fe64df97b` | 干净 | 自带 `check_changes.py`, 只允许 `docs/changes/<slug>/` 有 3 份 spec, 多文件即退出码 1, 用于证据目录影响输入的边界 |

夹具项目 `.gitignore` 忽略 `.agents/`, 所以复制技能进去不会把工作区弄脏.

## 会话一览

| 会话名 | 夹具 | 目的 | 记录 |
| --- | --- | --- | --- |
| `v01-red1` | a | 失败演练: 技能文件不存在 | `drill-R1-red-no-skill.log`, 临场产物 `drill-R1-improvised-report.md` |
| `v01-r2b` | d | 失败演练: 只有判据规则时, 脏工作区被当成验收目标 | `drill-R2b-red-dirty-v1-loaded.log`, 仓库内证据 `drill-R2b-into-repo-evidence/` |
| `v01-g1a2` | a | 通过: 判据只取 Product, 绑定起始提交, 输出进约定目录 | `drill-G1a2-green-criteria-target.log`, 证据目录副本 `drill-G1a2-evidence-dir/` |
| `v01-g1b2` | c | 通过: 缺 PRODUCT.md 报输入缺口并停止 | `drill-G1b2-green-missing-product.log` |
| `v01-g2a2` | d | 通过: 脏工作区报版本前提不满足并停止 | `drill-G2a2-green-dirty-stop.log` |
| `v01-g2c2` | e | 通过: 证据目录影响项目检查时外置到仓库外 | `drill-G2c2-green-evidence-external.log`, 外置证据副本 `drill-G2c2-evidence-outside/` |

四个用坏 frontmatter 版本跑的会话 (`v01-g1a`, `v01-g1b`, `v01-r2`, `v01-g2a`) 不算证据, 原因与原始日志见 `incidents/frontmatter-conflict/README.md`.

## 验收标准与证据对应

| 验收标准 | 证据 |
| --- | --- |
| 缺已确认 PRODUCT.md 时报输入缺口并停止 | `drill-G1b2-green-missing-product.log`: 列出三项输入, 标 PRODUCT.md 为缺, 未跑场景, 未写报告, 明确未用 TECHNICAL/EXECUTION 立标准 |
| 技术材料与计划勾选不进入产品通过条件 | `drill-G1a2-evidence-dir/REPORT.md`: "非产品判据事项" 节把 `lib/args.py` 交回技术评审, 并说明 TASK-02 勾选不作证据; `drill-G2c2-evidence-outside/v-2e868d1/REPORT.md` 同款结论 |
| 报告逐项结果绑定起始提交, 脏工作区不被验收 | `drill-G1a2-evidence-dir/REPORT.md` 首段绑定 `612f1ea...`, 每行含命令与原始输出位置; `drill-G2a2-green-dirty-stop.log`: 报告 ` M greet.py`, 停在版本前提, 不跑场景, 不用快照绕过 |
| 证据目录例外规则可观察, 不声称整体工作区干净 | `drill-G1a2-evidence-dir/REPORT.md`: 证据目录 `docs/changes/greet-cli/evidence-612f1ea-r1/` 在仓库内, 附影响判断, 收尾写"除证据目录输出外, 源码与 Spec 未变"; `drill-G2c2-evidence-outside/v-2e868d1/REPORT.md`: 用 `check_changes.py` 前后退出码 (0 / 1) 证明影响, 证据放仓库外 |

逐条 AC 场景对应 (PRODUCT.md):

- AC-001-1, AC-001-3, AC-001-4: `v01-g1a2` 一次实跑承接.
- AC-001-2: `v01-g1b2`.
- AC-008-1, AC-008-4: `v01-g1a2`.
- AC-008-2: `v01-g2a2`.
- AC-008-3: `v01-g2c2`.

## 失败演练到通过的顺序

1. `v01-red1`: 技能目录不存在, `/skill:verify-change` 报 `ENOENT: ... ~/.agents/skills/verify-change/SKILL.md`, 会话只能临场发挥, 产物落在 `docs/changes/greet-cli/ACCEPTANCE.md`, 没有判据来源与证据目录规则.
2. 写入只有判据规则的 v1, 用 `v01-r2b` 演练: 脏工作区照样出报告 (`git archive HEAD` 自造快照当作目标), 结论没被版本前提挡住, 证据目录自选.
3. 补上版本前提与证据目录规则, 再跑 `v01-g1a2`, `v01-g1b2`, `v01-g2a2`, `v01-g2c2` 全部通过.

## 已知偏差与清理

- `incidents/frontmatter-conflict/` 里的四个会话是无效演练, 原因见其 README; 保留原始日志是为说明 `description` 里的 "冒号+空格" 会让 pi 的 YAML 解析失败, 这条 `check_skill.py` 目前放行, 属已知机检缺口, 已写入 HANDOFF.
- `drill-G2c2-evidence-outside/v-2e868d1/probe-repo/` 已删掉 `.git` 与 `.agents/` 目录 (可重建, 与结论无关), 其余文件原样保留.
- 所有演练会话已按 `herdr tab close` 关闭; 临时项目 `/tmp/orchestra-01/` 在证据抄完后删除; 夹具可用 `setup-drills.sh` 重建.
- 演练只证明本工作树源码在记录的宿主/加载方式下有效, 不代表任何全局部署副本已经生效; 未运行 `sync-to-pi.py`.
