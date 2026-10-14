# 新容器 agent 配置模板

只用于后续新建容器. 不迁移/重启已有容器, 不改已有会话/凭据. 旧 resume 不自动加模板.
源码更新不等于发布. 当前可直接从源码调用脚本; 不全量 sync-to-pi, 不改真实 skills/主机模型设置/CLIProxyAPI 服务.

## 选择和数据

```text
uv run python scripts/agent-template.py list
uv run python scripts/agent-template.py show cliproxyapi
uv run python scripts/agent-template.py validate cliproxyapi
uv run python scripts/agent-template.py render cliproxyapi --output <隔离目录>/snapshot.json
uv run python scripts/swt.py birth ... --agent-template cliproxyapi
```

未传 `--agent-template` 必须 DECIDE, 即使只有一个候选. 现有网络/主机名/LAN/镜像决策仍有效.
收据绑定全部候选的名称/版本/内容摘要. 确认前任一模板变动都会废票, 不能把旧答案套到新数据上.

- `agent-templates/<名称>/template.json`: schema/name/version/contract/kind/base_url/credential/providers/defaults.
- `models.json`: 一份版本化模型规格, 含协议/窗口/输出声明/Pi 兼容项, 以及固定版本的 Codex 原生目录.
- `scripts/agent_config/{pi,codex,kimi}.py`: 确定的客户端格式转换器.
- `agent-template.py`: 固定校验/生成/安装/验收入口; 不构建镜像, 不接受模板 shell 命令.
- 同协议的新网关主要新增数据. 新协议/客户端格式须扩展转换器并测试; 不把安装命令塞入模板.

Codex 原生目录须含官方基础指令才能由当前客户端解析. 首版从官方 `rust-v0.162.1` 目录静态取 7 个已声明的 Responses 模型及必要字段, 不从主机取配置, 不在 birth 下载/猜目录. 关闭 WebSocket/Responses Lite/自动升级模型/未验证的实验工具. 原生基础指令是客户端目录数据, 不替代 birth 拼装的三份 agent 提示词 (`PUBLIC.md + ENV.md + 生成节 + 专属段`).

## 固定快照和目标绑定

全部 DECIDE 答完后:

1. 校验模板/默认模型/镜像契约/环境继承/凭据. 共用云/Git 凭据冲突须用户决定, 不自动删业务 Key.
2. 为本次创建分配随机令牌, 留档固定快照到 `runtime/<identity>/agent-templates/<容器>/<令牌>/snapshot.json`.
3. 创建新容器, 用既有过程完成启动/网络/SSH/git 克隆. 容器标签同时带契约/创建令牌/快照摘要.
4. 固定 installer 核对完整容器 ID/仓库/母体/名称/令牌/摘要和创建记录, 再向该完整 ID 写配置.
5. 配置/权限/凭据/三个客户端解析/GET 模型清单全过, 才写 ready 并登记 `verified`, 之后标 `born`/交付.

记录只保存名称/版本/摘要/快照路径/初始化状态/过滤掉的变量名/固定脱敏报告. 不保存 Key 原文或网关响应正文.
独立 install/check 与 swt 共用仓级锁, 不和生命周期操作并发写入.

重入使用本次固定快照, 不读取最新模板, 不换镜像/主机名/网络选择. create 已成功但登记前中断时, 只允许接回带本次令牌的同一新容器. 克隆完成有记录, 重入不再次 rm/clone 已完成的工作树.
模型配置安装已完成但网关验收失败时, 重入只重验已有文件/Key, 不重新复制主机最新 Key. 同名容器终结后再 birth 是新的创建, 用新的快照目录/令牌.

初始化失败留 `stage=agent-template-failed`, 不交付. 修复原因后重跑同一 birth, 或按 terminate 门禁终结该新容器. 不能用 resume 偷偷补安装.
新模板 resume 只核对该目标和固定快照, 不重新安装/换 Key/复制 OAuth, 不迁移旧对或修其他容器网络.
配置被用户另行改动时会报不一致, 不自动覆盖. 模板不是额外网络封锁, 不承诺阻止容器用户以后自行改配置或直接运行原始客户端.

## CLIProxyAPI 首版

统一入口 `http://host.containers.internal:8317/v1`.

