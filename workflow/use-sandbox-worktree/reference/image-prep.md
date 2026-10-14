# image-prep 细则

首次写项目需求清单, 构建/匹配镜像, 核对 base 复制内容时读本文件. agent 模板契约见 [agent-templates.md](agent-templates.md).

```text
uv run python scripts/image-prep.py build-base    [--requirements <file>]
uv run python scripts/image-prep.py build-display [--requirements <file>]
uv run python scripts/image-prep.py match --repo <主仓> --requirements <file>
uv run python scripts/image-prep.py build --repo <主仓> --requirements <file>
```

三层镜像: 跨项目共用 base (OS/git/sshd/node/pi/codex/kimi/uv/herdr/socat, 排障件与 agent 初始化工具, 构建期 COPY 公共 skill 和 Pi 交互资源) → display (VNC 栈/chromium/waypipe, 默认清单 `image/requirements-browser.md`) → 项目层 (项目依赖). 容器运行期挂载 host skill 库遮蔽 base 副本, 但 base COPY 的内容与镜像播种的 `.venv` 仍须在镜像重建后供新容器使用; 模板数据更新不要求重建.

- 需求条目 = 名称 + 版本要求 (`>= <= > < ==` 或裸名称), `install=`/`probe=`. 探测缺省 `<name> --version`, apt 条目必须写 install. 项目信号取仓库 AGENTS.md/README/依赖清单; 安装清单须展示并获我确认后才落盘/构建, 安装会运行第三方脚本. birth 的缺省清单在 `<records-root>/<项目slug>/requirements.md`, 调用 match/build 脚本时 `--requirements` 必填.
- base/display 只在我明说时重建, display 缺失/过期会报 `NO-DISPLAY`/`DISPLAY-STALE`, 须先按审批构建 display 再建项目层. base 更新使旧 display 失配, display 更新使旧项目层失配. 真正 base Containerfile 由 scripts/image-prep.py 生成, image/Containerfile 只是极简测试镜像.
- 通用 base 固定 Pi 1.2.0/Codex 0.162.1/Kimi Code 2.1.1, 包含公共资源与初始化工具, 不烘入模型配置/凭据/具体网关模板. 当前 agent-template 契约 2.
- 旧 codex-config/env_key 静态镜像配置方式不再用于新模板镜像. codex-config/pi-config/kimi-config 等条目会被拒绝, 不在镜像内写旧路由.
- Pi staging 只继承交互/键位/扩展/主题/提示模板等公共资源, 不继承模型目录/auth/OAuth/sessions/trust.json/主机默认模型/代理/信任答案. 公共资源内有符号链接时停止, 须用户审查.
- host-only 门禁扩展继续排除 filesystem-operation-gate/git-operation-gate/python-operation-hook, 其余公共扩展保留. host ~/AGENTS.md 和 ~/docs 不进镜像.
- 匹配: 项目 label 候选按 build-id 从新到旧, contents 实测版本/摘要满足, 直接父 digest 等于当前 display, agent 契约匹配才 REUSE. display 须基于当前 base.
- 子层构建前校验父层契约, 不给旧父镜像新贴标签冒充兼容. 模板数据更新不重建镜像, 初始化工具契约更新须新镜像.
- tag = 日期-序号, digest = 内容精确版本, contents.md = 构建后的实测清单. 旧镜像/共享缓存 ID 保留, 不 rmi/prune.
- 记录: `<records-root>/<slug>/builds/<build-id>/`, display 在 `display/builds/`, 含 Containerfile/requirements.md/contents.md/build.json/context, 不进项目 Git.
