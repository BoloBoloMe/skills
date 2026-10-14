# swt-container-env-docs Technical Spec

## 模块划分

- **swt.py 拼装模块** (改): `stage_agent_prompts` 及挂载表常量. 责任 = 读五份母本, 按拼装公式产出三份提示词, 调 env_docs 生成节与四份小抄, 全部落留档目录, 返回挂载源. 藏了什么 = 拼接顺序, 空专属段跳过, 留档幂等, 生成节插值, 挂载表到容器路径的映射. 删除测试: 删掉它, 拼装与留档知识散回 birth 命令构造处, 有价值.
- **env_docs.py** (新): 纯函数生成器. 责任 = 由容器事实渲染生成节文本与四份小抄文本. 藏了什么 = 经缺失测试筛过的全部环境文案, whitelist/blacklist 形态分支, 缺席值占位 ("未确认"/"未登记"), 指针要点插值. 删除测试: 删掉它, 文案散回 swt.py 字符串字面量, 失去独立演进面与可单测性, 有价值.
- **swt.py birth 验收段** (改): 挂载就位检查. 责任 = 容器内读取三份提示词与四份小抄, 校验非空且含生成标记, 缺件抛 PARTIAL. 藏了什么 = 受检文件清单与标记判定.
- **sync-to-pi.py 拼接项** (改): 宿主 AGENTS.md 组装. 责任 = 无条件 concat(仓库根 PUBLIC.md, PI.md), 复用备份原子写, 移除旧单文件询问项; 对容器侧母本零触碰. 藏了什么 = 母本缺失的报错路径.
- **母本文件组** (数据, 新/删): 仓库根 agent-prompts/{PUBLIC,PI}.md (宿主), skill agent-prompts/{PUBLIC,ENV,PI,CODEX,KIMI}.md (容器, CODEX/KIMI 为空占位), 删除旧三份 *_AGENTS.md 与仓库 pi/AGENTS.md. 责任 = 环境文本单一来源.
- **navigate/SKILL.md** (文档, 改): 删 "容器内展示配方" 节, 制图 step 4 保留.
- **tests/test_swt_m12.py** (改): 母本字节断言改为拼装产物断言.

模块/目录边界: `workflow/use-sandbox-worktree/scripts/{swt.py, env_docs.py}`, 仓库根与 skill 的 `agent-prompts/`, `sync-to-pi.py`, `workflow/navigate/SKILL.md`, `docs/language/` 与 `docs/adr/` 联动; 不触碰 agent_config/ 模板初始化与镜像层.

## 模块接口

**swt.py 拼装模块**:
- `stage_agent_prompts(records_root, identity, container_name, *, net_facts) -> Path`: 返回留档目录 (含三份拼装提示词, docs/ 四份小抄). 不变量: 幂等 (同输入同字节, 仅内容变化时重写); 必须在容器 create 前调用 (产物作挂载源); net_facts 缺键按缺席文案渲染, 不抛. 错误模式: 任一母本缺失 → SwtEnvError, 文案指引用 sync-to-pi 同步, exit 2 不动资源.
- `AGENT_PROMPT_MOUNTS`: (staged 文件名, 容器路径) 三项 (pi/codex/kimi-code); docs 目录挂载常量 `/home/bolo/docs`. 顺序约束: 挂载源目录必须先于 create 命令构造存在.

**env_docs.py**:
- `render_generation_section(facts) -> str`: 生成节文本 (标题 + 4 条触发指针, 带事实要点).
- `render_docs(facts) -> dict[str, str]`: 恰好 identity/network/web-ports/agents 四键.
- 不变量: 两者均为纯函数, 同 facts 同字节 (留档可比对, 满足 BR-003 审计); facts 为平铺 dict (container, repo_path, mother_dir, branch, code_path, mode, deny, lan_ip, template_name, template_version, snapshot_digest, default_models); lan_ip 为 None → "未确认"; mode 非 whitelist/blacklist → "未登记"; network 文本恒含快照声明.

**swt.py birth 验收段**:
- `verify_env_mounts(container) -> None`: 对容器 exec 读取 3+4 个文件, 全部非空且含生成标记才返回. 错误模式: 缺/空/无标记 → SwtError(3, PARTIAL), 文案列缺件清单. 调用时点: born 标记前.

**sync-to-pi.py 拼接项**:
- `compose_host_agents_md(repo_root, pi_dir) -> None`: 读两份母本, concat, `_backup_and_atomic_write` 落盘. 顺序约束: 在 pi 目录探测后、交互计划前执行. 错误模式: 母本缺失 → 报错退出, 目标文件不动. 幂等: 同输入重跑产出同字节.

