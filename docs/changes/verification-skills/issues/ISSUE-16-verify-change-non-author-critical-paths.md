## 父级

- `../EXECUTION.md`

## 执行

- [x] 已实现

## 要构建什么

修正 `workflow/verify-change/SKILL.md`: 首次验收时, 受影响的关键真实路径必须由非作者实跑, 不得只凭作者日志或旧观察放行; 条件仍适用的复用只限于非关键路径. 同时统一视角写法: 执行 agent 是 "你", 需求方是 "我", 不用第三人称 "用户" 混指指挥者.

## 覆盖依据

- 评审发现 (权威): `../evidence/code-review/SPEC.md` 发现 3 (高), `../evidence/code-review/STANDARDS.md` H4 中 verify-change 部分.
- Product: `../PRODUCT.md` 第 32 行与 229-233 行 (作者日志不能单独作为通过依据).
- 相关决策: `../DECISIONS.md` D010, D026, D031.

## 允许范围

- 修改 `workflow/verify-change/SKILL.md` 的相关段落; 必要时补 `reference/*.md` 并在正文引用.
- 新建 `docs/changes/verification-skills/evidence/ISSUE-16/`.

## 禁止范围

- 不改已确认的验收判据、AC 语义或其他技能; 不改 PRODUCT/TECHNICAL/DECISIONS; 不自动提交/推送/合并.

## TDD 切片

- TS-001 接缝: verify-change -> 证据复核与派工接口. 红: 目标版本只有作者原始日志时, 现行技能允许不重跑关键路径; 绿: 关键路径必须非作者实跑, 非关键路径可复用旧观察并注明. 覆盖评审发现 3 与 H4.
  不得测试: 具体措辞; 不测未确认报告格式.

## 验证入口

- `uv run python general/writing-for-llm/check_skill.py workflow/verify-change/SKILL.md` 退出 0; 全角标点扫描自写文件无命中.
- 临时项目真实会话跑红/绿两轮, 记录存 `evidence/ISSUE-16/`.
- 全量快层 `uv run --with pytest python -m pytest -m "not e2e" -q` 不超过 `../evidence/BASELINE.md` 的 6 条既有失败.

## 停止条件

需要改 Spec/决策/行为语义, 或越出允许范围时停止报告.

## 验收标准

- [ ] 关键真实路径首次验收必须非作者实跑, 有红绿演练证据.
- [ ] 视角统一为 "你" 与 "我", 无第三人称指挥者.
