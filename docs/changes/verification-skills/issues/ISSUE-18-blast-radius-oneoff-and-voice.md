## 父级

- `../EXECUTION.md`

## 执行

- [ ] 已实现

## 要构建什么

修正 `workflow/blast-radius/SKILL.md`: 承接一次性实验边界 (实验明确标为非正式 TC, 内部证明不能顶替成品入口, 需要新正式接缝时停止交回, 配置受保护与清理); 并统一视角 (执行 agent 是 "你", 需求方是 "我"), 拆开超长句与被动句.

## 覆盖依据

- 评审发现 (权威): `../evidence/code-review/SPEC.md` 发现 2 (高), `../evidence/code-review/STANDARDS.md` H3 与 H4 中 blast-radius 部分.
- Product: `../PRODUCT.md` 551-577 行 (一次性实验边界).
- 相关决策: `../DECISIONS.md` D021, D024, D037.

## 允许范围

- 修改 `workflow/blast-radius/SKILL.md` 与必要 `reference/*.md`.
- 新建 `docs/changes/verification-skills/evidence/ISSUE-18/`.

## 禁止范围

- 不改 benchmark-checklist 的既有内容 (只在需要时给调用指针); 不改权威输入; 不自动提交/推送/合并.

## TDD 切片

- TS-001 接缝: blast-radius -> 一次性实验与成品证据接口. 红: 内部实验可冒充成品证据且无停止规则; 绿: 非正式标记, 配置保护, 清理, 需新接缝时停止交回, 均有可观察行为. 覆盖发现 2.
- TS-002 接缝: 正文视角与句子结构. 红: 出现第三人称视角与超长句; 绿: 全篇 "你/我" 视角, 句子短且主动. 覆盖 H3/H4.

## 验证入口

- `check_skill.py` 退出 0; 全角标点扫描无命中; 视角扫描: 正文不再出现把执行 agent 写成 "我" 或把需求方写成 "用户" 的句子.
- 临时项目真实会话跑红/绿, 证据存 `evidence/ISSUE-18/`; 全量快层不超基线 6 条.

## 停止条件

需要改 Spec/决策/行为语义或越出范围时停止报告.

## 验收标准

- [ ] 一次性实验边界可观察, 有演练证据.
- [ ] 视角与长句问题已修正, 有扫描证据.
