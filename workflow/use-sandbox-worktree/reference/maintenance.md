# 维护容器指令与分发

修改容器内 agent 的全局指令/环境变量继承, 或将本仓库改动送到使用现场时读本文件. birth 使用运行现场的配置, 仓库文件更新不等于现有容器更新.

## 提示词与环境小抄

`agent-prompts/` 的 `PUBLIC.md` 是三 agent 公共核, `ENV.md` 是容器常驻纪律, `PI.md`/`CODEX.md`/`KIMI.md` 是各自专属段 (后两份当前为空). birth 以 `PUBLIC + ENV + 生成节 + 专属段` 拼成三份提示词; 生成节由 `scripts/env_docs.py` 按 create 前事实提供触发式指针. 拼装结果连同 `identity.md`/`network.md`/`web-ports.md`/`agents.md` 留在 `<records-root>/runtime/<identity>/agent-prompts/<容器>/`, 然后只读挂进容器 (目标见 [delivery.md](delivery.md)). 更改公共内容只改 PUBLIC, 环境纪律只改 ENV, 特定 agent 的行为只改对应专属段, 不在三份成品中逐字同步. 宿主提示词与容器提示词互不同步; 母本更新只影响新 birth, 不会重写现有容器. 改显示栈/窗口直飞的容器纪律时, 核对 [living.md](living.md) 与 [pull-window.md](pull-window.md) 所述契约.

## 环境变量继承

birth 用 `podman create -e` 把 host 环境变量烘入容器, 改清单须重建容器. 全局清单是 `<records-root>/env.conf`, 项目清单是 `<records-root>/<项目slug>/env.conf`, 后者同名覆盖前者. 每行 `NAME` 表示读取 host 当前环境 (文件不存秘密值), `NAME=value` 只写非秘密常量; `#` 开头为注释. host 未设置的 NAME 会警告并跳过, 不阻断 birth. 新模板 birth 会在改资源前过滤点名的模型凭据/路由/配置路径变量, 只报告名字; 云/Git 等共用业务凭据由我决定, 不自动丢弃. 多行值不写入 SSH environment. 客户端 Key 只走 stdin/600 文件/固定启动入口, 不进 `create -e` 或 SSH environment; 详情见 [agent-templates.md](agent-templates.md).

## 分发边界

- 修改和验收通过不自动授权同步部署, 须另行明确要求. 网络维护须成套分发同版 `swt.py`/`network_update.py`/`net-firewall.py` 及参考, 旧脚本不能安全处理新 network-change.
- 修改 `swt.py`/本 skill/`reference/` 等宿主 agent 读的文件: 在仓库根 `uv run python sync-to-pi.py` 同步到 host skill 库后生效. 本仓库提出的 skill 修改只改仓库, 不直接改真实 agent skills.
- 信箱脚本在独立的 `workflow/mailbox/scripts/mailbox.py`, 同经仓库同步分发到 `~/.agents/skills/mailbox/`; 设备侧有自己的副本, 更新后取信会话重跑脚本才生效.
- `present` skill 也在 base 镜像构建期 COPY, 新 birth 想使用它的新版本, 同步后还须经审批重建 base/display/项目镜像; 已存在的容器不会更新.
- 三份 agent 全局指令是 birth 留档的只读快照, 与实时挂载的 skill 库不同, 母本变化不回写现有容器. 带依赖的 skill 项目改 `pyproject.toml`/`uv.lock` 时, 容器中的 `.venv` 种子不会自动同步, 须经镜像重建审批.
