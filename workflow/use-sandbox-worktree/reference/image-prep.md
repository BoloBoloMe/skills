# image-prep 细则

首次为项目写需求清单, 手跑 image-prep 构建, 或核对 base 层复制内容时读本文件. 三层结构与重建纪律见 SKILL.md 镜像管理节.

- 需求清单条目 = 名称 + 版本要求 (`>= <= > < ==` 或裸名称), 指令 `install=`/`probe=` (探测缺省 `<name> --version`); apt 条目必须写 `install=` (只写 probe 不装包).
- **推导规则: 项目层清单含 codex (或其他支持 env_key 的 llm CLI) 时, 必须附静态配置条目** — 以 codex 为例: `codex-config install="mkdir -p /home/bolo/.codex && echo <config.toml 的 base64> | base64 -d > /home/bolo/.codex/config.toml && chown -R bolo:bolo /home/bolo/.codex" probe="grep -c . /home/bolo/.codex/config.toml"`; 配置文件零秘密, 密钥走 `env_key` 指向 env.conf 继承的环境变量, 禁止把密钥写进清单/镜像/文件. 参照实现: `<records-root>/skills/requirements.md`.
- 匹配规则: 按镜像 label 找候选取最新构建 → 需求逐项版本满足 + 硬性条件 "基于当前 display 构建" → REUSE, 否则 BUILD-NEW (display 缺失时报 BUILD-NEW + reason, 不硬崩).
- 版本语义: tag = 日期-序号 (人读索引), digest = 镜像内容哈希即精确版本; contents.md = 构建后**实测**清单.
- 记录落 `<records-root>/<slug>/builds/<build-id>/` (Containerfile/requirements.md/contents.md/build.json), display 层落 `<records-root>/display/builds/`, 均不落项目 git.
- base 层复制 `~/.pi/agent` 时排除 auth.json/sessions/AGENTS.md (AGENTS.md 走母本制, 见 SKILL.md 母本与分发节); sshd_config SetEnv 烘配非交互 PATH 含 `~/.local/bin`. 扩展过滤 (白名单心智): extensions/ 只排除显式点名的门禁类扩展 (filesystem-operation-gate / git-operation-gate / python-operation-hook, 名单落 image-prep.py 注释), 其余扩展 (含 repetition-guard/herdr-agent-state) 与未来新扩展默认进容器; host 环境文档 (`~/AGENTS.md`/`~/docs/`) 不进容器.
