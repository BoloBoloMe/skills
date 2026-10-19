# ISSUE-15 最终整合审计报告

审计对象: 验证 skills 变更 (五个通用 skill + `tdd-as-orchestra` 验收节点接入 + README 技能索引).
被审现场: 工作树 `/home/bolo/Workspace/skills/skills-v2.worktrees/ISSUE-15`, 分支 `issue/15`.
开工基线: `b378e4b` (已含 ISSUE-01 到 ISSUE-14 全部合并); 差异范围基线 `ec9d55f` (见 `../BASELINE.md`).
审计身份: `tdd-as-orchestra` 的执行者, 不是五个技能的作者, 只做只读核对与本 ISSUE 允许的两处写入 (`README.md`, 本目录).

## 1. 审计边界与本轮实际做了什么

只读核对的对象:

- 14 个 ISSUE 的交接报告 (`evidence/ISSUE-01..14/HANDOFF.md`) 与各目录的 `README.md`, `TS-*.md`, `TC-*.md`, `SUMMARY.md`.
- 抽样打开的原始材料: 真实 pi 会话转录, 验收者报告原件, 演练项目 `git log` 原件, 清理记录, 夹具快照, 上游源文副本.
- 五个技能源文件, `tdd-as-orchestra/SKILL.md`, 两个复刻包的 `LICENSE` 与 `reference/PROVENANCE.md`.
- Git 现场: 相对 `ec9d55f` 的最终差异, README 差异, 冻结路径 diff.
- 全局部署目录: `~/.agents/skills`, `~/.pi` 的只读检查.

本轮实际执行的命令与产物都在 `logs/` 与 `red/`, 汇总见第 8 节.

本轮**没有**做的事, 必须写明:

1. 没有重跑 ISSUE-01..14 的真实会话. 各 ISSUE 的临时项目 (`/tmp/orchestra-<NN>`) 在证据抄录后已删, 演练会话已关. 所以"行为通过"的结论继承各 ISSUE 保留的原件与记录, 本轮核对的是**可追溯性与一致性**, 不是第二次行为验收.
2. 没有覆盖其他运行时, 其他模型, 其他宿主, 以及任何全局部署副本的实际生效. 所有结论只覆盖各记录里写明的组合: Ubuntu 26.04.1 LTS x86_64, `pi 1.3.0`, `herdr 0.9.4`, 模型 `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`, 项目内 `.agents/skills/` 副本加 `/skill:<名>` 点名加载.
3. 没有为审计新建评测平台, 结果 JSON 协议或行为断言脚本. 审计清单 `audit_final.py` 只做机械项: frontmatter, 差异范围, 记录字段, 敏感字面量, 部署副本; 行为结论一律引用已有原件.

证据类型标注: `[会话]` 真实 pi 会话原件, `[机检]` 本轮命令输出, `[静态]` 源文或差异对照, `[记录]` 作者交接报告.

## 2. 结论摘要

| 检查项 | 结论 | 主要依据 |
| --- | --- | --- |
| AC-032 交付无自动 Git 动作 (TC-032) | 通过, 附 2 条记录缺口 | 五个 `SKILL.md` 交付边界原文 `[静态]`; 六个角色的演练记录 `[记录]`; `tdd-as-orchestra` 保留本地提交与合并 `[静态]`; ISSUE-09 演练项目 `git log` 原件 `[会话]` |
| BR-009 用户调用 frontmatter (TC-101) | 通过 | 六个技能 `check_skill.py` 退出 0 `[机检]`; 六个生成配方与两个维护后配方同检 `[机检]`; ISSUE-11 加载来源原件 `[会话]` |
| BR-010 许可/固定 SHA/差异记录 | 通过 | 三份 LICENSE sha256 相同 `[机检]`; 复跑 ISSUE-13 机检 `checks=50 failures=0` `[机检]`; 两份 PROVENANCE 差异表 `[静态]`; ISSUE-13 行为保真会话 `[会话]` |
| BR-011 范围只在允许范围 (TC-103) | 通过 | 相对 `ec9d55f` 的 3100 个改动文件全部在允许路径 `[机检]`; 冻结路径 diff 为空; README 只加 5 行; 五个技能无部署副本 |
| 安全策略 (TC-105) | 通过, 附 1 条需用户复核 | ISSUE-10 写入授权/清理/残留/哈希原件 `[会话]`; ISSUE-08 一次性实验边界 `[会话]`; 敏感字面量扫描 0 命中 `[机检]` |
| 演练记录边界 (TC-106) | 通过, 附 1 条记录缺口 | 14 个 ISSUE 的 required 字段全在 `[机检]`; ISSUE-06 缺提交渠道记录 |
| README 索引含五个新技能 | 通过 | `README.md` 差异只有 5 条新增行 `[机检]` |

