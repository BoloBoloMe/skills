## 父级

- `../EXECUTION.md`

## 执行

- [ ] 已实现

## 要构建什么

最终整合与审计: 更新 `README.md` 技能索引, 汇总全部 issue 证据, 逐项核对 BR-009/BR-011/AC-032 与安全策略, 确认五个新技能与 tdd-as-orchestra 集成只落在允许范围, 未修改权威输入, 未同步或部署. 交付后, 一份最终审计报告能把每个 AC/BR/非功能要求指到真实证据, 并给出可直接复核的 frontmatter, 许可, 差异范围, 无 Git 动作与证据边界结论.

## 覆盖依据

- Product: `../PRODUCT.md`, AC-032, BR-009, BR-011
- Technical: `../TECHNICAL.md`, 模块划分末尾的边界, 安全策略, 测试接缝末段 (演练记录边界), 两项复刻的共同交付要求

## 相关决策

- `../DECISIONS.md`: D022, D024, D031, D033, D035, D039

## 允许范围

- 修改 `README.md` 的技能索引表.
- 新建 `docs/changes/verification-skills/evidence/ISSUE-15/` 与最终审计报告 (可放 `evidence/ISSUE-15/AUDIT.md`).
- 只读检查全部技能源, 证据, git 现场, 部署目录是否被改动.

## 禁止范围

- 不新增或修改五个技能的已确认行为; 发现行为缺口回对应 issue 或按停止条件报告.
- 不修改 PRODUCT.md, TECHNICAL.md, DECISIONS.md, ADR, 既有技能.
- 不运行 `sync-to-pi.py`, 不写全局部署, 不提交/推送/开 PR/合并.
- 不以静态文本断言代替已有行为证据.

## 代码定位提示

- 索引: `README.md` 的通用技能与工作流技能表.
- 必读: 五个 `workflow/<skill>/SKILL.md`, `workflow/tdd-as-orchestra/SKILL.md`, `general/writing-for-llm/check_skill.py`, `general/translate-a-skill/SKILL.md`, `docs/changes/verification-skills/evidence/**`, `EXECUTION.md`.
- 现场: `git status --short`, `git diff --stat`, `git diff -- PRODUCT.md TECHNICAL.md`, 部署目录只读检查.

## TDD 切片

本 issue 是非代码审计特例, 不新增运行时行为; 以下为机械审计与证据核对切片.

- TS-001:
  接缝: 五个通用 skill / tdd-as-orchestra -> 交付与既有 Git 职责接口 (TECHNICAL.md 测试接缝 AC-032 行).
  测试用例: TC-032.
  先写的失败测试: `audit-no-git-actions` 在汇总证据前无法确认各 skill 报告没有自动提交/推送/开 PR; 审计脚本/清单对缺失证据应失败.
  最小绿色实现范围: 逐条核对 verify-change 报告, create 生成目录, maintain 修订记录, blast 交接, benchmark 报告, tdd 集成记录均只交付文件/证据, 无自动 Git 动作; 既有本地提交/合并在验收前由实现流程完成.
  不得测试: 不把本变更执行流程自身的本地提交当成 skill 违规.
  覆盖: AC-032.
- TS-002:
  接缝: 五个通用 skill / 生成的项目级 skill -> 用户调用 frontmatter 与公开目录接口 (TECHNICAL.md 测试接缝 BR-009 行).
  测试用例: TC-101.
  先写的失败测试: `audit-frontmatter` 对五个 SKILL.md 与 evidence 中的项目级配方运行 `check_skill.py`; 任一缺失/字段不对应失败.
  最小绿色实现范围: 五个技能零退出; name 与目录一致; description 单行人类摘要; `disable-model-invocation: true` 存在且为 true; 生成的项目配方 frontmatter 有可复核证据.
  不得测试: 用人工判断替代已有机检字段; 不扩写触发词.
  覆盖: BR-009.
