# navigate roadmap JSON 化 决策账本

## 决策

### D001 ROADMAP.json 单文件吞并全部路线图信息
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 路线图全部信息 (目的地/笔记/已关闭决策来源数据/里程碑详情/未知海域/歧路) 存入单个 ROADMAP.json; MILESTONE-NN.md 取消, 里程碑详情 (标题/状态/类型/阻塞于/问题) 作为 JSON 内 milestones 成员存在. 里程碑产物文件 (findings, 原型等) 仍是独立文件, JSON 只存链接 (artifacts 字段).
- 预计影响: `workflow/navigate/TEMPLATES.md` 重写; `workflow/navigate/SKILL.md` 全部读写动作改述

### D002 llm 禁止直接读写 ROADMAP.json, 一切读写经守门脚本
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: llm 不用 read/write/edit 工具直接触碰 ROADMAP.json, 必须通过 skill 提供的脚本完成. 动机 (用户原话): 尽可能降低 llm 输出不确定性对 JSON 正确性的影响 — llm 的错误输出被脚本拦截并返回错误提示; 脚本生成的 JSON 至少保证格式正确, 必要信息齐备. 脚本是 JSON 正确性的守门员, 不是透传器.
- 预计影响: `workflow/navigate/scripts/roadmap.py` (新增); SKILL.md 明文禁令

### D003 脚本接口与调用形态
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 脚本对外暴露三个操作: `save(file, path, content)` 写指定文件指定字段, `delete(file)` 删除整个 ROADMAP.json, `query(file, path)` 读指定字段. 调用形态为 CLI: `uv run python roadmap.py <save|delete|query> ...`, stdout 输出单行 UTF-8 JSON 结果, 退出码 0 成功 / 1 失败 — 对齐 general/present/scripts/web_server.py 的既有约定. save 自动创建文件与中间节点 (隐含 create). content 先按 JSON 解析, 解析失败按裸字符串存储.
- 预计影响: `workflow/navigate/scripts/roadmap.py`

### D004 path 语法: 点分隔, 数字段为数组下标
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: path 用点分隔 (如 `milestones.milestone-01.status`). 数字段定位数组元素 (如 `notes.2` = 第三条笔记), 支持下标级修改, 不要求调用者传全量数组. 下标 == 数组当前长度 = 追加; 下标 > 长度 = 越界报错. 对数组字段整体 save (如 `save(file, "notes", [...])`) 全量替换同样合法.
- 预计影响: `workflow/navigate/scripts/roadmap.py` 路径解析与写入逻辑

### D005 ROADMAP.json schema
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 顶层字段: `schema_version` (定为 "0.0.1"), `title`, `destination`, `notes` (数组, 下标即自然笔记编号), `milestones` (以 id 为键的对象, id 形如 `milestone-01`; 成员字段: `title` 简述, `status`, `type`, `blocked_by` 数组, `question` 详述, `artifacts` 产物链接数组, `close_summary` 关闭摘要初始 null), `unknown_seas` (字符串数组), `off_course` ({what, reason} 对象数组). **前沿, 已关闭决策, 阻塞关系均不落盘**: 前沿 = 未关闭且 blocked_by 全部已关闭的里程碑; 已关闭决策 = 各里程碑 close_summary + artifacts; 阻塞关系 = blocked_by 并集. JSON 只存路线图/里程碑逻辑数据, 零展示信息 (不存坐标/颜色等任何网页端展示字段).
- 预计影响: `workflow/navigate/scripts/roadmap.py` schema 定义与校验; TEMPLATES.md

### D006 save 校验规则 (守门员职责)
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: (a) 写 `status` 校验枚举 (待处理/进行中/已关闭), 写 `type` 校验枚举 (research/deliberate/prototype/task), 非法值报错并列出合法值; (b) 新增里程碑 = `save(file, "milestones.<new-id>", {...})`, 必填 `title`/`type`/`question`, 缺失则报错并列出缺失字段名, `status` 默认 `待处理`, `blocked_by` 默认 `[]`; (c) `blocked_by` 引用的 id 必须已存在且不允许环 (含自环); (d) 未知顶层字段拒绝写入.
- 预计影响: `workflow/navigate/scripts/roadmap.py` 校验层

