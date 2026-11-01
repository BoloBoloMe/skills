# milestone-18 实施记录: 宿主端口映射自查顺序落地

- 依据: docs/proposals/2026-10-31-host-port-mapping-self-check.md P1-P3, 不改提案文档本身
- 分支: m18-env-docs (起点 50eb649)
- 状态: 三项均实现; 实测细节见下方 "已实测通过 / 未验证 / 证据缺口"

## 改动点

### P1 workflow/use-sandbox-worktree/agent-prompts/ENV.md

容器纪律句把 "查" 与 "问" 拆开: 缺值先按 ~/docs/web-ports.md 的自查顺序查 (当前 env → 容器内全进程 environ → 技能文档配方), 仍未找到再经可用信箱向宿主索取, 信箱不可用才问用户; 不猜. 文本与提案第 3 节 P1 改后文本一致.

### P2 workflow/use-sandbox-worktree/scripts/env_docs.py::_web_ports

- 宿主端口映射条目: 补 "端口每次 create 都变, 不要写死"; 删除旧的 "从 env 读取; 变量缺席时..." 连读即 "没看到 → 问人" 表述.
- 新增自查顺序条目 (先查后问三步): 当前 shell 的 `env` → 扫 `/proc/[0-9]*/environ` 全进程 (含提案原命令 `for p in /proc/[0-9]*/environ; do tr '\0' '\n' < "$p" 2>/dev/null | grep -E '^SWT_HOST'; done | sort -u`, 说明变量 create 时注入当时进程, 常不继承新 shell/tab) → 两步都没有才算缺失再走降级.
- 新增交付形状条目: `http://<SWT_HOST_LAN_IP>:<SWT_HOST_WEB_PORT>/<页面文件>`, 端口以自查结果为准; 样例只给形状, 无具体端口数字.
- 新增视角条目: 服务自报的 `url`/`hostname`/`lan_ip` 是容器视角不要直接交付, 宿主地址一律取 `SWT_HOST_LAN_IP`, 与 general/present/REMOTE.md 容器分支对齐.
- 架桥配方四步与 "信箱可用时向宿主会话索取网址 / 否则请我提供" 降级条款保留未动.
- 未手改容器 ~/docs/web-ports.md (它是生成器输出); 生成效果已渲染到 stdout 核对 (见命令记录).

### P3 tests/test_env_docs.py

新增 `test_web_ports_contains_self_check_order`: 断言生成的 web-ports.md 出现 `/proc/[0-9]*/environ` 与 `SWT_HOST_LAN_IP` 两个关键词 (另断言 "先查后问"), 防后续重构删掉自查指引不报错.

## 命令与证据

全部在本 worktree (/home/bolo/Workspace/refactor-skill-around-verification.worktrees/m18-env-docs) 内执行.

1. `PATH=/tmp/navigate-milestone-18/bin:$PATH uv run python -m pytest tests/test_env_docs.py -v`
   → 11 passed, 8 subtests passed in 0.02s (含新增 test_web_ports_contains_self_check_order).
2. 同法跑改动面映射要求的关联快层 (tests/README.md: env_docs.py → test_env_docs + test_swt_stage_env + test_swt_herdr):
   `PATH=... NAVIGATE_WEB_RUNTIME_DIR=/tmp/navigate-milestone-18 uv run python -m pytest tests/test_swt_stage_env.py tests/test_swt_herdr.py -q`
   → 23 passed in 0.18s.
3. 生成效果核对: `uv run python -c "...render_docs(facts)['web-ports.md']"` 输出含自查三步/交付形状/容器视角条目, 文本与提案第 3 节建议一致.
4. check_skill.py: `uv run python general/writing-for-llm/check_skill.py workflow/use-sandbox-worktree/agent-prompts/ENV.md` → 报 "缺少开头的 frontmatter 分隔线", exit 1. 结论: 该检查工具只适用于带 frontmatter 的 SKILL.md; agent-prompts/*.md 均为无 frontmatter 的提示词片段 (PI/CODEX/KIMI/PUBLIC 同), 对 ENV.md 不适用, 不据此改文档.

## 提案第 4 节实测 (只读生成的 web-ports.md, 容器内独立拼 URL)

- 第 1 步 (当前 shell `env | grep SWT_HOST`): 0 个命中 (grep exit 1) — 与事故根因 A 一致.
- 第 2 步 (照文档命令扫全进程): 拿到全套 SWT_HOST_LAN_IP=192.168.65.165, SWT_HOST_WEB_PORT=41141, _2.._6 等 (个别 /proc/<pid>/environ permission denied 属正常, 输出仍齐全).
- 第 4 步拼装: `http://192.168.65.165:41141/` 形状成立, 全程容器内操作, 未发信未提问.

## 环境 workaround (如实记录)

- 本容器无 podman, tests/conftest.py 的 pytest_sessionstart/sessionfinish 会硬调 `podman volume ls` 而使任何 pytest 直接 INTERNALERROR (前例: milestone-07/11 的同款阻塞). 本轮在 /tmp/navigate-milestone-18/bin/podman 放了仅 `exit 0` 的 stub 并前置 PATH: 只满足 conftest 的卷基线/清扫卫生钩子, 不参与任何用例断言; 上述 11+23 个用例本身均不依赖 podman. 未修改 conftest 或测试环境假装其他东西通过.

## 已实测通过

- P3 断言生效: 删除自查指引会导致 test_web_ports_contains_self_check_order 红 (关键词存在性由生成器文本保证).
- tests/test_env_docs.py 11 项全绿; test_swt_stage_env.py + test_swt_herdr.py 23 项全绿.
- 提案第 4 节自查路径: 容器内只读 web-ports.md 三步拼出局域网 URL 形状, 不发信不提问.

## 未验证

- `http://192.168.65.165:41141/` 的页面可达性: 容器内 curl 返回 000 (宿主侧该端口当前无服务监听或不可达, 非本里程碑范围); 本轮只验证 URL 可被独立拼出, 未验证从用户侧可打开.
- 真容器 birth 全流程 (birth 收尾验收 D018 用 BIRTH_MARKER 判断挂载物) 未跑: 本容器无 podman/镜像.

## 证据缺口

- 生成文档的 "真实 birth 写入 ~/docs/ 并被新容器读取" 端到端链路无本容器证据, 依赖真容器验收 (同既有 swt-container-env-docs 验收边界).
- 提案第 4 节的 "5 分钟计时" 未做严格计时, 仅确认操作链路可走通且步数明确.
