## 父级
- `../EXECUTION.md`
## 执行
- [x] 已实现
## 要构建什么
skill 文档改造与审计收口:
1. `workflow/navigate/SKILL.md`: 制图与航行的全部读写动作改述为守门脚本调用 (load/query/save/delete), 加明文禁令 — llm 不得用 read/write/edit 直接触碰 ROADMAP.json (D002); 制图 step 4/5 按 D013 重排: 经脚本写 ROADMAP.json → start 展示服务交付 URL → 用户浏览器确认 → 有异议经脚本修订 → 确认后 git commit (确认动作从落盘前挪到 commit 前, present 退出, ROADMAP.html 取消); 调用模式判断依据改为 ROADMAP.json 存在与否; 注明旧格式 (ROADMAP.md/MILESTONE-NN.md) 出现时由 llm 读旧文件经脚本重建, 不提供迁移命令 (D014); 航行步骤同步改述 (加载索引经 query, 认领改 status, 收口记 artifacts, 关闭写 close_summary, 探明海域改 unknown_seas/milestones).
2. `workflow/navigate/TEMPLATES.md`: 重写为 JSON schema 说明 (字段, 类型, 枚举, 必填, 默认值 — 即 D005/D006), 不再含 markdown 模板.
3. BR-006 审计测试: 静态扫描 `workflow/navigate/scripts/*.py` 的 import 断言仅 stdlib; 扫描 `web/index.html` 断言无外部 http(s) 引用.
结尾: 文档改造适合 AFK — 全部改述规则由决策定死; 最终审阅由用户 (验收含 LLM 可执行性检查).
## 覆盖依据
- Product: `docs/changes/navigate-roadmap-json/PRODUCT.md`, G-001, G-004, NG-001, BR-006
- Technical: `docs/changes/navigate-roadmap-json/TECHNICAL.md`, 模块划分 (skill 文档改造), 测试接缝 (BR-006 -> 静态检查脚本)
## 相关决策
- `docs/changes/navigate-roadmap-json/DECISIONS.md`: D001, D002, D013, D014, D015
## 允许范围
- `workflow/navigate/SKILL.md`, `workflow/navigate/TEMPLATES.md`
- 新增 `workflow/navigate/tests/` 审计测试
## 禁止范围
- 不动 `roadmap.py`, `web_server.py`, `web/index.html` 的行为; 其他 skill 目录 (尤其 present)
- 不新增/改变任何决策内容; 不做迁移命令 (NG-001)
## 代码定位提示
- 现行 SKILL.md 90 行: 制图 step 4 (present 画 ROADMAP.html) 与 step 5 (落盘 md 文件集) 是主要改写对象; 航行步骤 1-7 的文件读写动作逐条对应到脚本操作
- 审计测试参照 `tests/test_old_mechanism_retired.py` 一类的静态断言风格
## TDD 切片
- TS-001:
  接缝: TECHNICAL.md 测试接缝 BR-006 -> 全模块 -> import 清单 -> 静态检查.
  测试用例: TC-102.
  先写的失败测试: `test_stdlib_only_and_no_external_refs` — 解析 scripts/*.py 全部 import 语句断言属 stdlib; 正则扫描 web/index.html 断言无外部 http(s) src/href.
  最小绿色实现范围: 仅测试文件 (前序 issues 均守约则测试直接绿 — 先写测试确认现状, 若红说明前序违约束, 停止并上报).
  不得测试: 文档文字内容.
  覆盖: BR-006.
## 验证入口
- `uv run pytest workflow/navigate/tests/ -q` 全绿 (含 TS-001)
- `grep -n 'ROADMAP.md\|MILESTONE-' workflow/navigate/SKILL.md` — 命中处仅允许出现在旧格式重建/历史说明语境
- 手动走查: 制图 7 步与航行 7 步的动作描述全部指向脚本/服务/URL, 无任何 "直接写 ROADMAP.md/MILESTONE-NN.md" 残留指令
## 风险提示
- SKILL.md 改述遗漏航行节是常见回归 — 两节都要过一遍
- 文档是给 llm 执行的: 措辞须可操作 (命令形态, 判断依据), 不是给人看的散文
## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.
## 适合 AFK 的原因
改述规则, 流程顺序, 禁令措辞均有决策原文可依; 唯一自由度是行文, 验收由用户走查.
## 验收标准
- [x] SKILL.md: 读写全部经脚本, 含 D002 明文禁令; 制图流程符合 D013; 判断依据为 ROADMAP.json; 含 D014 重建约定
- [x] TEMPLATES.md 为 JSON schema 说明, 无 markdown 文件模板
- [x] BR-006: TC-102 静态检查测试在且绿
- [x] grep 与走查通过
## 被阻塞于
- `ISSUE-01-gatekeeper-read-write.md`
- `ISSUE-02-gatekeeper-validation.md`
- `ISSUE-03-web-server-lifecycle.md`
- `ISSUE-04-web-server-endpoints-idle-exit.md`
- `ISSUE-05-spa-cosmos-render.md`
- `ISSUE-06-spa-interaction-edges.md`
