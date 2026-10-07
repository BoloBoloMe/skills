# host 的每设备配置目录经运行期只读挂载进容器, 不烤进镜像层

容器内 agent 需要宿主侧那份"每台设备一份"的配置数据 (先例: llm-select 的评分表与模型目录 `~/.agents/llm-select/`), 而镜像构建只烤 `~/.agents/skills` 与 `~/.pi/agent`, 这类兄弟目录既不在烤入面也不在任何挂载点, 容器内相应 skill 直接报数据文件缺失. 决策: 这类**需要实时跟随宿主**的配置目录, 一律走 swt birth 时的 `-v <host dir>:<容器同路径>:ro` 只读挂载, 不 COPY 进镜像层 — 宿主改完, 新 birth 的容器立即生效, 无需重建 base (重建会顺镜像淘汰谓词链连带淘汰 display 与全部项目层).

备选方案: 镜像构建时 COPY (被拒绝: 每次改数据都要重建 base, 容器内数据随镜像过期); 整体挂 `~/.agents` (被拒绝: 其下 sandbox-worktree 运行记录与 mailbox 物刻意不进容器, 暴露面最小原则要求逐目录挂); 硬拦式前置检查 (被拒绝: 可选增强缺失不应阻断 birth, 软跳过加 stderr 告警即可).

后果: `~/.agents/llm-select` 与 skill 库同口径跟随宿主, 容器内 `score.py` 输出与宿主逐字一致且防写回; 该挂载是可选项, 宿主目录缺失或权限不足时 birth 照常, 容器内仍是数据缺失态, 由 stderr 说明. 注意: "输出逐字一致" 已由 2026-10-07 宿主真 birth (`swt-host-verify`, 镜像 `skills-v2:2026.10.07-2`) 验收: 容器内 `score.py` 65 行输出与宿主 `diff` 逐字一致, md5 同为 `3937f7358363c7f27b636aaa394925b0`, 见 `docs/changes/use-sandbox-worktree/DECISIONS.md` D059 端到端验收条. 完整决策见 `docs/changes/use-sandbox-worktree/DECISIONS.md` D059.