- TS-003:
  接缝: 本变更源范围与 tdd-as-orchestra 集成 -> 最终差异/调用关系接口 (TECHNICAL.md 测试接缝 BR-011 行).
  测试用例: TC-103.
  先写的失败测试: `audit-scope` 在未汇总差异前无法证明没有额外上游体系/调度协议/自动评测平台/未授权部署; 清单缺项应失败.
  最小绿色实现范围: 最终差异只在允许范围; PRODUCT.md/TECHNICAL.md 字节不变; 未运行同步/部署; 无新增公共 JSON/平台; README 只加索引行.
  不得测试: 不要求全部历史未跟踪文件干净; 只审计本变更范围.
  覆盖: BR-011.
- TS-004:
  接缝: 安全策略 (写入授权/清理/脱敏/冻结目标).
  测试用例: TC-105.
  先写的失败测试: `audit-security-evidence` 在缺少 ISSUE-10/ISSUE-08 授权与清理记录时失败.
  最小绿色实现范围: 核对批准范围, 未批准写入未发生, 清理残留单列, 报告已脱敏, 冻结目标未被修改, 一次性实验未冒充成品.
  不得测试: 未确认的凭据内容; 不读取或复制秘密.
  覆盖: 安全策略.
- TS-005:
  接缝: 演练记录边界 (TECHNICAL.md 测试接缝末段).
  测试用例: TC-106.
  先写的失败测试: `audit-drill-records` 在任一演练记录未区分待测源文件/宿主/临时项目或无起始提交时失败.
  最小绿色实现范围: 每个记录含源路径与提交, 宿主/pi 版本与加载方式, 临时项目路径与目标提交, 命令/结果/清理; 结论不扩大到全局部署.
  不得测试: 统一记录 JSON; 不测未确认的宿主版本.
  覆盖: 测试接缝末段.

## 验证入口

- `for s in verify-change create-verification-skill maintain-verification-skill blast-radius benchmark-checklist tdd-as-orchestra; do uv run python general/writing-for-llm/check_skill.py workflow/$s/SKILL.md || exit 1; done` (六个均退出 0).
- 全角标点扫描全部新增/修改中文文档无命中.
- `uv run --with pytest python -m pytest general/writing-for-llm/tests -q` 通过; 全量快层记录结果并与开工基线比较.
- `git diff --stat` 与 `git status --short` 证明范围; `git diff -- PRODUCT.md TECHNICAL.md` 为空; 检查 `~/.agents/skills` 与 `~/.pi` 无本轮写入.
- 汇总审计报告存 `docs/changes/verification-skills/evidence/ISSUE-15/AUDIT.md`; 通过标准: 每个 AC/BR/TC 可追溯到证据, 五个技能 frontmatter 合格, 许可与差异记录齐全, 范围与安全审计通过, 未同步/部署.

## 风险提示

- 最终审计容易退化为读摘要; 必须打开原始材料与真实会话记录.
- 未跟踪的既有文件 (ADR, 本变更目录) 与本轮新增要分开, 不把开工前现场当成本轮改动.
- 不要为了让审计通过而修改行为或弱化证据; 发现缺口回对应 issue.

## 停止条件

发现需要改变任一 Spec, 决策或行为, 扩大范围, 触碰禁止范围或证据无法支撑结论时停止并报告.

## 适合 AFK 的原因

审计清单, 通过标准和证据位置已由 Spec 固定; 只做只读核对与 README 索引更新, 无产品/架构决策.

## 验收标准

- [ ] README 索引包含五个新技能.
- [ ] 五个技能通过 `check_skill.py`, frontmatter 与项目级配方证据合格.
- [ ] BR-010 许可/固定 SHA/差异记录齐全.
- [ ] 最终差异只在允许范围, 权威输入字节不变, 未同步/部署.
- [ ] 交付无自动 Git 动作; 安全策略与演练记录边界有证据.

## 被阻塞于

- ISSUE-11, ISSUE-12, ISSUE-13, ISSUE-14.