自动审计清单结果: `red/red-audit-run1.log` 退出 1 (README 索引未加, 1 条措辞过严导致的假失败), 修好后 `green-audit-run2.log` 退出 0, `WARN 3` 写入第 9 节.

## 3. AC-032: 交付只交文件与证据, 不自动做 Git 动作 (TC-032)

### AC-032-1 角色与交付物

五个技能正文里的交付边界原文 `[静态]`:

| 技能 | 原文位置 | 原文 |
| --- | --- | --- |
| verify-change | `workflow/verify-change/SKILL.md` 边界节 | 不提交, 不推送, 不开 PR, 不合并 |
| create-verification-skill | `workflow/create-verification-skill/SKILL.md` 交付节 | 只交文件路径, 差异和证据; 不提交, 不推送, 不开 PR |
| maintain-verification-skill | `workflow/maintain-verification-skill/SKILL.md` 末句 | 不自动提交, 推送, 开 PR 或合并 |
| blast-radius | `workflow/blast-radius/SKILL.md` 交接节 | 只交接材料, 不自动合并, 不创建 PR |
| benchmark-checklist | `workflow/benchmark-checklist/SKILL.md` 对外报告节 | 这份清单只产出草稿与判定: 提交, 推送, 开 PR 与合并都由使用者按自己的流程做 |

五个技能正文里没有 `git push`, `git commit`, `gh pr create`, `git merge` 这类写动作命令; 只读命令 (如 `git log`, `git show`, `git blame`, `gh pr view`) 保留. `blast-radius` 的 `gh pr view` 只读 PR 正文, 不算发布动作.

真实执行记录 `[会话]`:

- 验收指挥者 (verify-change): ISSUE-01 `drill-G1a2-evidence-dir/REPORT.md` 首段绑目标提交 `612f1ea...` 并写"除证据目录输出外, 源码与 Spec 未变"; ISSUE-03 `drill-G7-blocked/REPORT.md` 首行"结论: 受阻, 未完成验收", 6 项全部未验证, 没有自建提交或发布; ISSUE-05 `drill-green-010-stale/r1-20261019-04a8dd6/VERIFICATION-REPORT.md` 有"操作缺口 (不产生判据)"节; ISSUE-10 `drill-green-011-012/report.md` 写入与清理记录节末写"未提交, 未推送".
- 配方生成者 (create-verification-skill): ISSUE-11 生成物是项目内 `.agents/skills/verify-fixture/`, 报告给出目录, 差异与实跑证明, 没有提交或推送项目.
- 配方维护者 (maintain-verification-skill): ISSUE-12 `drill-b-green/maintain-report.md` 首段绑起始提交 `456c360`, 结论写范围内修正与缺口, 未自动提交项目.
- 调查者 (blast-radius): ISSUE-07 交接报告只给五部分材料; ISSUE-13 `TS-002-drill.md` 记录会话只写仓库外 `/tmp` 脚本.
- 性能检查者 (benchmark-checklist): ISSUE-09 `green-ts002/docs/green2-pr.md` 是**文件草稿**, 原件记录"演练项目 `git log` 顶端仍为编排者提交 `6052846`, `git status --short` 只有两个未跟踪的 `docs/green2*.md`". 这一条是"准备 PR 正文不等于自动开 PR"的直接证据.
- 本变更自身的提交与合并: 由实现流程按 `tdd-as-orchestra` 既有职责完成 (ISSUE 分支提交, 合并节点 `git merge --no-ff`, 见 `evidence/ORCHESTRATION.md` 的波次记录), 不属于技能违规.

### AC-032-2 两项复刻不附带自动发布

`blast-radius` 与 `benchmark-checklist` 的对外材料规则都是"只给草稿与判定, 发布由使用者做". ISSUE-09 实测: PR 草稿存在, 远端不存在, 项目顶端提交不是会话产生的. ISSUE-13 的行为保真演练同样只在临时项目 `.agents/skills/` 里安装技能副本, 没有向任何远端发布.

### AC-032-3 既有本地提交与合并在验收前完成

