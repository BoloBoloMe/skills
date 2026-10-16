# 新容器 agent 配置模板

新 birth 选择/安装模板, 初始化失败重入, 或检查已采用模板的容器配置时读本文件. 初始化只作用于本次新建目标, 后续 resume 按固定快照检查; 旧容器不加模板, 现有会话/凭据与主机模型设置不追溯修改.

## 选择与数据

```text
uv run python scripts/agent-template.py list
uv run python scripts/agent-template.py show <名称>
uv run python scripts/agent-template.py validate <名称>
uv run python scripts/agent-template.py render <名称> --output <隔离目录>/snapshot.json
```

birth 未传 `--agent-template` 就出 DECIDE, 即使只有一个候选也由我选. 收据绑定全部候选的名称/版本/内容摘要, 确认前任一模板变化都会废票; 网络/主机名/LAN/镜像仍各按其审批处理.
模板入口, provider, 默认模型与推理档位看 `show`/`agent-templates/<名称>/template.json`, 模型/协议/窗口/输出声明看同目录 `models.json`. 这些是客户端声明, 不等于长上下文/大输出或真实请求实测; 客户端不支持的字段不能冒称生效.
`scripts/agent_config/{pi,codex,kimi}.py` 转换客户端格式, `agent-template.py` 校验/生成/安装/验收, 不构建镜像或执行模板提供的 shell 命令. 同协议新网关以新增数据为主, 新协议/客户端格式须改转换器并测试.
Codex 固定原生模型目录须含官方基础指令, 不从主机配置或 birth 临时下载/猜目录. 关闭 WebSocket/Responses Lite/自动升级模型/未验证实验工具. 原生基础指令是客户端数据, 不替代 birth 拼装的全局提示词.

## 固定快照与重入

全部 DECIDE 答完后, 工具为本次创建保存固定快照与随机令牌, 创建记录/容器标签绑定模板契约和快照摘要. installer 核对完整容器 ID/仓库/母体/名称/令牌/摘要后才向该目标写配置, 不靠同名判定身份. 快照留在 `runtime/<identity>/agent-templates/<容器>/<令牌>/snapshot.json`.
配置/权限/凭据/三个客户端解析/网关 GET 模型清单全部通过, 才登记 `verified` 并标 `born`. 记录只存模板标识/摘要/快照路径/初始化状态/过滤掉的变量名/脱敏报告, 不存 Key 原文或网关响应正文. 独立 install/check 与 swt 共用仓级锁, 不与生命周期操作并发写入.

重入沿用本次固定快照/镜像/主机名/网络选择. create 成功但登记前中断时, 只接回带本次令牌的同一容器; 克隆已有完成记录时不再次 rm/clone 工作树. 配置安装完成但网关验收失败时只重验已有文件/Key, 不复制主机最新 Key. 同名容器终结后再 birth 才是新创建, 使用新快照目录/令牌.
初始化失败留 `stage=agent-template-failed`, 不交付. 修复后重跑同一 birth, 或按 terminate 保护检查终结; resume 不补安装. 新模板 resume 只核对固定配置与目标, 不重装/换 Key/复制 OAuth/迁移旧对/修其他容器网络. 配置被我另行改动时报告不一致, 不自动覆盖.

## 凭据与验收边界

凭据来源由所选模板的 `credential` 指定, 只读取 JSON 的 `client_api_key` 字段. 源必须为当前账户所有的普通文件且权限 600, 拒绝符号链接; 不复制整个文件, management_key/上游 Key/OAuth 不进容器. 云/Git 等与模型共用的业务环境变量冲突须由我决定, 不自动继承或丢弃; env.conf 继承规则见 [maintenance.md](maintenance.md).
Key 仅经 stdin 注入容器 `.config/swt-agent/client-key.json`, 属主 bolo, 文件 600/目录 700; 不进镜像/argv/create -e/SSH environment/普通日志. pi/codex/kimi 固定启动入口读取该文件并设入子进程环境, 无须 source shell 文件. 客户端诊断可能含 Key, 只用脱敏报告.
网关验收仅 GET `/v1/models`, 禁止认证重定向/隐式代理; 响应只检查模板模型是否齐全, 不自动导入额外派生模型. 网关失败不选供应商回退. HTTP 网关未加密, 只用已确认的本机/可信内网入口.
客户端自动验收只做本地解析: Pi 列模型和 auth check, Codex 用 features list 加载配置与固定原生目录, Kimi 用 doctor config. Codex doctor 额外检查更新/网络/沙盒, 不用于 birth/resume 验收. Key 文件权限/环境注入与网关认证分别检查, 本地解析不是请求/工具流证据; Kimi 的高级推理/工具流须单独实测, 不沿用 Pi compat 的结论.
Pi 内置目录/模板 enabledModels 不是认证隔离. 新镜像不复制 auth/OAuth/主机模型目录/信任答案, 新容器不继承已知旧模型凭据/路由变量, 默认和轮换都选模板 provider. 模板约束初始配置, 不阻止容器内进程读取客户端 Key 或以后自行改配置/运行原始客户端, 不是真正零凭据沙盒.

## 镜像与发布

准备兼容镜像或初始化工具契约变化时读 [image-prep.md](image-prep.md), 按其父层匹配与构建审批处理; 模板数据更新本身不要求重建镜像. 模板确认不授权构建或放宽主机 Wayland 权限, 遇缺口仍须问我.
源码更新不等于发布, 现场生效范围与同步授权见 [maintenance.md](maintenance.md); 现有容器不会因修改本文件或模板数据自动更新.

## 安全测试与隔离验收

```text
# 在 skills-v2 仓库根执行, 不加载 tests/conftest.py 的全机卷/进程清理 hooks.
uv run --no-project python -m unittest discover -s tests -p 'test_agent_templates*.py' -v

# 单独批准真实容器验收后, 显式指定已经存在的本地镜像. 不拉取/构建镜像.
SWT_AGENT_PARSER_IMAGE='<已批准的本地镜像ref>' uv run --no-project python -m unittest discover -s tests -p 'test_agent_templates_codex_validation.py' -v
```

普通测试用临时目录/假 Key/模拟 Podman/本机模拟网关. 真实容器验收须单独审批, 用独立仓库/记录根/镜像命名空间和唯一名称的一次性容器; 不跑历史 m12 birth/OAuth 夹具/全量 pytest/sync-to-pi, 不拿业务容器/母体试验.
Codex 专项只创建一次性断网容器, 只读挂载本仓库初始化源码, 假 Key 与容器回环网关验证真实 install/check: 正常/错误配置与原生目录, 重复检查不重写文件, 网关只收到 GET `/v1/models`. 清理只按本次 cidfile 和随机标签匹配的完整 ID. 默认不跑; 覆盖源码通过不等于新镜像已发布, 也不替代完整 birth/resume/显示栈验收.
真实客户端生成/工具调用优先接模拟网关. 对 CLIProxyAPI 只 GET `/v1/models`, 不产生额外上游生成费用. 报告须分别列文件/清单/真实请求/工具流的证据, 未实测就标未检查.
