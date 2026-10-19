## 父级

- `../EXECUTION.md`

## 执行

- [x] 已实现

## 要构建什么

修 `workflow/create-verification-skill/SKILL.md` 与 `workflow/maintain-verification-skill/SKILL.md`: 把新出现的 "交用户批准"/"转给用户决定" 改成 "我" 的视角 (需求方是 "我", 执行 agent 是 "你"); 去掉两处逐字重复的批准绑定规则, 共用规则只保留一处并用指针承接, 各自只留资源清单.

## 覆盖依据

- 评审发现 (权威): `../evidence/code-review/STANDARDS-2.md` N1 (硬性) 与 N3 (判断性).

## 允许范围

- 修改上述两个技能正文; 不新建 reference.
- 新建 `docs/changes/verification-skills/evidence/ISSUE-21/`.

## 禁止范围

- 不改批准语义与既有行为; 不改其他技能与权威输入; 不自动提交/推送/合并.

## TDD 切片

- TS-001 接缝: 视角扫描与重复规则. 红: 两份正文出现 "用户" 指需求方, 且批准规则逐字重复; 绿: 视角统一为 你/我, 共用规则只一处且有指针. 覆盖 N1/N3.

## 验证入口

- 两个技能 `check_skill.py` 退出 0; 视角扫描无命中; diff 显示重复段已并入一处.
- 全量快层不超 `../evidence/BASELINE.md` 的 6 条失败.

## 停止条件

需要改批准语义或越出范围时停止报告.

## 验收标准

- [ ] 视角统一, 有扫描证据.
- [ ] 重复规则合并为一处, 有 diff 证据.