ISSUE-14 的原件 `logs/green-ts002-fix-git-log.txt` `[会话]` 显示真实顺序: `3dbba65 docs: 新增 ISSUE-02 (验收回传 ...)` -> `0a7166f feat: ISSUE-02: 修复 ...` -> `9e578b2 merge: 合并 issue/02` -> `89ea49e docs: 记录评审第 2 轮结论` -> `3c79985 docs: 归档第 2 轮独立验收报告与原始证据`. 即实现/合并/评审在前, 验收报告归档在后, 与 AC-032-3 一致.

机械检查: `audit-no-git-actions` 对五个技能与 `tdd-as-orchestra` 全部通过; 角色记录覆盖 verify-change 4/6, benchmark-checklist 2/4, 其余满覆盖, 缺口见第 9 节第 3 条.

## 4. BR-009: 用户调用 frontmatter 与项目级配方 (TC-101)

六个技能的 `check_skill.py` 逐个退出 0 `[机检]` (`logs/check-skill-six.log`):

```
workflow/verify-change/SKILL.md: OK
workflow/create-verification-skill/SKILL.md: OK
workflow/maintain-verification-skill/SKILL.md: OK
workflow/blast-radius/SKILL.md: OK
workflow/benchmark-checklist/SKILL.md: OK
workflow/tdd-as-orchestra/SKILL.md: OK
```

字段事实 `[静态]`: 六个文件的 `name` 与目录名一致; `description` 都是单行人类摘要 (描述"做什么", 不是"何时触发"的触发词清单); 六个都有 `disable-model-invocation: true`. `benchmark-checklist` 的 description 较长, 但仍是单行摘要, 列的是覆盖范围而不是触发语.

项目级配方 frontmatter (BR-009 后半段) `[机检]`: 把 ISSUE-11 的 6 份生成物与 ISSUE-12 两个 `final-recipe/SKILL.md` 分别按 `name` 落到临时目录后跑 `check_skill.py`, 全部退出 0. 例: `evidence/ISSUE-11/generated/TS-001-p1-verify-fixture-SKILL.md` -> `name: verify-fixture`, `disable-model-invocation: true`; `evidence/ISSUE-12/drill-a-green/final-recipe/SKILL.md` -> `name: verify-notes`.

配方的"真实加载入口"证据 `[会话]`: ISSUE-11 `raw/TS-002-017-verifier-transcript-i11-ver1.txt` 首条展开块原文

```
<skill name="verify-fixture" location="/tmp/orchestra-11/p2-gaps/.agents/skills/verify-fixture/SKILL.md">
References are relative to /tmp/orchestra-11/p2-gaps/.agents/skills/verify-fixture.
```

即加载来源是项目当前文件, 不是全局副本; 同一文件还记录全局替身 sha256 全程未变, 且 `/home/bolo/.agents/skills/verify-fixture` 不存在.

## 5. BR-010: 许可, 固定来源与逐项差异记录

来源固定 `[静态]`: 两个复刻以 `cursor/plugins` 的 `4382e687a50b8d2c5ce4d141d001186589cff8d5` 为固定来源, 不追浮动 main. 两份 `reference/PROVENANCE.md` 各命中该 SHA 3 次, 差异表字段固定为源版位置, 目标版位置, 影响, 处理决定 (blast-radius 15 行, benchmark-checklist 16 行).

许可随副本 `[机检]` (`logs/br010-provenance.log`):

```
bc957ca6bee02792566a1a028d105e02e247c6e77cf057061674273da77b200e  workflow/blast-radius/LICENSE
bc957ca6bee02792566a1a028d105e02e247c6e77cf057061674273da77b200e  workflow/benchmark-checklist/LICENSE
bc957ca6bee02792566a1a028d105e02e247c6e77cf057061674273da77b200e  evidence/ISSUE-13/upstream/pstack-LICENSE.txt
```

复跑 ISSUE-13 的机检脚本 (只读): `checks=50 failures=0`, 退出 0, 输出 `OK 两个复刻包的许可, 固定来源与逐项差异记录可读`. 该脚本核对完整 MIT 段落 (版权行, 授权段, 随附条件段, 全大写免责段), 固定 SHA, 差异表四列, 以及 translate-a-skill 第 7 节校验命令是否记在包内.

