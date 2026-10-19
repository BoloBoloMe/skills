## 父级

- `../EXECUTION.md`

## 执行

- [x] 已实现

## 要构建什么

修正 `workflow/create-verification-skill/SKILL.md` 与 `workflow/maintain-verification-skill/SKILL.md`: 生成或修改配方前, 默认只读, 先说明将要写入的资源/对象/操作/清理与验证办法并等我批准; 运行期临时数据同样受独立授权约束; 批准范围要明确传给它派出的子会话. 另去掉 maintain 与 `reference/drift-classification.md` 的判据重复: 正文或参考文件保留一份判据, 另一处只放混淆例子.

## 覆盖依据

- 评审发现 (权威): `../evidence/code-review/SPEC.md` 发现 1 (高), `../evidence/code-review/STANDARDS.md` J1.
- Technical: `../TECHNICAL.md` 125-126 行 (默认只读与写入前批准).
- 相关决策: `../DECISIONS.md` D010, D031 与账本第 214 行.

## 允许范围

- 修改上述两个技能正文与 `workflow/maintain-verification-skill/reference/drift-classification.md`.
- 新建 `docs/changes/verification-skills/evidence/ISSUE-17/`.

## 禁止范围

- 不改其他技能与权威输入; 不新增统一审计协议; 不自动提交/推送/合并.

## TDD 切片

- TS-001 接缝: 生成与维护 -> 写入授权接口. 红: 未声明写入范围与清理办法即写配方; 绿: 写前说明并等批准, 子会话收到同一范围与授权. 覆盖发现 1.
- TS-002 接缝: maintain 判据单一来源. 红: 同一判据在两处各写一份; 绿: 判据只在一处, 另一处只留例子. 覆盖 J1.

## 验证入口

- 两个技能 `check_skill.py` 均退出 0; 全角标点扫描自写文件无命中.
- 临时项目真实会话跑红/绿, 证据存 `evidence/ISSUE-17/`; 全量快层不超基线 6 条.

## 停止条件

需要改 Spec/决策/行为语义或越出范围时停止报告.

## 验收标准

- [ ] 两个技能写入前都要求说明范围与清理并等批准, 有演练证据.
- [ ] 判据只保留一份, 有 diff 证据.
