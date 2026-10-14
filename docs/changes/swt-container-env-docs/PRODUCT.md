# swt-container-env-docs Product Spec

## 背景

容器内的 pi/codex/kimi 三个 coding agent 干活时需要知道容器环境的限制与约定: 网络白名单, 信箱, 端口发布, 代码交付方式等, 这些都在容器创建时确定. 原先这类知识一部分重复写在三个 agent 各自的提示词里 (三份手工逐字同步, 迟早漂移), 一部分散落在宿主侧 skill 文档里, 容器内 agent 根本看不到. 本次改造: birth 时由脚本把母本拼装成三份 agent 系统提示词 (公共核 + 环境纪律 ENV + 生成节触发指针 + 各自专属段), 并生成 4 份本容器事实小抄只读挂载到 ~/docs/; 容器不再设 ~/AGENTS.md; 宿主机 pi 的 AGENTS.md 也改为 sync-to-pi 拼接生成. 提出方与受益者: 仓库维护者 (省去三份手工同步, 环境知识单一事实源) 与容器内 agent (环境知识每次开机必达, 不再依赖主动读文件).

## 目标

- G-001: 宿主 pi 的 AGENTS.md 由 sync-to-pi 每次运行自动拼接生成 (PUBLIC+PI), 带备份, 无逐项询问
- G-002: 新 birth 容器的三份 agent 系统提示词含全部环境纪律与生成节, 环境知识触达不依赖容器内 agent 主动读文件
- G-003: 新 birth 容器 ~/docs/ 有 4 份与该容器事实一致的生成小抄, 只读
- G-004: 容器内不再创建 ~/AGENTS.md
- G-005: navigate 的容器内展示配方只存在于环境小抄, SKILL.md 不再含该节
- G-006: birth 交付前验证提示词与小抄确实挂进容器

## 非目标

- NG-001: 不迁移运行中容器, 已有容器不补新提示词与小抄. (理由: 沿用既有母本制纪律, 改动不追溯)
- NG-002: 不改镜像三层与 agent-template 初始化结构, 提示词与小抄是挂载物不进镜像. (理由: 挂载实时可达, 重建镜像无收益)
- NG-003: 不做容器内启动时文件存在性检查. (理由: 挂载缺失属 birth bug, 由 birth 验收把关)
- NG-004: 不做宿主/容器提示词一致性校验. (理由: 用户裁定两环境允许不一致)
- NG-005: 不把 allow 清单与 create 后才知的事实写进小抄. (理由: 动态事实写死会过期, 走 env 变量与实测)
- NG-006: 不给容器 agent 可写观察区. (理由: 反方立论舍弃, 冲突报宿主已是环境纪律)

## 业务规则

- BR-001: 容器三份提示词 = concat(PUBLIC.md, ENV.md, 生成节, PI/CODEX/KIMI.md), 空专属段跳过; 容器内无 ~/AGENTS.md.
- BR-002: ENV.md 固定纪律条目 0-29 按账本 D008 全文逐字进入三份提示词.
- BR-003: 生成节与四份小抄全部由脚本生成, llm 运行时不现写注入内容. (审计)
- BR-004: 小抄集合与字段按账本 D012: identity (容器名/主仓路径/母体目录/分支/代码路径), network (模式+deny 清单+快照声明), web-ports (局域网地址+端口变量指引+架桥配方), agents (模板名/版本/摘要+三默认模型); allow 清单与 create 后才知的事实不写入.
- BR-005: 生成节 = 4 条触发式指针, 在三份提示词中相同, 指针携带本容器事实要点.
- BR-006: 容器内三份提示词与小抄只读.
- BR-007: 宿主 AGENTS.md = concat(仓库根 agent-prompts/PUBLIC.md, PI.md), sync-to-pi 每次运行无条件重写, 写前备份 .bak.
- BR-008: sync-to-pi 不同步不校验容器侧提示词, 宿主与容器提示词允许不一致.
- BR-009: birth 验收含挂载就位检查: 三份提示词与四份小抄非空且含生成标记, 缺件 PARTIAL 不交付.
- BR-010: navigate SKILL.md 不含容器内展示配方节, 制图 step 4 宿主流程保留; 架桥配方全文在 web-ports.md.
- BR-011: 母本与生成器更新只对新 birth 容器生效, 运行中容器不补.

## 验收标准

<!-- confirmed-flow: v1 -->