行为保真 `[会话]`: ISSUE-13 `TS-002-drill.md` 用两个临时项目的真实会话各跑一个代表场景 (`br13-g1`, `bm13-g1`), 会话转录记录加载来源; 对照口径就是两份差异表. 汉化正文全角标点与残留英文的结果记在 `ISSUE-13/machine-checks.log` 第 4 到 6 节.

## 6. BR-011: 最终差异范围与调用关系 (TC-103)

差异统计 `[机检]` (`logs/scope-git.log`), 相对 `ec9d55f`:

| 路径前缀 | 改动文件数 |
| --- | --- |
| `docs/changes/verification-skills/evidence` | 3073 |
| `docs/changes/verification-skills/issues` | 14 |
| `workflow/blast-radius` | 5 |
| `workflow/benchmark-checklist` | 3 |
| `workflow/maintain-verification-skill` | 2 |
| `workflow/verify-change` | 1 |
| `workflow/create-verification-skill` | 1 |
| `workflow/tdd-as-orchestra` | 1 (`SKILL.md`) |
| `README.md` | 1 (本 ISSUE 新增 5 行索引) |

冻结路径: `git diff --name-only ec9d55f..HEAD -- docs/changes/verification-skills/{PRODUCT,TECHNICAL,DECISIONS}.md docs/adr general tests pi sync-to-pi.py` 输出为空, 即权威输入与既有技能, 测试, pi 配置, 同步脚本字节不变 `[机检]`.

README: 差异只有新增行, 没有删除或改写行; 新增内容就是五个技能的索引行, 没有别的 `[机检]`.

部署与同步 `[机检]` (`logs/deployment-readonly-check.log`): `~/.agents/skills/{verify-change,create-verification-skill,maintain-verification-skill,blast-radius,benchmark-checklist}` 与 `~/.pi/skills/*` 全部 `absent`; `~/.agents/skills` 仍是开工前的 34 个条目; `~/.pi` 下只有 `agent`. 即本轮没有运行 `sync-to-pi.py`, 没有部署副本.

没有新增平台或协议 `[机检]`: 最终差异里没有 `platform/`, `runner/`, `harness/`, `schema/`, `protocol/`, `result_protocol`, `evaluation_platform` 一类路径; 新增的 `.py` 只有本目录的只读审计清单与各 ISSUE 的任务专用夹具/证据整理脚本 (都在 `evidence/` 内).

`tdd-as-orchestra` 的调用关系 `[静态]`: 只改 `SKILL.md`, 新增验收节点与验收回传, 保留原有 EXECUTION/TDD 输入, 工作树, 本地提交, 合并与完整测试职责. 没有把 verify-change 内联进实现指挥者, 也没有多夹一层无职责会话.

## 7. 安全策略 (TC-105)

写入授权 `[会话]` (`evidence/ISSUE-10/drill-green-011-012/plan.md` 原文):

```
## 写入授权 (用户已批准, 原样交给验收者)
- 资源: 测试实例 runtime/data.
- 对象: 临时账号 tmp-verify-01 及其一条备注记录 (note id n1); 允许在同一账号上重复写入该备注.
- 操作: README 记录的 account-ensure / note-put (同一命令可重复).
- 清理: 已批准, 但必须走 README 记录的 account-delete 入口; 管理员令牌未提供. 禁止直接改 runtime/data 里的数据文件或用其他方式绕过.
- 未批准: 修改 config/shared.json.
```

写入与清理 `[会话]` (`evidence/ISSUE-10/drill-green-011-012/report.md`): 逐条记录对象, 命令, 时间, 结果; 同范围重复写入没有再要批准; `account-delete` 返回 `rc=2 (missing --admin-token)`, 残留写成独立小节"残留对象 (清理未完成, 单列)", 明确"残留只记为清理未完成, 不当作整项通过, 也不写成产品功能失败"; 未批准对象 `config/shared.json` 结束 sha256 与前提一致; 未执行直接改数据文件或起服务桩.

一次性实验与冻结目标 `[会话]` (`evidence/ISSUE-08/green-ts003/docs/green3.md` 与 `TS-003.md`): 实验标非正式 TC, 只动独立脚本与临时数据, 内部结果不冒充成品通过; 需要给冻结目标加计数时按停止条件报缺口, 没有取得新写入权限.

脱敏 `[机检]`: 扫描 `evidence/` 下 `.md`, `.txt`, `.log`, `.jsonl`, `.py`, `.sh`, `.diff` 中的四类凭据字面量 (`sk-`, `ghp_`, `AKIA`, 长 Bearer 串), 命中 0; ISSUE-14 里有 54 处 `Authorization: Bearer $AUDIT_TOKEN` 或 `Bearer <token>` 形态的占位符, 已按占位符排除并人工确认不含凭据正文.

