# milestone-09 执行输入准备记录

本里程碑是 HITL 准备工作: 为 milestone-04 (AFK 编码任务) 准备 drive-execution 所需的权威输入, 并与仓库主人确认验收标准. 本记录不表示编码已开始, 也不构成 milestone-08 的验收结论.

## 结论

milestone-04 已具备按 `drive-execution` 正常进入派工的全部输入:

- `../milestone-04/PRODUCT.md`: 产品说明, 含 G-001..G-012, NG-001..NG-004, BR-001..BR-006 与 22 条 Gherkin 验收标准 (AC-001..AC-022). 已在 chat 中经仓库主人明确采纳, 转正标记 `<!-- confirmed-flow: v1 -->`, 审阅版本 `5aedcd4d6637d2e122a0eaf7ee20e2ca8775f942b2d157d58565cc71d56c3e17`.
- `../milestone-04/TECHNICAL.md`: 技术说明, 六节齐全, `check-tech.py` 通过.
- `../milestone-04/EXECUTION.md`: 全局允许/禁止范围, 完成定义, 验证策略, 任务图, 覆盖矩阵 (AC-001..AC-022 与 BR/非功能要求/模块接口不变量逐条给验证入口), 评审起点另行填入完整提交号.
- `../milestone-04/issues/ISSUE-01` 至 `ISSUE-06`: 六个垂直切片, 含验证契约, 验证入口与交付证据栏; 依赖为 ISSUE-02 -> ISSUE-03, ISSUE-01 -> ISSUE-04, 前四者 -> ISSUE-06, ISSUE-05 独立.

## 确认与检查过程

1. 领域与决策来源: `../milestone-01/DECISIONS.md` (D004-D007, D013) 与 `../milestone-03/DECISIONS.md` (D001-D019). 两份账本都是已确认决策, 本里程碑不新增决策内容.
2. 验收标准起草: 由独立子代理按 `workflow/to-spec/GHERKIN.md` 起草, 主会话逐条核对书写纪律后返工一次 (v2), 再按仓库主人两项裁决与独立复查意见出 v3. v1/v2 未采纳, 只有 v3 被采纳并转正.
3. 机检: `check-ac.py` 草稿模式 22 个场景 / 22 个 AC 通过; 转正后正式模式同样通过; `check-tech.py` 6 节通过.
4. 独立检查 (未参与作者): 两轮, 报告见同目录 `SPEC-CHECK.md` 与 `SPEC-CHECK-02.md`. 第一轮提出 9 项 (P1-P9), 第二轮逐条复核为已解决, 另提 3 条低危 (N-1 指针范围措辞, N-2 D011 半句, N-3 拆分判据归属). 处理方式: N-1 与 N-3 按"指针只管交付定义, 默认句归终止处置, 拆分判据并入何时创建"落进 ISSUE-03 与 EXECUTION 覆盖矩阵, 未改已采纳的验收正文; N-2 不属于已采纳的任何 AC, 留作后续需要时再议, 不在本里程碑补写.

## 仓库主人裁决 (本轮)

- PoC 被裁决终止的处置写在 navigate 的 poc 条目里 (不另立章节).
- `workflow/demo/SKILL.md` 通用规则 1/5/6 三条一起改写, 口径为"演示材料可保留回看, 不主动删, 验证止于能演示", 并据此新增 G-008 与 AC-018/AC-019.
- 上一版验收清单里的其余内容 (含 P1-P5 对应的补充项) 一并采纳, 无删除项.

## 环境事实与注意

- 仓库没有 `.venv`, 测试用 `uv run python -m pytest workflow/navigate/tests`; 拆分时基线 27 passed.
- pytest 里有三个 navigate 展示服务 lifecycle 用例假定没有守护占用默认端口. 拆分时发现残留守护 (pid 18659, 端口 39271, 由更早会话为交付地图页启动) 导致 3 个用例失败; 已 `web_server.py stop` 后复跑通过. 该守护原先为容器 8801 -> 39271 的 socat 桥提供后端, 停止后该桥后端为空, 不影响本次产物.
- `workflow/to-spec/check-ac.py` 与 `ac-draft.py` 依赖 `gherkin-official`, 直接 `uv run python` 会缺包; 本仓库实际用法为 `uv run python <脚本>` 只在脚本带 PEP 723 头时成立, `check-ac.py` 无该头, 因此需要 `uv run --with gherkin-official python ...`.
- 视觉巡检 `workflow/navigate/tests/visual/render_checks.py` 在本容器可用 (`uv run --project general/access-web/browse ...`), 拆分时 9 项全通过; 该脚本不属于 pytest 套件.

## 未做与边界

- 未运行 `sync-to-pi.py`, 未改已安装 skills 与全局配置, 未验证安装效果或模型行为.
- 未开始 milestone-04 的任何实施改动; `roadmap.py`, `web/index.html`, `workflow/prototype/` 等文件在本轮仍为原样.
- 本里程碑不替 milestone-06 (流程接口打包裁决) 做决定, 也不改变其状态.
