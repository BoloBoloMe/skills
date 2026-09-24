## 父级
- `../EXECUTION.md`
## 执行
- [x] 已实现
## 要构建什么
在 ISSUE-01 骨架上补守门校验, 非法写入被拦截且文件保持原状:
(a) 写 `status` 校验枚举 {待处理, 进行中, 已关闭}, 写 `type` 校验枚举 {research, deliberate, prototype, task}, 非法值报错并列出合法值;
(b) 新增里程碑 `save <file> milestones.<new-id> <json>` 必填 title/type/question, 缺失报错并列出缺失字段名, status 默认 `待处理`, blocked_by 默认 `[]`;
(c) blocked_by 引用的 id 必须已存在且不允许环 (含自环/互环);
(d) 未知顶层字段拒绝写入;
(e) 每次 save 在内存完成写入后对整文档跑完整 schema 校验 (含环检测), 任一失败不落盘, 文件保持原状 (兜底闸门).
结尾: 适合 AFK — 校验规则由 D006/D007 逐条定死, 测试例子在 AC-002/003/004 中给全.
## 覆盖依据
- Product: `docs/changes/navigate-roadmap-json/PRODUCT.md`, AC-002, AC-003, AC-004
- Technical: `docs/changes/navigate-roadmap-json/TECHNICAL.md`, 模块接口 (守门脚本: 不变量与错误模式), 测试接缝
## 相关决策
- `docs/changes/navigate-roadmap-json/DECISIONS.md`: D005, D006, D007, D015
## 允许范围
- `workflow/navigate/scripts/roadmap.py`
- `workflow/navigate/tests/`
## 禁止范围
- 不动 `web_server.py`, `web/`, `SKILL.md`, `TEMPLATES.md`, `pytest.ini`, 其他 skill 目录
- 不改变 ISSUE-01 已定的 CLI 接口与输出契约
- 不新增第三方依赖; 不放宽任何校验规则
## 代码定位提示
- 校验逻辑加在 ISSUE-01 落成的 roadmap.py 内: 快速通道 (字段级, 写前) + 兜底 (整文档, 写后内存复核) 两层
- 测试与 ISSUE-01 的 CLI 测试同风格同目录, 建议独立文件 (如 test_roadmap_validation.py)
## TDD 切片
- TS-001:
  接缝: subprocess 调 CLI + tmp_path.
  测试用例: TC-002.
  先写的失败测试: `test_invalid_enum_rejected` (参数化: status=已做完, type=coding) — 骨架无枚举校验, 写入会成功, 断言拒绝失败.
  最小绿色实现范围: status/type 枚举校验, 错误信息列出合法值, 拒绝时不落盘.
  不得测试: 校验函数内部调用次数.
  覆盖: AC-002.
- TS-002:
  接缝: 同上.
  测试用例: TC-003.
  先写的失败测试: `test_new_milestone_missing_required_field` — 新增里程碑只给 title 与 type, 断言报错列出缺失字段 question 且文件不变; 变体: 缺 title/缺 type; 合法新增断言 status/blocked_by 默认值填充.
  最小绿色实现范围: 新增里程碑必填校验与默认值.
  覆盖: AC-003.
- TS-003:
  接缝: 同上.
  测试用例: TC-004.
  先写的失败测试: `test_blocked_by_invalid_reference` (参数化: 引用不存在 milestone-09 / 自环 milestone-01 / 互环 milestone-02) — 断言拒绝且文件不变.
  最小绿色实现范围: blocked_by 存在性校验 + 环检测 (含自环).
  覆盖: AC-004.
- TS-004:
  接缝: 同上.
  测试用例: TC-104.
  先写的失败测试: `test_unknown_top_level_field_rejected` — save 写顶层未知字段, 断言拒绝.
  最小绿色实现范围: 顶层字段白名单.
  覆盖: AC-004 (错误模式延伸).
- TS-005:
  接缝: 同上.
  测试用例: TC-105.
  先写的失败测试: `test_full_document_validation_rollback` — 构造局部合法但整文档非法的写入 (如对尚不存在的里程碑 save blocked_by, 中间节点创建后整文档缺必填), 断言不落盘, 文件保持原状.
  最小绿色实现范围: 写后整文档 schema 校验 + 失败回滚 (不写临时文件/rename).
  覆盖: AC-004 (D007 兜底).
## 验证入口
- `uv run pytest workflow/navigate/tests/ -q` 全绿 (含 ISSUE-01 既有测试不回归)
## 风险提示
- 环检测须在整文档视图上做 (blocked_by 可间接成环), 不能只查直接引用
- 拒绝路径必须发生在任何落盘动作之前, 否则 "文件不变" 断言会破
## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.
## 适合 AFK 的原因
校验规则, 合法值集合, 测试例子全部先定死, 无待决策项.
## 验收标准
- [ ] AC-002: 非法枚举被拒, 错误列合法值, 文件不变
- [ ] AC-003: 缺必填被拒, 错误列缺失字段名, 合法新增默认值正确
- [ ] AC-004: 引用不存在/自环/互环均被拒, 文件不变
- [ ] 未知顶层字段被拒; 整文档校验失败不落盘
- [ ] `uv run pytest workflow/navigate/tests/ -q` 全绿
## 被阻塞于
- `ISSUE-01-gatekeeper-read-write.md`