需用户复核 (来自 ISSUE-10 记录, 不是本轮新判断): 指挥者把"按 README 建立 `runtime/data` 实例"解释为"建立已批准的测试实例"的一部分. 该步骤超出字面对象清单 (临时账号 + 一条备注). 若用户认为 init 不在批准范围内, 依赖该实例的 AC-001-1/AC-003-1/AC-004-1/AC-005-1 结论作废, 只保留不依赖它的缺口结论.

## 8. 演练记录边界 (TC-106)

required 字段 (源路径, 源版本, 宿主与 pi 版本, 加载方式, 临时项目, 结论边界) 在 14 个 ISSUE 的顶层记录里全部命中 `[机检]`. 抽查原件确认字段不是套话:

- ISSUE-07 `TS-001-drill.md` 首段: 待测源路径, sha256 前 16 位 `a0d09c481e1884a8`, 宿主 `pi 1.3.0`, `herdr 0.9.4`, 加载方式 `pi -a` 加 `/skill:blast-radius`, 临时项目 `/tmp/orchestra-07/drill-ts001-*`, 起始提交 `04ddf93`.
- ISSUE-13 `TS-002-drill.md`: 两个技能 `SKILL.md` 的 sha256, 三个临时项目与起始提交 (`bb5902c`, `e248487`, `a94b619`), 四个会话名, 提交渠道 `herdr pane send-text` 加 `herdr agent send-keys "alt+\\"`.
- ISSUE-12 `drill-b-green/maintain-report.md`: 项目路径, 起始提交 `456c360`, 配方目录, 产品判据路径, 配方原始副本位置.
- ISSUE-10 `README.md`: 待测源文件与两个版本 md5, 宿主明细, 加载来源抽取方式, 5 个夹具的起始提交, 会话与 `pi session id` 表, 清理记录位置.

边界表述: 各 ISSUE 都写了"结论只覆盖所记录组合". 多数用"未写全局部署副本/不覆盖全局部署"的写法; ISSUE-07 用的是"只在单一宿主与 pi 1.3.0 + herdr 0.9.4 上做过; 其他运行时的点名加载与多模型开法未验证" `[记录]`, 属同一含义的不同措辞, 按实质判定为满足, 不是弱化要求.

没有把源码演练结论扩大为部署生效: 第 6 节的部署目录检查独立证明五个技能没有任何部署副本; `evidence/ORCHESTRATION.md` 也没有任何部署或同步记录.

## 9. 缺口, 风险与未验证 (如实列出)