### D007 写后整体校验 + 失败不落盘; 文件锁 + 原子写
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 每次 save 在内存完成写入后对整文档跑完整 schema 校验 (含环检测), 任一校验失败则不落盘并返回错误 — 这是兜底闸门, D006 是快速通道. 写文件经 fcntl 文件锁 + 写临时文件再 rename 的原子替换, 防并行 AFK 子代理并发写撕裂文件 (web_server.py 已有 fcntl 先例).
- 预计影响: `workflow/navigate/scripts/roadmap.py`
- 来源说明: 盘问扫盲阶段自扫发现, 用户审阅后未异议, 随盘问结束生效

### D008 展示 web 程序为 navigate skill 自持有的独立单例服务
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: web 程序是 navigate skill 自带的新脚本, 不复用/不依赖 present skill 的常驻展示服务. 架构照抄 present 模式: 同 uid 单例 (锁文件), 隐藏 `__serve__` 子命令 re-exec 自身起守护进程, CLI 输出单行 JSON. 独立理由: skill 自持有先例 (ADR-0015 mailbox 独立), navigate 不应依赖 present.
- 预计影响: `workflow/navigate/scripts/web_server.py` (新增)

### D009 数据端点只放行存在的 .json 文件; 网段可读为已接受取舍
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: `GET /api/roadmap?path=<绝对路径>` 仅当路径以 .json 结尾且文件存在时返回数据, 否则拒绝. 服务默认绑定 0.0.0.0, 网段内可读 — 对齐 ADR-0005 中用户已接受的网段信任取舍; 不引入认证/TLS. 后缀检查挡掉 `/etc/passwd` 类任意文件探测; 曾被评估的 "登记簿" 方案 (只放行登记过的路线图) 因状态维护成本不值而拒绝.
- 预计影响: `workflow/navigate/scripts/web_server.py`

### D010 服务生命周期: start/status/stop, 幂等复用, 24h 空闲自退, 端口冲突自动回退
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 脚本提供 start/status/stop 子命令; start 幂等 — 同 uid 已有存活实例则复用不起新进程; 24h 无请求空闲自退 (防永久暴露, 对齐 ADR-0005 二阶后果封堵); 默认固定端口 39271 (避开 mailbox LLM 中转 38427-38436), 端口被占时自动寻找可用端口启动; 实际端口不猜, 经 status 子命令读运行时文件获得.
- 预计影响: `workflow/navigate/scripts/web_server.py`

### D011 SPA 形态与数据刷新
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 单页应用为单个 HTML 文件, css/js 全部内联, 零外部引用 (无 CDN, 无构建步骤), 由 python 服务直接返回. 页面每 3-5 秒轮询数据端点, 数据变化时增量更新画面 (飞船位置, 恒星状态); 不用 websocket, 零额外依赖.
- 预计影响: `workflow/navigate/web/index.html` (新增)

### D012 宇宙渲染语义
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 宇宙背景充满星系; 每个里程碑 = 一颗恒星, 四种里程碑类型 + 终点 = 五种可区分恒星外观; 每艘飞船对应一个进行中里程碑, 绕其恒星旋转, 可多艘并行; 已关闭里程碑 = 已被驶过的恒星; 飞船停靠终点恒星 (抵达) 的条件 = 全部里程碑已关闭 **且** 未知海域清空 — 里程碑清空但迷雾未散是假抵达. 恒星位置由前端按 blocked_by 做 DAG 分层自动布局, JSON 不存坐标. 交互: 点击恒星弹出详情面板 (问题/状态/类型/阻塞于/产物链接); 目的地为终点恒星的详情内容; 笔记收进页面角落可折叠小面板; 歧路不画进宇宙, 只在折叠区列出 (已被排除的工作不占航线视野). URL 参数指定路线图路径, 页面据此请求端点; 路线图不存在时展示友好提示页.
- 预计影响: `workflow/navigate/web/index.html`
- 来源说明: 抵达条件中的 "且未知海域清空" 为盘问扫盲自扫发现, 用户审阅后未异议, 随盘问结束生效

