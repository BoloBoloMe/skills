# navigate roadmap JSON 化 Product Spec

## 背景

skills-v2 仓库的 navigate skill 以 ROADMAP.md + 多个 MILESTONE-NN.md 记录路线图, 由 llm 直接手写文件, 格式正确性依赖 llm 输出质量, 漂移无强制防线; 制图展示依赖 present 画一次性 HTML, 无法随航行持续反映路线图状态. 提出方与受益者均为仓库所有者本人: 他要 llm 读写路线图的正确性由脚本强制保证, 并能随时经浏览器以宇宙航行隐喻查看任意路线图的实时状态.

## 目标

- G-001: 路线图全部信息存于单个 ROADMAP.json, llm 对路线图的每次读写都经守门脚本完成.
- G-002: 非法写入被守门脚本拦截, 返回指明原因的错误提示, 文件内容保持合法不变.
- G-003: 用户经浏览器打开 URL 即可查看指定路线图的宇宙可视化, 路线图状态变化在页面自动反映.
- G-004: 展示服务在同一设备上以单例常驻运行, 可服务任意路线图路径.

## 非目标

- NG-001: 不提供旧 markdown 格式 (ROADMAP.md/MILESTONE-NN.md) 到 JSON 的迁移命令. (理由: 旧路线图由 llm 读经脚本重建, 一次性成本低于维护迁移器.)
- NG-002: 不做认证, TLS 与网段隔离. (理由: 网段信任是 ADR-0005 已接受的既有取舍.)
- NG-003: 前端宇宙动画不做自动化测试. (理由: 视觉行为手动验收, 自动化成本不成比例.)
- NG-004: JSON 不存任何展示信息 (坐标, 颜色, 动画状态). (理由: 路线图是逻辑数据, 展示由前端推导.)
- NG-005: 页面只读, 不提供从页面编辑路线图的能力. (理由: 写的唯一通道是守门脚本.)

## 业务规则

- BR-001: 里程碑 status 只允许 `待处理`, `进行中`, `已关闭`.
- BR-002: 里程碑 type 只允许 `research`, `deliberate`, `prototype`, `task`.
- BR-003: blocked_by 只引用已存在的里程碑 id, 且不允许成环 (含自环).
- BR-004: 新增里程碑必填 title, type, question; status 默认 `待处理`, blocked_by 默认空.
- BR-005: 抵达终点恒星的判定 = 全部里程碑已关闭且未知海域为空; 里程碑清空但未知海域未散不算抵达.
- BR-006: 本变更不新增第三方依赖 (python 仅用 stdlib, 前端零外部引用). (审计)
- BR-007: 路线图目录不再产生 ROADMAP.md 与 MILESTONE-NN.md. (审计)

## 验收标准

