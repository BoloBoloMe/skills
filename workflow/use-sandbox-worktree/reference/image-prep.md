# image-prep 细则

首次写项目需求清单/构建镜像/核对 base 复制内容时读本文件. 三层链与审批纪律见 SKILL.md 镜像管理节, agent 模板契约见 [agent-templates.md](agent-templates.md).

- 需求条目 = 名称 + 版本要求 (`>= <= > < ==` 或裸名称), `install=`/`probe=`. 探测缺省 `<name> --version`, apt 条目必须写 install. 安装清单须展示并获用户确认后才落盘/构建.
- base/display 仍只在用户明说时重建. 真正 base Containerfile 由 scripts/image-prep.py 生成, image/Containerfile 只是极简测试镜像.
- 通用 base 固定 Pi 1.2.0/Codex 0.162.1/Kimi Code 2.1.1, 包含公共资源与初始化工具, 不烘入模型配置/凭据/具体网关模板. 当前 agent-template 契约 2.
- 旧 codex-config/env_key 静态镜像配置方式不再用于新模板镜像. codex-config/pi-config/kimi-config 等条目会被拒绝, 不在镜像内写旧路由.
- Pi staging 只继承交互/键位/扩展/主题/提示模板等公共资源, 不继承模型目录/auth/OAuth/sessions/trust.json/主机默认模型/代理/信任答案. 公共资源内有符号链接时停止, 须用户审查.
- host-only 门禁扩展继续排除 filesystem-operation-gate/git-operation-gate/python-operation-hook, 其余公共扩展保留. host ~/AGENTS.md 和 ~/docs 不进镜像.
- 匹配: 项目 label 候选按 build-id 从新到旧, contents 实测版本/摘要满足, 直接父 digest 等于当前 display, agent 契约匹配才 REUSE. display 须基于当前 base.
- 子层构建前校验父层契约, 不给旧父镜像新贴标签冒充兼容. 模板数据更新不重建镜像, 初始化工具契约更新须新镜像.
- tag = 日期-序号, digest = 内容精确版本, contents.md = 构建后的实测清单. 旧镜像/共享缓存 ID 保留, 不 rmi/prune.
- 记录: `<records-root>/<slug>/builds/<build-id>/`, display 在 `display/builds/`, 含 Containerfile/requirements.md/contents.md/build.json/context, 不进项目 Git.
