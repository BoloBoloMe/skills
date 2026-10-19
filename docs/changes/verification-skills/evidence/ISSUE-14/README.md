# ISSUE-14 演练总表: 收尾前的独立验收节点

本目录是 `docs/changes/verification-skills/issues/ISSUE-14-tdd-orchestra-acceptance-node.md` 的行为证据. 结论来自真实 pi 会话在临时 Git 项目上的实际运行, 不是源码关键词断言. 两次红演练用改动前的技能, 绿演练用改动后的技能.

## 待测对象与版本

- 源文件: 本工作树 `workflow/tdd-as-orchestra/SKILL.md` (分支 `issue/14`, 基线提交 `05b9a64`).
- 三个版本原件在 `logs/skill-versions/`, md5 与用途:

| 版本 | md5 | 内容 | 用在哪 |
| --- | --- | --- | --- |
| v1 | `391709eee88142e356412d846d9f34f0` | 改动前, 执行循环无验收节点 | 红 `red-ts001`, `red-ts002` |
| v2 | `60bcde71bcee6d323c1b66661a4caf59` | 加入独立验收, 验收回传, 收尾引用报告 | 绿 `green-ts001`, `green-ts002-gap-v2` |
| v3 | `f89dac0f2d205e02a60bbf3ae2d37ce9` | 在 v2 上补齐缺口门: 有未验证必验项时不生成讲解页, 不走正常收尾 | 绿 `green-ts002-fix`, `green-ts002-gap2` (中止), `green-ts002-gap-only`, `green-ts001-pending` |

v3 与分支当前文件一致 (`cmp` 通过). 结论只覆盖这份源文件与下面的加载方式, 不表示任何全局部署副本已更新; 本次没有运行 `sync-to-pi.py`.

## 宿主与加载方式

- 宿主: Ubuntu 26.04.1 LTS (x86_64), kernel 7.0.0-31-generic; pi 1.3.0; herdr 0.9.4 (client/server protocol 22); uv 0.12.5, `uv run python` 为 CPython 3.14.7. 明细见 `logs/host-versions.txt`.
- 会话: `pi --provider cli --model deepseek-v4.1-flash-expires-on-0910 --thinking high -a`, `-a` 只做一次性项目信任, 没有改全局配置. 提交渠道 `herdr pane send-text` 加 `herdr agent send-keys "alt+\\"`.
- 加载方式: 待测目录复制到临时项目 `.agents/skills/<name>/` 并提交, 在项目 cwd 开新会话, 用 `/skill:tdd-as-orchestra <任务>` 点名加载. 每个指挥会话的 jsonl 首条用户消息带 `<skill name="tdd-as-orchestra" location="...">`, 位置都指向该项目当前文件, 见 `logs/session-index.txt` 与各 `sessions/*/` 原件.
- 项目里同时提交了 `verify-change`, `code-review`, `explain-diff` 的当前版本, 让被派发的子会话也读项目当前文件; `use-herdr`, `tdd`, `domain-awareness`, `present` 等用本机已有技能.

## 临时项目与预置现场

夹具由 `setup-drills.sh` 在 `/tmp/orchestra-14/` 生成, 都是独立 Git 仓库. 每个现场都预置了"ISSUE-01 已实现并合并, 评审结论已落盘"的状态, 并明确标注为预置, 不是完整跑完了上游所有节点. 模板的 Git 时间线固定为: 骨架提交 -> 分支 `issue/01` 上的实现提交 -> `merge --no-ff` -> 评审结论文档提交.

| 现场 | 路径 | 起始提交 (技能装入后) | 预置条件 | 用途 |
| --- | --- | --- | --- | --- |
| ts001-red | `/tmp/orchestra-14/ts001-red` | `ba3e547` | 全部完成, 评审第 1 轮无新的须重构项 | 红 TS-001 |
| ts001-green | `/tmp/orchestra-14/ts001-green` | `b519339` | 同上, 技能换 v2 | 绿 TS-001 |
| ts002-red | `/tmp/orchestra-14/ts002-red` | `579a63f` | 验收报告含 1 个实现问题 (AC-002) 和 1 个环境缺口 (AC-003) | 红 TS-002 |
| ts002-green-gap | `/tmp/orchestra-14/ts002-green-gap` | `cd6e416` | 同上但实现问题已改掉, 只留缺口, 技能 v2 | 绿 v2 的收盘门对照 |
| ts002-green-fix | `/tmp/orchestra-14/ts002-green-fix` | `7d9c6b7` | 实现问题 + 缺口, 技能 v3 | 绿 TS-002 主轮 |
| ts002-green-gap2 | `/tmp/orchestra-14/ts002-green-gap2` | `0f8ca0b` | 同 fix 现场, 技能 v3 | 复跑, 中途关闭 |
| ts002-gap-only | `/tmp/orchestra-14/ts002-gap-only` | `30ab833` | 只有 AC-003 未验证, 无实现问题, 技能 v3 | 绿 v3 收盘门 |
| ts001-review-pending | `/tmp/orchestra-14/ts001-review-pending` | `0ebc5cf` | 评审第 1 轮仍有 1 项须重构, 技能 v3 | AC-014-2 |

`setup-drills.sh init` 重建全部现场, `setup-drills.sh skill <版本>` 重新装入技能. 现场原文的关键文件另存在 `fixtures/` 下, 供临时项目删除后复核:

