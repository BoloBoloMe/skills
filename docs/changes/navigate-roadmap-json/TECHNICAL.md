# navigate roadmap JSON 化 Technical Spec

## 模块划分

- **守门脚本** (`workflow/navigate/scripts/roadmap.py`, 新增): ROADMAP.json 的唯一读写入口. 藏住的复杂度: schema 定义与校验 (枚举/必填/阻塞引用存在性/环检测/写后整文档复核), 点分隔路径解析 (含数组下标定位与追加), fcntl 文件锁与原子写. 删除测试: 删掉它, 校验与并发保护复杂度散回每个 llm 读写调用点 — 有价值.
- **展示服务** (`workflow/navigate/scripts/web_server.py`, 新增): 同 uid 单例常驻 HTTP 服务, 交付 SPA 与路线图数据. 藏住的复杂度: 进程生命周期 (锁文件判活, 隐藏 `__serve__` 子命令 re-exec 守护化, 24h 空闲自退, 端口冲突自动回退), 端点安全限制 (.json 后缀 + 存在性). 删除测试: 删掉它, 单例与生命周期管理复杂度散到 SKILL.md 的手工操作步骤 — 有价值.
- **单页应用** (`workflow/navigate/web/index.html`, 新增): 单文件 SPA (css/js 内联, 零外部引用), 宇宙可视化. 藏住的复杂度: 按 blocked_by 的 DAG 分层布局, 恒星/飞船渲染与动画状态机, 轮询增量更新, 详情面板与折叠区交互.
- **skill 文档改造** (`workflow/navigate/SKILL.md`, `TEMPLATES.md`): SKILL.md 读写动作全部改述为守门脚本调用, 制图流程合并展示与落盘步骤, 调用模式判断依据改为 ROADMAP.json; TEMPLATES.md 重写为 JSON schema 说明.

模块边界: `workflow/navigate/` 内 (scripts/, web/, tests/, SKILL.md, TEMPLATES.md), 不触碰其他 skill.

## 模块接口

**守门脚本** — CLI: `uv run python roadmap.py <save|delete|query> <file> [path] [content]`.

- `save <file> <path> <content>`: 写指定字段; file 不存在则新建 (顶层结构自动初始化), 中间节点自动创建. content 先按 JSON 解析, 失败按裸字符串存. path 点分隔; 数字段为数组下标, 下标 == 长度追加, > 长度报错. 不变量: 写后整文档校验, 失败不落盘, 文件保持原状. 并发约束: fcntl 锁串行化写, 写经临时文件 rename 原子替换. 幂等: 同值重写结果相同.
- `delete <file>`: 删除整个 ROADMAP.json; 文件不存在时报错.
- `query <file> <path>`: 读指定字段; 文件或路径不存在时报错指明.
- 错误模式: stdout 单行 UTF-8 JSON, 成功 `{"success": true, ...}`, 失败 `{"success": false, "code": ..., "error": ...}`; 退出码 0/1. 校验类错误 message 含合法值或缺失字段名.
- 持久化 schema (即模块接口的一部分): 见 D005 — `schema_version` ("0.0.1"), `title`, `destination`, `notes[]`, `milestones{<id>: {title,status,type,blocked_by[],question,artifacts[],close_summary}}`, `unknown_seas[]`, `off_course[{what,reason}]`; 前沿/已关闭决策/阻塞关系派生不落盘.
- 性能特征: 单文件读写, 路线图规模 (数十里程碑) 下无要求.

**展示服务** — CLI: `uv run python web_server.py <start|status|stop>`; 隐藏子命令 `__serve__` 仅脚本自身 re-exec 用.

- `start`: 幂等 — 同 uid 有存活实例则复用并返回其 URL; 否则起守护进程. 默认端口 39271, 被占时自动选可用端口. 返回实际端口与 URL.
- `status`: 读运行时文件报告存活状态与实际端口; `stop`: 停止并清理运行时文件.
- 运行时文件 (pid/锁/端口) 位于系统临时目录, 不进仓库.
- 空闲自退: 最后一次请求后 24h 无新请求则退出.
- HTTP 端点: `GET /` 与 `GET /index.html` 返回 SPA 单文件; `GET /api/roadmap?path=<绝对路径>` 仅当路径以 `.json` 结尾且文件存在时返回其 JSON 内容, 否则返回错误 (页面据此渲染友好提示). 绑定 0.0.0.0.
- 错误模式: CLI stdout 单行 JSON, 退出码 0/1 (同守门脚本约定).