| 客户端 | 配置 | 默认 |
| --- | --- | --- |
| Pi | 单 `cli`, 11 模型, 每模型各自 Responses/Chat 协议与 compat; enabledModels=[cli/*] | glm-5.3, max |
| Codex | 单 `cli`, Responses, `model_catalog_json` 指向固定 7 模型目录 | gpt-6-luna |
| Kimi Code | cliproxy-chat/openai 和 cliproxy-responses/openai_responses, 共 11 模型, 仅协议不同 | cliproxy-chat/glm-5.3 |

GPT 窗口声明 872000, 最大输出声明 128000; DeepSeek/GLM 保留模型数据中的规格. 这是版本化的客户端声明, 不等于长上下文/大输出实测. Codex/Kimi 不支持的输出上限字段不会伪造为已生效的配置. Kimi 的高级推理/工具流兼容性须用真实客户端另验, 不把 Pi compat 当成它的验收结果.
Pi 内置目录不等于配置的模型入口, enabledModels 也不是认证隔离. 因此新镜像不复制 auth/OAuth/模型目录/信任答案, 新容器不继承已知旧模型凭据/路由变量, 默认和轮换均选模板 provider. 网关失败不选择供应商回退.

凭据来源只允许 JSON 文件的 `client_api_key` 字段. 首版源 `/home/bolo/.config/cliproxyapi/keys.json`, 源须当前用户所有/普通文件/600, 拒绝符号链接. 不复制整个文件, management_key/上游 Key/OAuth 不进容器.
Key 只经 stdin 注入到容器 `.config/swt-agent/client-key.json`, 属主 bolo, 权限 600, 目录 700. 不进镜像/argv/普通日志. `pi/codex/kimi` 固定启动入口启动时读取此文件并设进子进程环境, 无需先 source shell 文件.
客户端诊断原文可能含 Key, 不透传. 网关仅 GET /v1/models, 禁止认证重定向/隐式代理, 响应只用于检查模板模型是否齐全, 不自动导入额外派生模型.
客户端自动验收只做本地解析: Pi 列模型和 auth check, Codex 0.162.1 用 features list 加载配置与固定原生目录, Kimi 用 doctor config. Codex doctor 会额外检查更新/网络/沙盒, 不用于 birth/resume 验收. 客户端 Key 的文件权限/环境注入和网关认证分别检查, 不把本地配置解析冒充真实请求/工具流证据.

## 通用镜像和审批

当前初始化契约为 2. base/display/项目链必须使用匹配契约的父镜像; 不能给旧父镜像重新贴新标签冒充兼容.
客户端固定版本 Pi 1.2.0/Codex 0.162.1/Kimi Code 2.1.1. 镜像包含程序/公共交互资源/固定工具, 不包含具体网关模板/配置/凭据/主机 trust.json.
真正 base Containerfile 由 image-prep.py 生成, `image/Containerfile` 仍是极简测试镜像.
镜像需求清单中的 codex-config/pi-config/kimi-config 等旧静态模型配置条目被拒绝. 模型配置只在 birth 初始化.
后续只改模板数据不重建镜像. 初始化工具契约改变时须新契约/新镜像. 旧镜像保留, 不做 rmi/prune, 共享缓存 ID 也不冒险删除.

base/display 重建仍须用户明说, 项目清单展示并确认后才落盘/构建. 构建会联网运行 apt/npm/uv/Playwright 安装脚本, 不能把模板方案确认当成跳过此门禁.
新模板过程不自动 chmod 主机 wayland socket 或放宽主机信任. 遇到该前置/共用业务凭据冲突时直接报告, 由用户决定.

## 安全测试和隔离验收

```text
# 在 skills-v2 仓库根执行, 不加载 tests/conftest.py 的全机卷/进程清理 hooks.
uv run --no-project python -m unittest discover -s tests -p 'test_agent_templates*.py' -v

# 单独批准真实容器验收后, 显式指定已经存在的本地镜像. 不拉取/构建镜像.
SWT_AGENT_PARSER_IMAGE='<已批准的本地镜像ref>' uv run --no-project python -m unittest discover -s tests -p 'test_agent_templates_codex_validation.py' -v
```

Codex 专项容器用例只创建一次性断网容器, 只读挂载本仓库初始化源码, 使用假 Key 和容器内回环模拟网关. 验证真实 install/check, 正常/错误 Codex 配置与原生目录, 重复检查不重写文件, 网关只收到 GET /v1/models. 超时清理只按本次 cidfile 和随机标签匹配的完整 ID 操作. 默认不跑此用例; 只读覆盖源码的通过结果不等于新镜像已发布, 也不替代完整 birth/resume/显示栈验收.

测试均用临时目录/假 Key/模拟 Podman/本机模拟网关. 真实容器验收单独审批, 使用独立仓库/记录根/镜像命名空间和唯一名称的一次性新容器. 不跑历史 m12 birth/OAuth 夹具, 不跑全量 pytest 或 sync-to-pi, 不使用业务容器/母体做试验.
真实客户端生成/工具调用优先接模拟网关. 对 CLIProxyAPI 只 GET /v1/models, 不产生额外上游生成费用. 文件/模型清单通过不等于真实客户端请求和工具流已经通过; 验收报告须分别列证据.