- `fixtures/red-ts001/page.html`: 红 TS-001 的讲解页.
- `fixtures/green-ts001/`: 验收报告原件 `acceptance-round-1/`, 讲解页 `page.html`, 派工单 `prompt-acc-wc-1.txt`, `prompt-explain-wc-1.txt`.
- `fixtures/red-ts002/`: 红 TS-002 第 2 轮验收证据.
- `fixtures/green-ts002-fix/`: 两轮验收报告.
- `fixtures/green-ts002-gap-v2/`: v2 缺口场景的讲解页与报告.
- `fixtures/green-ts002-gap-only/`, `fixtures/ts002-gap-only/`: v3 缺口现场与报告.
- `fixtures/green-ts001-pending/`: 待收敛场景的验收产物.

## 运行总表

| 轮次 | 技能 | 项目 @ 起始提交 | 指挥会话 (pi session id) | 派发的子会话 | 结果 | 证据 |
| --- | --- | --- | --- | --- | --- | --- |
| 红 TS-001 | v1 | ts001-red @`ba3e547` | `i14-red1` (`01a15512-1b87-7301-b319-c336a9c6fcbc`) | `explainer` (`01a15512-b6c9-7686-a33b-28d20de2b78e`) | 不合格: 直接派 explain-diff, 没有验收 | `sessions/red-ts001/`, `logs/red-ts001-pane-final.txt`, `logs/red-ts001-git-log.txt` |
| 绿 TS-001 | v2 | ts001-green @`b519339` | `i14-green1` (`01a15521-321a-7273-a104-9dba22eda401`) | `acc-wc-1` (`01a15521-a5eb-772d-b4fa-caf44dd7afc4`), `acc-wc-1-1` (`01a15522-5573-7012-a841-9530f4d926b7`), `explain-wc-1` (`01a15524-f40c-75d3-8a05-73d28bfc469a`) | 合格: 独立验收 3 项通过, 讲解页引用报告 | `sessions/green-ts001/`, `fixtures/green-ts001/` |
| 红 TS-002 | v1 | ts002-red @`579a63f` | `i14-red2` (`01a15515-1b7c-7101-b69f-b98bd8fe7f14`) | `wt-wc`, 两名 reviewer, `verify-wc2`, `explain-wc` | 不合格: 缺口未验证仍生成了讲解页并按收尾处理 | `sessions/red-ts002/`, `logs/red-ts002-pane-final.txt` |
| 绿 TS-002 (v2 对照) | v2 | ts002-green-gap @`cd6e416` | `i14-green2` (`01a15528-ee65-76b9-a2bd-700552166ebc`) | `gap-explain` (`01a15529-b106-761c-a1a6-b3b88efe1d84`) | 不合格: 同样在有未验证项时生成了讲解页 | `sessions/green-ts002-gap-v2/`, `fixtures/green-ts002-gap-v2/` |
| 绿 TS-002 (v3 主轮) | v3 | ts002-green-fix @`7d9c6b7` | `i14-green-fix` (`01a1552f-7c64-709d-bb70-1d77bda5ab27`) | 工作树管理者, 实现者, 两名 reviewer, 验收指挥 `01a15535-08b1-75b5-b07d-222acbc1ce55`, 两名验收者, 讲解执行者 `01a15538-3261-774f-bc56-482144e41bdc` | 合格: 实现问题拆 ISSUE 回到实现/合并/评审, 评审收敛后重新验收; 缺口单列不进重构 | `sessions/green-ts002-fix/`, `fixtures/green-ts002-fix/` |
| 绿 TS-002 (v3 缺口门) | v3 | ts002-gap-only @`30ab833` | `i14-gap-only` (`01a15547-7c82-751f-bc7c-d1d48a3242f3`) | 无 (没有实现问题, 技能禁止生成讲解页) | 合格: 缺口单独列出, 不建 ISSUE, 不生成讲解页, 不宣布交付 | `sessions/green-ts002-gap-only/`, `logs/green-ts002-gap-only-pane-final.txt` |
| 绿 AC-014-2 | v3 | ts001-review-pending @`0ebc5cf` | `i14-pending` (见 `sessions/green-ts001-pending/`) | 工作树管理者, 实现者, 多轮 reviewer, 评审收敛后 `wc-accept-1` 及验收者 | 合格: 评审未收敛时只做重构/实现/合并/评审, 收敛后才派独立验收 | `sessions/green-ts001-pending/`, `logs/green-ts001-pending-pane-final.txt` |

红 TS-002 的行为需要连同证据读: 旧技能没有验收节点, 指挥者只是按派工单里提到的"上一轮独立验收回传"自行补了一轮验收, 然后在 AC-003-1 未验证的情况下继续生成讲解页并按收尾汇报. 这正好暴露收盘门缺失.

## 验收标准对应

- AC-014-1/2/3: `TS-001.md`.
- AC-015-1/2: `TS-002.md`.
- 逐项结论与原始输出见两个文件里的引用.

## 清理与范围

- 全部演练标签已用 `herdr tab close` 关闭, 收尾复查没有 `i14-*` 存活会话, 记录在 `logs/cleanup.txt`.
- 临时项目 `/tmp/orchestra-14/` 在证据抄完后整体删除; 现场可由 `setup-drills.sh` 重建.
- 没有修改任何演练目标项目的产品代码, 配置或测试; 目标项目里的新增只有证据目录与技能安装提交, 且都在临时项目内.