**单页应用** — 接口即 URL 契约: `http://<host>:<port>/?roadmap=<ROADMAP.json 绝对路径>`; 页面经 `/api/roadmap` 每 3-5 秒轮询, 数据变化时增量更新画面. 渲染语义见 D012 (五类恒星外观, 飞船绕转=进行中, 驶过=已关闭, 抵达=全关闭且未知海域为空, 歧路折叠区, 笔记折叠面板, 点击恒星详情面板). 配置: 无.

**skill 文档** — 不适用 (文档无接口).

## 接缝与适配器

- **守门脚本 ↔ 文件系统** (跨模块接口): 生产侧适配器 = 本地文件系统读写; 测试侧适配器 = pytest `tmp_path` 下的临时文件. 依赖类别: 本地可替换.
- **展示服务 ↔ 网络监听** (模块接口): 生产侧适配器 = stdlib `http.server` 绑定 0.0.0.0; 测试侧适配器 = 测试起真实实例绑 loopback 随机端口发真实 HTTP 请求 (对齐 present 测试先例). 依赖类别: 进程内.
- **展示服务 ↔ 运行时状态** (内部): 生产侧适配器 = 系统临时目录下的 pid/锁/端口文件; 测试侧适配器 = 环境变量覆盖运行时目录指向 `tmp_path`, 测试隔离互不干扰. 依赖类别: 本地可替换.
- **SPA ↔ 数据端点** (跨模块接口): 生产侧适配器 = `fetch /api/roadmap`; 测试侧无自动化适配器 (NG-003, 手动验收).

无外部依赖引入 (BR-006).

## 测试接缝

- AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007 -> 守门脚本 -> CLI -> subprocess 调脚本 + `tmp_path` 文件
- AC-008, AC-009, AC-010, AC-011 -> 展示服务 -> CLI + 运行时状态 -> 环境变量覆盖运行时目录 + 起真实实例 (AC-011 以缩短空闲阈值配置验证)
- AC-015, AC-016 -> 展示服务 -> HTTP 端点 -> loopback 真实 HTTP 请求
- AC-012, AC-013, AC-014, AC-017, AC-018, AC-019 -> 单页应用 -> URL + HTTP 端点 -> 手动验收, 无自动化适配器
- BR-006 (审计) -> 全模块 -> import 清单 -> 静态检查脚本: 扫描 import, 断言仅 stdlib
- BR-007 (审计) -> 守门脚本 -> 文件系统 -> 测试断言脚本只写目标 .json 文件, 不产生 .md

## 安全策略

认证/授权: 不适用 — 网段信任为 ADR-0005 已接受取舍, 本变更对齐不新增 (NG-002). 唯一暴露面收敛: 数据端点仅放行 `.json` 后缀且存在的路径, 挡任意文件探测 (D009). 加密/密钥/脱敏: 不适用 (无密钥, 无敏感数据处理). 隐私: 路线图内容网段可读, 与 present 常驻展示服务同一已接受取舍.

## 非功能要求

- 空闲自退: 24h 无请求自动退出 (防走后永久暴露); 验证口径: 测试以缩短的空闲阈值触发同一代码路径, 断言进程退出与运行时文件清理.
- 页面刷新延迟: 数据变更后一个轮询周期 (≤5s) 内反映; 验证口径: 手动验收 (NG-003).

## 关键流程

**save 写路径 (守门脚本单模块内)**: fcntl 加锁 → 读入并解析 JSON → 按 path 定位/写入 → 快速通道校验 (D006) → 整文档校验 (D007, 含环检测) → 写临时文件 rename 原子替换 → 解锁. 任一校验失败: 不落盘, 返回错误.

**start 幂等与端口回退 (展示服务单模块内)**: 读运行时文件判活 (pid 存活且 ping 通 → 复用返回) → 否则尝试默认端口 39271 → 被占则依次探测可用端口 → re-exec `__serve__` 守护化 → 写运行时文件 → 返回实际 URL.

## 决策引用

- docs/changes/navigate-roadmap-json/DECISIONS.md: D001, D002, D003, D004, D005, D006, D007, D008, D009, D010, D011, D012, D013, D014, D015, D016.