**母本文件组**: 文件存在性契约 — stage 时五份 (skill) 与两份 (仓库根) 缺一即报错; CODEX.md/KIMI.md 允许 0 字节.

## 接缝与适配器

- **接缝 1 (模块间, swt.py ↔ env_docs)**: 纯函数接口. 生产侧适配器 = swt.py birth 调用点; 测试侧适配器 = 直接调纯函数断言输出字节 (无 mock 需要). 内部无状态, 一个实现即覆盖全部调用点 (杠杆).
- **接缝 2 (宿主 ↔ 容器, ro bind 挂载)**: 位置 = 容器文件系统. 生产侧适配器 = podman create -v (留档目录 → 容器路径); 测试侧适配器 = 留档目录直接读 (与挂载源同字节) 与 m12 真容器 exec cat. 依赖类别: 本地可替换 (podman CLI, 已有 run 封装).
- **接缝 3 (sync-to-pi ↔ 宿主 pi 目录)**: 文件写入接缝. 生产侧适配器 = 真实 ~/.pi/agent; 测试侧适配器 = 临时目录. 依赖类别: 进程内.
- 无新外部依赖, 无远程接缝.

## 测试接缝

- AC-001-1/2/3 -> sync-to-pi.py 拼接项 -> 接缝 3 -> 临时目录单测: 拼接字节/备份/幂等/缺母本报错
- AC-002-1/2, AC-003 -> swt.py 拼装模块 + 母本组 -> 接缝 1 -> 拼装单测: 公式逐段, ENV 条目逐字, 空段跳过, 无 ~/AGENTS.md 挂载项
- AC-002-3, AC-004-1 -> env_docs.py -> 接缝 1 -> 纯函数单测: 生成节四指针与三份同字节, 四份小抄字段与缺席占位
- AC-004-2/3/4 -> env_docs.py -> 接缝 1 -> 纯函数单测: lan_ip None, blacklist+deny, 输出不含 allow/宿主端口值
- AC-005-1/2 -> swt.py 挂载表 -> 接缝 2 -> m12 真容器: exec 追加写被拒 (沿用现有 ro 写断言扩展 docs 目录)
- AC-006-1/2 -> swt.py birth 验收段 -> 接缝 2 -> 单测: 留档目录全齐/构造缺件两态; m12 真容器 born 路径各一次
- AC-007-1 -> navigate/SKILL.md -> 无代码接缝 -> 文件内容断言 (不含该节, step 4 在)
- AC-007-2 -> env_docs.py -> 接缝 1 -> 纯函数单测: web-ports 文本含配方全要素
- AC-008 -> sync-to-pi.py 拼接项 -> 接缝 3 -> 单测: 容器侧母本与仓库根不一致时拼接仍成功
- AC-009 -> swt.py 拼装模块 -> 接缝 2 -> 无新测试: 挂载随 create 固定为既有架构性质 (P1-6 机制沿用)
- BR-003 (审计) -> env_docs.py -> 接缝 1 -> 覆盖矩阵: 纯函数无 IO 无 llm 调用的代码结构审计 (人工)
- BR-001/002/004/005/006/007/008/009/010/011 -> 对应 AC 场景 -> 同上列接缝 -> 已由上列场景覆盖

## 安全策略

- 容器篡改防护: 三份提示词与小抄全部 ro 挂载, 容器内写被拒 (AC-005), 防容器内 agent 改写自身环境事实与宿主注入的纪律.
- 凭据隔离: 注入内容 (提示词/小抄/生成节) 不含任何密钥; 客户端 Key 仍走既有 stdin/600 文件通道, 本变更不触碰.
- 信息暴露边界: 小抄含局域网地址与容器拓扑, 与既有 SWT_* env 烘入同等级 (宿主已确认非秘密); allow 清单与宿主端口映射刻意不入小抄 (缩小可读面).

## 关键流程

birth 内顺序约束 (跨模块, 不可从单模块接口读出): stage_agent_prompts 拼装 (含 env_docs 渲染) → create 命令携带 3+1 个挂载 → start → apply_network (create 后, deny 事实已冻结于小抄) → bake_host_info_env (宿主端口/直通走 env, 不回写小抄) → verify_env_mounts → 标 born. resume 不重跑拼装 (留档即真相), 仅沿用既有挂载.

## 决策引用

- DECISIONS.md (同目录): D001-D019