```gherkin
# language: zh-CN
功能: navigate roadmap JSON 化

@AC-001 @normal @G-001
场景: 合法写入可读回
  假定 存在一份合法 ROADMAP.json, 含里程碑 milestone-01
  当 agent 经守门脚本将 milestone-01 的 status 写为 "进行中"
  那么 脚本报告成功
  而且 agent 经守门脚本 query 该字段返回 "进行中"

@AC-002 @failure @G-002 @BR-001 @BR-002
场景大纲: 写非法枚举值被拦截
  假定 存在一份合法 ROADMAP.json, 含里程碑 milestone-01
  当 agent 经守门脚本将 milestone-01 的 <字段> 写为 "<值>"
  那么 脚本拒绝写入, 错误提示列出合法值
  而且 ROADMAP.json 内容不变

  例子:
    | 字段   | 值     |
    | status | 已做完 |
    | type   | coding |

@AC-003 @failure @G-002 @BR-004
场景: 新增里程碑缺必填字段被拦截
  假定 存在一份合法 ROADMAP.json
  当 agent 经守门脚本新增里程碑 milestone-02, 只提供 title 与 type
  那么 脚本拒绝写入, 错误提示列出缺失字段 question
  而且 ROADMAP.json 内容不变

@AC-004 @failure @G-002 @BR-003
场景大纲: 非法阻塞引用被拦截
  假定 存在一份合法 ROADMAP.json, 含里程碑 milestone-01 与 milestone-02, 且 milestone-02 的 blocked_by 为 ["milestone-01"]
  当 agent 经守门脚本将 milestone-01 的 blocked_by 写为 <引用>
  那么 脚本拒绝写入
  而且 ROADMAP.json 内容不变

  例子:
    | 引用             | 说明       |
    | ["milestone-09"] | 引用不存在 |
    | ["milestone-01"] | 自环       |
    | ["milestone-02"] | 互环       |

@AC-005 @edge @G-001
场景大纲: 数组下标写入语义
  假定 存在一份合法 ROADMAP.json, notes 数组长度为 2
  当 agent 经守门脚本向 <路径> 写入 "新笔记"
  那么 <结果>

  例子:
    | 路径    | 结果                            |
    | notes.2 | 追加成功, notes 长度变为 3      |
    | notes.5 | 脚本拒绝并提示越界, 文件不变    |

@AC-006 @normal @G-001
场景: delete 删除路线图文件
  假定 存在一份合法 ROADMAP.json
  当 agent 经守门脚本 delete 该文件
  那么 该文件不再存在
  而且 agent 再 query 该文件时报文件不存在

@AC-007 @failure @G-001
场景: query 不存在的字段路径
  假定 存在一份合法 ROADMAP.json
  当 agent 经守门脚本 query 路径 "milestones.milestone-99"
  那么 脚本报错指明该路径不存在

@AC-008 @normal @G-004
场景: 首次启动展示服务
  假定 本设备无存活展示服务实例
  当 agent 执行 start
  那么 服务就绪并返回可访问的 URL

@AC-009 @normal @G-004
场景: 重复 start 复用单例
  假定 本设备已有存活展示服务实例
  当 agent 再次执行 start
  那么 服务复用既有进程, 不启动第二个实例

@AC-010 @edge @G-004
场景: 默认端口被占时自动换端口
  假定 本设备无存活展示服务实例
  而且 端口 39271 已被其他进程占用
  当 agent 执行 start
  那么 服务自动选用可用端口启动
  而且 status 报告实际使用端口

@AC-011 @edge @G-004
场景: 24h 空闲自退
  假定 展示服务正在运行
  当 最后一次请求之后经过 24h 无任何新请求
  那么 服务自动退出

@AC-012 @normal @G-003
场景: 页面渲染路线图
  假定 展示服务正在运行
  而且 存在一份 ROADMAP.json, 含已关闭里程碑 milestone-01 与进行中里程碑 milestone-02
  当 用户经带 roadmap 参数的 URL 打开页面
  那么 页面宇宙背景中每个里程碑各显示为一颗恒星
  而且 milestone-02 的恒星旁有飞船绕转
  而且 milestone-01 的恒星显示为已被驶过

@AC-013 @normal @G-003
场景: 多个进行中里程碑各有飞船
  假定 展示服务正在运行
  而且 存在一份 ROADMAP.json, 含两个进行中里程碑
  当 用户经带 roadmap 参数的 URL 打开页面
  那么 两艘飞船各自绕对应恒星旋转

@AC-014 @edge @G-003 @BR-005
场景大纲: 抵达终点判定
  假定 展示服务正在运行
  而且 存在一份 ROADMAP.json, 全部里程碑已关闭, 未知海域<海域状态>
  当 用户经带 roadmap 参数的 URL 打开页面
  那么 飞船<结果>

  例子:
    | 海域状态 | 结果                     |
    | 为空     | 停靠终点恒星, 页面显示抵达 |
    | 非空     | 不停靠终点恒星             |

@AC-015 @edge @G-003
场景: 路线图不存在时展示友好提示
  假定 展示服务正在运行
  当 用户经 roadmap 参数指向不存在文件的 URL 打开页面
  那么 页面展示路线图不存在的友好提示

@AC-016 @failure @G-003
场景: 端点拒绝非 .json 路径
  假定 展示服务正在运行
  当 攻击者向数据端点请求路径 "/etc/passwd"
  那么 端点拒绝, 不返回文件内容

@AC-017 @normal @G-003
场景: 页面轮询反映数据变更
  假定 用户已打开某 ROADMAP.json 的展示页面
  当 agent 经守门脚本将一里程碑的 status 改为 "已关闭"
  那么 页面在数秒轮询内将该恒星更新为已被驶过

@AC-018 @normal @G-003
场景: 恒星外观按类型区分
  假定 存在一份 ROADMAP.json, 含 research, deliberate, prototype, task 四类里程碑各一个
  当 用户经带 roadmap 参数的 URL 打开页面
  那么 四类里程碑恒星与终点恒星共五种外观互相可区分

@AC-019 @normal @G-003
场景: 查看恒星详情
  假定 用户已打开某 ROADMAP.json 的展示页面
  当 用户打开一颗里程碑恒星的详情
  那么 详情面板显示该里程碑的问题, 状态, 类型, 阻塞于与产物链接
```

## 决策引用

- docs/changes/navigate-roadmap-json/DECISIONS.md: D001, D002, D003, D004, D005, D006, D007, D008, D009, D010, D011, D012, D013, D014, D015, D016.