1. **未重跑行为** (最大限制): 14 个 ISSUE 的临时项目已删, 会话已关. 本轮只核对了原件, 记录与机械项, 没有第二次行为验收. 任何"通过"结论的强度不超过各 ISSUE 自己的证据强度.
2. **ISSUE-06 缺提交渠道记录**: 其 `README.md` 与 `HANDOFF.md` 记录了宿主, 加载方式, 临时项目, 起始提交, 会话名与清理, 但没有写文本是怎么提交给会话的 (`send-text`/`send-keys`). 这是 TECHNICAL 证据固定记录里的字段缺口; 结论本身不受影响 (会话输出原件在 `sessions/`).
3. **四份顶层记录缺一句无自动 Git 动作说明**: ISSUE-04 与 ISSUE-10 (verify-change), ISSUE-06 与 ISSUE-08 (benchmark-checklist) 的 `HANDOFF.md`/`README.md` 没有写这一句. 同一技能的其他 ISSUE 写了 (verify-change: 01/02/03/05; benchmark-checklist: 09/13), 且技能正文边界原文与本变更自身的提交流程都可核对, 所以 AC-032 判定通过; 但记录一致性不齐.
4. **引用路径漂移** (抽样 296 条 HANDOFF 路径引用): 242 条按声明路径直接可开, 36 条需按 ISSUE 目录补齐轮次子目录 (HANDOFF 省略了中间层), 3 条同名多候选 (`recipe-diff.patch` 在三个 drill 目录各有一份). 另有 3 处确认的真实漂移: ISSUE-07 引用的 `workflow/blast-radius/reference/source-record.md` 已被 ISSUE-13 改名为 `reference/PROVENANCE.md`; `ts003-wide-raw/report.md` 与 `merge.md` 实际文件名是 `ts003-wide-report.md` 与 `ts003-wide-merge.md`. 材料本身都在, 属记录精度问题. ISSUE-05 的 3 条 `REPORT.md` 引用是轮次子目录里的同名文件 (各 drill 目录内唯一). 其余未解析项是 `/tmp` 临时项目名或 drill 目录别名. 明细 `logs/handoff-path-sample.log` 与 `logs/handoff-path-sample-suffix.log`.
5. **`/skill:` 点名入口未验证项**: ISSUE-10 的两项方法由验收者用 `read` 读取项目内 `SKILL.md` 后执行, ISSUE-14 的验收指挥会话按项目内 `SKILL.md` 步骤执行, 都不是 `/skill:` 点名加载. 方法内容与证据级别按当前文件执行, 但点名入口下的行为没有证明.
6. **样本与宿主**: 每个场景基本一次运行, 单一模型 (`cli/deepseek-v4.1-flash-expires-on-0910`), 单一 pi 与 herdr 版本. ISSUE-13 的多模型同题调查没有做 (按影响面判窄走单路, 并写明 `llm-select` 里只有当前这款有评分). ISSUE-07 的"只有一款模型"分支是受控材料, 不是真实能力缺失.
7. **受控材料**: ISSUE-06, 08, 09 的性能数字来自 `time.sleep` 与小型字典模拟, 只证明方法与判定流程, 不代表真实产品性能; ISSUE-05 的 AC-003 成功分支需要真实部署方 relay, 未覆盖.
8. **`check_skill.py` 机检缺口** (ISSUE-01 事故记录): 该脚本在 `disable-model-invocation: true` 时放行 description 里"冒号+空格", 而 pi 的 YAML 解析会整份丢弃技能. 五个技能当前写法都能被 pi 接受 (ISSUE-11 的 v3 复跑验证过), 但脚本仍不拦这种写法; 修脚本属 `general/` 范围, 本 ISSUE 禁止改动, 只记录.
9. **记录里的自我纠正项**: ISSUE-14 的 `green-ts002-fix` 轮因为派工单预授权继续收尾而出了讲解页, 该轮不作为收盘门证据, 收盘门由 `ts002-gap-only` 单独证明. ISSUE-02 的两条对照 (冲突检测, 带原件旧观察) 在旧版也能通过, 没有红轮对照. ISSUE-06 与 ISSUE-08 的红轮没有全部跑红. 这些是证据强度差异, 不是行为缺口.
10. **未验证部署生效**: 本轮没有运行同步, 五个技能不在 `~/.agents/skills`. 后续部署与部署后验证不在本 ISSUE 范围, 也不能用本报告冒充.

## 10. 机械检查与复核命令

| 命令 | 退出码 | 结果 | 日志 |
| --- | --- | --- | --- |
| `uv run python docs/changes/verification-skills/evidence/ISSUE-15/audit_final.py` (红, 未加 README 索引) | 1 | 2 FAIL, 3 WARN | `red/red-audit-run1.log` |
| 同上 (绿) | 0 | 五项 required 全通过 | `green-audit-run2.log` |
| 六个技能 `check_skill.py` 循环 | 0 | 六行 OK | `logs/check-skill-six.log` |
| 全角标点扫描 (README.md 与本目录全部 md/py/log) | 0 命中 | `TOTAL_HITS 0` | `logs/fullwidth-scan.log` |
| `uv run python .../ISSUE-13/check-provenance-artifacts.py` | 0 | `checks=50 failures=0` | `logs/br010-provenance.log` |
| `uv run --with pytest python -m pytest general/writing-for-llm/tests -q` | 0 | `7 passed, 18 subtests passed` | `logs/pytest-writing-for-llm.log` |
| `uv run --with pytest python -m pytest -m "not e2e" -q` | 1 | `6 failed, 659 passed, 2 skipped, 103 deselected, 33 subtests passed in 274.02s`, 失败集合与 `../BASELINE.md` 的 6 条逐条一致 | `logs/pytest-full-not-e2e.log` |
| `git diff`/`git status` 范围与 README 差异 | 0 | 见第 6 节 | `logs/scope-git.log` |
| 部署目录只读检查 | 0 | 五个技能全部 absent | `logs/deployment-readonly-check.log` |
| HANDOFF 路径引用抽样 | 0 | 296 / 242 直接可解析 | `logs/handoff-path-sample.log` |

