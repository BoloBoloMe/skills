## 父级
- `../EXECUTION.md`
## 执行
- [ ] 已实现
## 要构建什么
重写 `workflow/navigate/web/index.html` 为完整单文件 SPA (css/js 全内联, 零外部引用 — 无 CDN 无构建):
从 `?roadmap=<绝对路径>` 取路径, 经 `fetch` 轮询 `/api/roadmap` (每 3-5 秒), 数据变化时增量更新画面;
宇宙背景充满星系; 每个里程碑 = 一颗恒星, 四种类型 (research/deliberate/prototype/task) + 终点共五种互相可区分的外观; 恒星位置由前端按 blocked_by 做 DAG 分层自动布局 (JSON 不存坐标); 进行中里程碑 = 绕其恒星旋转的飞船, 可多艘并行; 已关闭里程碑 = 已被驶过的恒星; 抵达判定 = 全部里程碑已关闭且未知海域为空 → 飞船停靠终点恒星并显示抵达 (迷雾未散是假抵达).
结尾: 人工验证特例 (NG-003) — 前端宇宙动画不做自动化测试, 靠手动验收清单核对.
## 覆盖依据
- Product: `docs/changes/navigate-roadmap-json/PRODUCT.md`, AC-012, AC-013, AC-014, AC-017, AC-018
- Technical: `docs/changes/navigate-roadmap-json/TECHNICAL.md`, 模块接口 (单页应用), 非功能要求 (页面刷新延迟), 测试接缝 (SPA -> 手动验收, 无自动化适配器)
## 相关决策
- `docs/changes/navigate-roadmap-json/DECISIONS.md`: D011, D012, D015
## 允许范围
- `workflow/navigate/web/index.html` (整体重写 ISSUE-04 的占位页)
## 禁止范围
- 不动 `roadmap.py`, `web_server.py`, `SKILL.md`, `TEMPLATES.md`, 测试目录, 其他 skill
- 不做页面编辑能力 (NG-005); 不引入任何外部引用/依赖 (BR-006); JSON 侧不加展示字段 (NG-004)
## 代码定位提示
- 数据契约: D005 schema (schema_version/title/destination/notes/milestones/unknown_seas/off_course)
- 端点行为: ISSUE-04 落成的 `/api/roadmap?path=` (成功返回 JSON 内容, 失败返回错误)
- 无既有前端代码, 从零写; 渲染可用 canvas 或 svg 自选
## TDD 切片
- 无自动化 TDD 切片 — 人工验证特例. 理由: NG-003 前端宇宙动画不做自动化测试 (视觉行为手动验收, 自动化成本不成比例); TECHNICAL.md 测试接缝明确 SPA -> 手动验收, 无自动化适配器.
## 验证入口
手动验收, 步骤:
1. 经守门脚本造样例数据: `uv run python workflow/navigate/scripts/roadmap.py save /tmp/demo-RM.json title 演示`, 依次 save destination, 一个已关闭里程碑, 一个进行中里程碑, 一个待处理里程碑, notes 若干
2. `uv run python workflow/navigate/scripts/web_server.py start` 取 URL, 浏览器开 `?roadmap=/tmp/demo-RM.json`
3. 逐条核对下方验收标准; 再经脚本改一个 status 为 已关闭, 观察页面数秒内更新
通过标准: 各场景肉眼核对成立, 轮询更新 ≤5s.
## 风险提示
- 深层 DAG 或宽扇入时布局可能挤爆画布 — 分层间距与画布缩放须留余量
- 零外部引用是硬约束 (BR-006): 不得引任何 CDN 字体/图标/库, 全部自绘
## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.
## 适合 AFK 的原因
渲染语义由 D012 逐条定死, 数据契约与端点已就绪; 实现与验收可由执行 agent 独立完成后交付用户手动核对 (验收本身 HITL, 构建过程 AFK).
## 验收标准
- [ ] AC-012: 每个里程碑一颗恒星, 进行中恒星旁有飞船绕转, 已关闭恒星显示为已被驶过
- [ ] AC-013: 两个进行中里程碑时两艘飞船各自绕转
- [ ] AC-014: 全关闭且未知海域空 → 飞船停靠终点恒星显示抵达; 未知海域非空 → 不停靠
- [ ] AC-017: 经脚本改 status 后页面数秒内更新
- [ ] AC-018: 四类型恒星 + 终点共五种外观互相可区分
- [ ] 单文件, 无外部引用 (源码无 http(s) 的 src/href 依赖)
## 被阻塞于
- `ISSUE-04-web-server-endpoints-idle-exit.md`
