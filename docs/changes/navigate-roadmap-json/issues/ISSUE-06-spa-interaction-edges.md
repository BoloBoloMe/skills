## 父级
- `../EXECUTION.md`
## 执行
- [x] 已实现
## 要构建什么
在 ISSUE-05 的 `workflow/navigate/web/index.html` 上叠加交互与边界态:
点击恒星弹出详情面板 (问题/状态/类型/阻塞于/产物链接); 目的地为终点恒星的详情内容; 笔记收进页面角落可折叠小面板; 歧路 (off_course) 不画进宇宙, 只在折叠区列出; 路线图不存在 (端点报错) 或参数缺失时展示友好提示页.
结尾: 人工验证特例 (NG-003) — 同 ISSUE-05, 手动验收.
## 覆盖依据
- Product: `docs/changes/navigate-roadmap-json/PRODUCT.md`, AC-015 (展示侧), AC-019
- Technical: `docs/changes/navigate-roadmap-json/TECHNICAL.md`, 模块接口 (单页应用: 渲染语义见 D012), 测试接缝 (SPA -> 手动验收)
## 相关决策
- `docs/changes/navigate-roadmap-json/DECISIONS.md`: D012
## 允许范围
- `workflow/navigate/web/index.html`
## 禁止范围
- 不动 `roadmap.py`, `web_server.py`, `SKILL.md`, `TEMPLATES.md`, 测试目录, 其他 skill
- 不做页面编辑能力 (NG-005); 不引入外部引用 (BR-006); 不把歧路画进宇宙 (D012)
## 代码定位提示
- 在 ISSUE-05 落地的同一文件内扩展: 详情面板/折叠区是叠加交互, 不改布局与轮询骨架
- 错误形态对接 ISSUE-04 的 TC-015 定下的端点错误响应
## TDD 切片
- 无自动化 TDD 切片 — 人工验证特例. 理由: NG-003; TECHNICAL.md 测试接缝明确 SPA 交互无自动化适配器 (AC-015/AC-019 -> 手动验收).
## 验证入口
手动验收, 在 ISSUE-05 的样例数据上追加: 造 off_course 条目与多条件 notes; 打开页面核对:
- 点击各恒星与终点恒星看详情字段齐备
- 笔记面板折叠/展开
- 歧路只在折叠区列出, 宇宙中不可见
- URL 指向不存在文件 → 友好提示页
通过标准: 各场景肉眼核对成立.
## 风险提示
- 详情面板与轮询更新并发: 数据刷新后已打开的详情面板内容须保持一致 (指向的里程碑被删除时不残留悬空面板)
## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.
## 适合 AFK 的原因
交互语义由 D012 定死, 全部为叠加实现; 构建过程 AFK, 验收 HITL (用户肉眼核对).
## 验收标准
- [x] AC-019: 恒星详情面板显示问题, 状态, 类型, 阻塞于, 产物链接
- [x] 终点恒星详情为目的地内容
- [x] 笔记可折叠面板, 歧路仅列于折叠区
- [x] AC-015 展示侧: 路线图不存在时展示友好提示页
- [x] 仍为零外部引用单文件
## 被阻塞于
- `ISSUE-05-spa-cosmos-render.md`