### D013 制图流程改造: present 退出, 确认动作后移
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 原制图 step 4 (present 画一次性 ROADMAP.html) 与 step 5 (确认落盘) 合并为: 经守门脚本写 ROADMAP.json → start web 服务并交付 URL → 用户在浏览器查看确认 → 有异议经脚本修订 → 确认后 git commit. 确认动作从 "落盘前" 挪到 "落盘后, commit 前". ROADMAP.html 取消, present skill 不再参与 navigate 制图. SKILL.md 调用模式判断依据改为 ROADMAP.json 存在与否.
- 预计影响: `workflow/navigate/SKILL.md` 制图 Roadmap 节

### D014 不提供旧格式迁移命令
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 不做 ROADMAP.md → ROADMAP.json 迁移器. 旧路线图出现时由 llm 读旧文件后经守门脚本重建, 一次性成本低于维护迁移器; SKILL.md 注明此约定.
- 预计影响: `workflow/navigate/SKILL.md`

### D015 测试范围
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: python 侧 pytest 覆盖: roadmap.py (save/delete/query, 枚举与必填校验, 环检测, 数组下标与追加语义, 越界报错) 与 web_server (单例复用, 端口冲突自动回退, 端点行为, .json 后缀限制, 友好提示页). 测试置于 `workflow/navigate/tests/`, 对齐 present 的 per-skill tests 布局. 前端宇宙动画不写自动化测试, 手动验收.
- 预计影响: `workflow/navigate/tests/` (新增)

### D016 web 服务运行时文件放系统临时目录
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: pid/锁/端口等运行时文件放系统临时目录, 不进仓库, 避免弄脏 git 工作区.
- 预计影响: `workflow/navigate/scripts/web_server.py`
- 来源说明: 盘问扫盲阶段自扫发现, 用户审阅后未异议, 随盘问结束生效

## 事实

### F001 现行 navigate 产物形态
- 状态: 当前有效
- 来源: `workflow/navigate/TEMPLATES.md`
- 内容: 现行产物为 ROADMAP.md (区段: 目的地/笔记/已关闭决策/前沿/未决迷雾/范围外/阻塞关系) + 每里程碑一个 MILESTONE-NN.md (头三字段: 状态/类型/阻塞于; 正文: 问题). 存放于 `docs/changes/<feature-slug>/roadmap/`; research 与 deliberate 产物放 `docs/changes/<feature-slug>/<milestone-NN>/`.

### F002 present 常驻展示服务模式可直接参照
- 状态: 当前有效
- 来源: `general/present/scripts/web_server.py` (1331 行), ADR-0005, ADR-0006, docs/language/UBIQUITOUS_LANGUAGE.md
- 内容: present skill 已有同 uid 单例常驻 web 服务: 纯 stdlib 零依赖 (http.server), CLI start/status/stop/add-dir, stdout 单行 JSON, 隐藏 `__serve__` 子命令 re-exec 起守护进程, fcntl 锁, 24h 空闲自退, 控制端点仅 loopback, 绑定 0.0.0.0 网段可读是用户已接受的取舍.

### F003 术语 Roadmap/Milestone 已固化
- 状态: 当前有效
- 来源: docs/adr/0004-probe-roadmap-milestone-terminology.md
- 内容: ADR-0004 把 probe skill 术语从 Backlog/Item 改为 Roadmap/Milestone, 文件标识符 ROADMAP.md/MILESTONE-NN.md. 本变更把存储介质改为 JSON 但不改术语.

### F004 本仓库无存量 ROADMAP 文件
- 状态: 当前有效
- 来源: `find docs/changes -maxdepth 2 -name 'ROADMAP*'` 无结果
- 内容: 仓库内无需迁移的旧路线图; 旧格式可能存在于其他使用 navigate 的仓库, 由 D014 覆盖.

### F005 mailbox LLM 中转占用端口 38427-38436
- 状态: 当前有效
- 来源: docs/language/UBIQUITOUS_LANGUAGE.md (信箱词条)
- 内容: 选默认端口须避开该段; D010 取 39271.

### F006 本会话不在 Herdr 管理内
- 状态: 当前有效
- 来源: `env | grep -i herdr` 为空, HERDR_ENV 未注入
- 内容: use-herdr 规则禁止在 Herdr 之外操控聚焦会话, 本次 deliberate 的反方攻击子代理无法派发, 已按 grilling 规则降级纯自扫; 后续 deliberate 要求的 "子代理校验落盘产物" 步骤同样无法经 herdr 派发, 需用户指示替代方式.