全量快层: `logs/pytest-full-not-e2e.log` 末尾为 `6 failed, 659 passed, 2 skipped, 103 deselected, 33 subtests passed in 274.02s`. 6 条失败分别对 `general/present/tests/test_browser_session.py` 的 5 条与 `tests/test_mailbox_admin.py::test_pending_cap_drops_oldest`, 与 `../BASELINE.md` 的既有失败集合逐条一致, 没有新增失败. 这些失败都是 socket 超时, 与本变更新增路径无关.

## 11. 全量证据索引 (AC/BR -> ISSUE -> 证据)

`evidence/ISSUE-<NN>/` 目录与主要原件. 本轮核对 = 打开了该目录的顶层记录与抽样原件.

| 标准 | ISSUE | 主要原件 (本轮打开或核对位置) |
| --- | --- | --- |
| AC-001 缺 PRODUCT 停止, 判据只取产品标准 | 01 | `drill-G1b2-green-missing-product.log`, `drill-G1a2-evidence-dir/REPORT.md` |
| AC-002 必验清单全量覆盖, 静态与运行分开 | 02 | `evidence-G1/REPORT.md`, `evidence-R1/`, `setup-drills.sh` |
| AC-003 证据类型与摘要不冒充原件 | 02 | `evidence-G2/report.md`, `evidence-G3/report.md`, `evidence-G4/report-7f360da-r1.md` |
| AC-004 非作者委派, 无可用非作者受阻 | 03 | `drill-G1-non-author/`, `drill-G7-blocked/REPORT.md`, `SUMMARY.md` |
| AC-005 场景组派工与人数依据 | 03 | `drill-G2..G6/PLAN.md`, `drill-R2-plan-red/`, `drill-G4-three-groups-2avail/dispatch-time.txt` |
| AC-006 并行与原始证据共享 | 04 | `drill-green-parallel/evidence-e398c7c-r1/report.md`, `runtime-shared/events.log`, `drill-green-parallel-run1/` |
| AC-007 修复后复验 | 04 | `drill-reverify-round1..3/VERIFY-REPORT.md`, `drill-reverify-author-materials/` |
| AC-008 目标提交与证据目录 | 01 | `drill-G2a2-green-dirty-stop.log`, `drill-G2c2-evidence-outside/v-2e868d1/REPORT.md` |
| AC-009 旧证据适用性 | 05 | `drill-green-009-r1/board-d2e680c-r1/REPORT.md`, `drill-green-009-r2/board-verify-65b43e1/REPORT.md`, `drill-green-009-r3/REPORT.md` |
| AC-010 配方选择与过时配方 | 05 | `drill-green-010-norecipe/r1-d1f656e-.../90-report.md`, `drill-green-010-stale/r1-20261019-04a8dd6/VERIFICATION-REPORT.md` |
| AC-011 写入授权与清理 | 10 | `drill-green-011-012/plan.md`, `report.md`, `verifier-1/state.log`, `logs/cleanup.txt` |
| AC-012 问题与缺口分类 | 10 | `drill-green-011-012/report.md` 三类去向节, `drill-red-011-012-r2/REPORT.md` |
| AC-013 条件调用两项方法 | 10 | `drill-green-013/00-plan.md`, `V1-perf/REPORT.md`, `V2-del/REPORT.md`, `logs/loaded-locations.txt` |
| AC-014 独立验收节点 | 14 | `fixtures/green-ts001/acceptance-round-1/report.md`, `sessions/green-ts001/`, `logs/green-ts001-pane-final.txt` |
| AC-015 验收发现回重构与缺口出口 | 14 | `fixtures/green-ts002-fix/REPORT-round-2.md`, `logs/green-ts002-fix-git-log.txt`, `sessions/green-ts002-gap-only/` |
| AC-016 配方生成范围与缺 Product | 11 | `TC-016.md`, `generated/TS-001-p1-verify-fixture-SKILL.md`, `raw/TS-001-draft-product-transcript-i11-gen6.txt` |
| AC-017 新会话实跑与按名加载 | 11 | `TC-017.md`, `raw/TS-002-017-verifier-transcript-i11-ver1.txt`, `raw/verifier-evidence/ver1-p2-.../` |
| AC-018 生成物范围与构建受阻 | 11 | `TC-018.md`, `generated/TS-003-green-p3-verify-fixture-SKILL.md`, `raw/verifier-evidence/ver4-p3-.../` |
| AC-019 维护范围与漂移分类 | 12 | `drill-a-green/maintain-report.md`, `recipe-diff.patch`, `drill-c-no-product/maintain-report.md` |
| AC-020 修订后新会话复跑 | 12 | `drill-b-green/maintain-report.md`, `recipe-evidence/*.log`, `sessions/drill-b-verifier-subsession.jsonl` |
| AC-021 关键安全事实与证据级别 | 07 | `TS-001-drill.md`, `ts001-raw/green/report.md`, `proof_parse.py`, `proof_read.py` |
| AC-022 风险与已排除项交接 | 07 | `ts002-raw/report.md`, `ts003-gap-raw/report.md` |
| AC-023 多模型同题与单路/缺口分支 | 07 | `ts003-wide-raw/ts003-wide-report.md`, `ts003-wide-merge.md`, `ts003-local-raw/report.md`, `ts003-gap-raw/report.md` |
| AC-024 一次性实验边界 | 08 | `TS-003.md`, `green-ts003/docs/green3.md`, `green-ts003/bench/oneoff_authz.py` |
| AC-025 测量前主张与工具检查 | 06 | `TS-001.md`, `sessions/roundA-red.log`, `sessions/roundB-AC025.log` |
| AC-026 公平调优与重复统计 | 06 | `TS-002.md`, `sessions/roundD-task1..4.log` |
| AC-027 错误计数与工作发生 | 06 | `TS-003.md`, `sessions/roundE2-task2.log`, `sessions/roundF-task1..3.log` |
| AC-028 粗估与选型边界 | 09 | `TS-001.md`, `green-ts001/docs/green1.md` |
| AC-029 结论与 PR 主数字 | 09 | `TS-002.md`, `green-ts002/docs/green2.md`, `green-ts002/docs/green2-pr.md` |
| AC-030 占比上限与端到端 | 08 | `TS-001.md`, `green-ts001/docs/green1.md`, `green-ts001/docs/raw/task*.log` |
| AC-031 基线与脚本固定前检查 | 08 | `TS-002.md`, `green-ts002/docs/green2.md`, `green-ts002/bench/team-entry.diff` |
| AC-032 交付无 Git 动作 | 15 | 本报告第 3 节; 各 ISSUE 记录与 `logs/green-ts002-fix-git-log.txt` |
| BR-009 (审计) | 15 | 第 4 节; `logs/check-skill-six.log`; ISSUE-11 `TC-017.md` |
| BR-010 (审计) 静态 | 13 | `TS-001.md`, 三份 LICENSE, 两份 `reference/PROVENANCE.md` |
| BR-010 翻译保真 | 13 | `TS-002-drill.md`, `sessions/`, `red-round/`, `drill-artifacts/` |
| BR-011 (审计) | 15 | 第 6 节; `logs/scope-git.log`, `logs/deployment-readonly-check.log` |
| 加载来源与同名冲突/未加载 (TC-104) | 11 | `TC-104.md`, `raw/TC-104-ver2-startup-diagnostics.txt`, `raw/TC-104-ver2-collision-notloaded-pane.txt` |
| 安全策略 (TC-105) | 15 | 第 7 节; ISSUE-10 与 ISSUE-08 原件 |
| 演练记录边界 (TC-106) | 15 | 第 8 节; 14 个 ISSUE 的顶层记录 |
| 自足历史定位与中文交接 (TC-107) | 07 | `TS-003-drill.md` 末节与三份演练记录 |
| 翻译行为保真 (TC-108) | 13 | `TS-002-drill.md` |

## 12. 判定

- 五个技能与 `tdd-as-orchestra` 集成落在允许范围; 权威输入字节不变; 没有同步或部署; 没有新增评测平台或结果协议; README 索引补齐.
- 五个技能 frontmatter 合格, 项目级配方的 frontmatter 与加载来源有可复核证据.
- 许可, 固定 SHA 与逐项差异记录齐全, 行为保真演练有会话原件.
- 交付不带自动 Git 动作; 既有本地提交与合并仍由实现流程在验收前完成.
- 安全策略与演练记录边界有证据, 残留与未验证项保持可见.

本报告的通过结论是**代理审计结论**, 不关闭正式人工验收. 第 9 节的 10 条缺口仍然有效, 其中第 2, 3, 4 条是记录层面的缺口, 第 1, 5, 6, 7, 10 条是覆盖与样本边界, 第 8, 9 条是已知工具或证据强度限制.