```gherkin
# language: zh-CN
功能: swt-container-env-docs 容器环境知识注入改造

背景:
假定 变更已实施: 仓库根与 skill 各有 agent-prompts 母本 (PUBLIC/PI/ENV/CODEX/KIMI), scripts/env_docs.py 存在, sync-to-pi.py 已含拼接逻辑

@AC-001 @normal @G-001 @BR-007
场景: 宿主 AGENTS.md 拼接生成并备份
假定 宿主 ~/.pi/agent/AGENTS.md 已有旧内容
当 使用者运行 sync-to-pi.py
那么 宿主 AGENTS.md 变为仓库根 PUBLIC.md 与 PI.md 的顺序拼接, 原内容备份为 AGENTS.md.bak, 全程无逐项询问

@AC-001 @edge @G-001 @BR-007
场景: 宿主拼接幂等重跑
假定 宿主 ~/.pi/agent/AGENTS.md 已是最新拼接结果
当 使用者再次运行 sync-to-pi.py
那么 拼接结果与现文件逐字一致, .bak 更新为重跑前的相同内容, 无报错

@AC-001 @failure @G-001 @BR-007
场景: 宿主拼接母本缺失报错
假定 仓库根 agent-prompts/PUBLIC.md 缺失
当 使用者运行 sync-to-pi.py
那么 脚本报错指出缺失母本路径, 宿主 AGENTS.md 保持原样未被改写

@AC-002 @normal @G-002 @BR-001 @BR-002
场景: pi 提示词为四段拼装
假定 已按 cliproxyapi 模板完成 birth, 容器运行中
当 读取容器内 /home/bolo/.pi/agent/AGENTS.md
那么 内容 = PUBLIC.md, ENV.md, 生成节, PI.md 的顺序拼接, ENV 条目 0-29 逐字在内, 末段含 herdr 专属行

@AC-002 @normal @G-002 @BR-001
场景: codex 与 kimi 提示词空专属段跳过
假定 已按 cliproxyapi 模板完成 birth, 容器运行中
当 分别读取容器内 /home/bolo/.codex/AGENTS.md 与 /home/bolo/.kimi-code/AGENTS.md
那么 两份 = PUBLIC.md, ENV.md, 生成节 的顺序拼接, 空的 CODEX/KIMI 专属段被跳过, 无占位说明残留

@AC-002 @edge @G-002 @BR-005
场景: 生成节三份相同
假定 已按 cliproxyapi 模板完成 birth, 容器运行中
当 比对三份提示词的生成节段
那么 三段逐字相同, 均含 4 条触发指针, 指针携带本容器事实要点 (网络模式, 容器名等)

@AC-003 @normal @G-004 @BR-001
场景: 容器内无 ~/AGENTS.md
假定 已按 cliproxyapi 模板完成 birth, 容器运行中
当 检查容器内 /home/bolo/AGENTS.md
那么 该路径不存在

@AC-004 @normal @G-003 @BR-004
场景大纲: 四份小抄存在且字段与容器事实一致
假定 已按 cliproxyapi 模板完成 birth, 容器运行中
当 读取容器内 ~/docs/<文件>
那么 该文件存在且非空, 内容为 <应有内容> 且与该容器实际事实一致

例子:
| 文件 | 应有内容 |
| identity.md | 容器名, 主仓路径, 母体目录名, 分支, 代码路径, 均与实际容器一致 |
| network.md | 网络模式 whitelist, deny 清单 (无则只写模式), 快照声明 "以实际连通性为准" |
| web-ports.md | 已确认局域网地址, SWT_HOST_WEB_PORT* 变量指引, socat 架桥配方 |
| agents.md | 模板名 cliproxyapi, 版本与快照摘要, pi/codex/kimi 各自默认模型 |

@AC-004 @edge @G-003 @BR-004
场景: 局域网地址未确认时的小抄形态
假定 birth 时宿主无已确认局域网地址
当 读取容器内 ~/docs/web-ports.md
那么 局域网地址位置写 "未确认", 端口变量指引仍在

@AC-004 @edge @G-003 @BR-004
场景: blacklist 容器的 network.md 形态
假定 容器改以 blacklist 模式创建且带 deny 条目
当 读取容器内 ~/docs/network.md
那么 模式写 blacklist, deny 条目逐条列出

@AC-004 @edge @G-003 @BR-004
场景: 动态事实不写入小抄
假定 已按 cliproxyapi 模板完成 birth, 容器运行中
当 在四份小抄全文检索 allow 放行条目与宿主端口映射数值
那么 均不出现 (allow 动态不写死, 宿主端口映射走 env)

@AC-005 @failure @G-002 @BR-006
场景: 提示词只读
假定 已按 cliproxyapi 模板完成 birth, 容器运行中
当 容器内 agent 向 /home/bolo/.pi/agent/AGENTS.md 追加内容
那么 写入被拒绝, 文件内容不变

@AC-005 @failure @G-003 @BR-006
场景: 小抄只读
假定 已按 cliproxyapi 模板完成 birth, 容器运行中
当 容器内 agent 向 ~/docs/identity.md 写入
那么 写入被拒绝, 小抄内容不变

@AC-006 @normal @G-006 @BR-009
场景: 挂载就位检查通过则交付
假定 birth 全部前置检查通过且挂载就位
当 birth 收尾执行挂载就位检查
那么 三份提示词与四份小抄均非空且含生成标记, 容器标 born 并交付

@AC-006 @failure @G-006 @BR-009
场景: 挂载缺件按 PARTIAL 报
假定 检查发现任一提示词或小抄缺失或为空
当 birth 收尾执行挂载就位检查
那么 birth 以 PARTIAL 报缺件, 不标 born 不交付

@AC-007 @normal @G-005 @BR-010
场景: navigate SKILL.md 不再含容器内展示配方节
假定 仓库为改造后的 skills-v2
当 检查 workflow/navigate/SKILL.md
那么 不含 "容器内展示配方" 节, 制图 step 4 宿主侧起服务交付 URL 的流程仍在

@AC-007 @normal @G-005 @BR-010
场景: 架桥配方完整迁入 web-ports.md
假定 已按 cliproxyapi 模板完成 birth, 容器运行中
当 读取容器内 ~/docs/web-ports.md
那么 socat 架桥配方完整在内: 8801 固定口归 navigate, 起服务读实际端口, 清残留死桥, 桥随服务同生死, URL 拼接, 变量缺席软失败走信箱, 不改 web_server.py

@AC-008 @edge @G-001 @BR-008
场景: 宿主与容器提示词互不同步
假定 使用者修改 skill 内 agent-prompts/PUBLIC.md 使其与仓库根版本不一致
当 使用者运行 sync-to-pi.py
那么 脚本正常运行且不报不一致错误, 宿主 AGENTS.md 仍只由仓库根 agent-prompts 拼接生成

@AC-009 @edge @BR-011
场景: 母本更新不影响运行中容器
假定 存在一个改造前 birth 的运行中容器
当 使用者更新母本或生成器后重跑 sync-to-pi
那么 该运行中容器的提示词与小抄保持原样不变
```

## 决策引用

- DECISIONS.md (同目录): D001-D019
