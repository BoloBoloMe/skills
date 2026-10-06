# milestone-02 调查结论

调查目标是查清 pi 与本仓库当前实际存在的检查入口和护栏, 区分 pi 本身支持的能力, 仓库中写过的代码, 当前环境实际加载的代码.

## 0. 总结

1. [已证实] pi 有钩子式拦截点. 证据见 `/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/docs/extensions.md` 的 `Events and concurrency`/`Tool exposure` 小节. 扩展可以在 `tool_call` 阶段修改工具参数或返回 `{ block: true }` 阻断调用, 也可以通过 `user_bash` 替换用户 shell 执行实现. 这不是 Git 提交前检查, 而是 pi 进程内的工具调用检查.
2. [已证实] 本仓库有 3 个面向工具调用的护栏实现, 路径是 `/home/bolo/Workspace/review-old-sessions/pi/extensions/git-operation-gate.ts`, `/home/bolo/Workspace/review-old-sessions/pi/extensions/filesystem-operation-gate.ts`, `/home/bolo/Workspace/review-old-sessions/pi/extensions/python-operation-hook.ts`. 但它们目前只存在于仓库 `pi/extensions/`, 不在本机当前实际加载的 `~/.pi/agent/extensions/` 中, 也没有被当前 `/home/bolo/.pi/agent/settings.json` 直接登记. 不能把它们当成当前会话必然生效的护栏.
3. [已证实] 当前实际加载目录 `/home/bolo/.pi/agent/extensions/` 中的扩展主要处理会话状态, 重复输出, skill 输入和 Herdr 状态, 没有发现 `tool_call` 拦截器. `/home/bolo/.pi/agent/settings.json` 中还登记了一个不存在的扩展路径.
4. [未发现] 在 `/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/docs/` 和已安装的 pi `1.0.0` 代码 `/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/dist/` 中没有专门的 `pre-commit` 事件, Git 提交生命周期钩子或自动运行仓库测试的设置. 本仓库也没有活动的 pre-commit 配置, CI 工作流或 Git `pre-commit`/`pre-push` 钩子.
5. [已证实] 本仓库的测试入口是 `/home/bolo/Workspace/review-old-sessions/tests/run` + `/home/bolo/Workspace/review-old-sessions/pytest.ini`. `tests/run` 会根据未提交 Git 改动选择少量套件, `--fast` 排除 `e2e`, `--all` 才是全量回归. 这套改动面映射目前比 `/home/bolo/Workspace/review-old-sessions/tests/README.md` 写的覆盖范围窄, 存在漏选风险.
6. [已证实] pi 的全局 `/home/bolo/.pi/agent/AGENTS.md` 和仓库根目录 `/home/bolo/Workspace/review-old-sessions/AGENTS.md` 是两个不同作用域的上下文文件, 通常一起进入 prompt, 不是仓库文件替换全局文件. 两者都是提示词约束, 不是操作系统权限或测试强制执行器.

## 1. pi 的钩子和自动拦截能力

### 1.1 pi 本身提供拦截点

[已证实]

证据:

- `/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/docs/extensions.md`, `Events and concurrency` 小节明确说明不同事件可以通知, 修改数据, 替换结果或取消操作, 并明确写出 `tool_call` 可以修改输入或阻止执行.
- 同一文件的 `user_bash` 说明中写明, handler 返回 `operations` 或 `result` 会停止传播;没有 handler 处理时才继续本地执行.
- 同一文件的 `Error handling and cleanup` 小节写明, `tool_call` handler 出错时会阻止工具调用, 是 fail-safe 行为.
- `/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/docs/extensions.md`, `Tool exposure` 小节给出了返回 `{ block: true, reason: ... }` 的权限扩展示例.
- `/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/docs/security.md` 开头明确说 pi 默认不会在每次工具调用前逐次询问批准;需要用扩展, 沙箱或其他隔离手段降低影响.

因此, pi 有足够的进程内自动拦截能力, 但是否有护栏取决于实际加载的扩展. pi 不会因为存在 Git 仓库就自动运行测试或自动安装 Git hook.

### 1.2 settings.json 的实际状态

[已证实]

检查路径:

- pi 版本: `1.0.0`.
- `/home/bolo/.pi/agent/settings.json`.
- `/home/bolo/.pi/agent/extensions.synced.json`.
- `/home/bolo/.pi/agent/extensions/`.

实际配置要点:

- `defaultTools` 只有 `+codemode`, 即在默认工具基础上启用 codemode. 这里没有 Git 检查, pytest 检查或权限门禁设置.
- `packages` 是空数组.
- `extensions` 显式登记了 3 个路径:
  - `/home/bolo/.agents/skills/mailbox/pi-extension`, 存在.
  - `/home/bolo/Workspace/skills/skills-v2-visual-roadmap/workflow/use-sandbox-worktree/pi-extension`, 当前不存在.
  - `/home/bolo/.agents/skills/use-sandbox-worktree/pi-extension`, 存在.
- `/home/bolo/.pi/agent/extensions.synced.json` 只记录前后两个存在的 skill 扩展, 没有记录不存在的 visual-roadmap 路径.

本机实际存在的用户扩展是:

- `/home/bolo/.pi/agent/extensions/herdr-agent-state.ts`
- `/home/bolo/.pi/agent/extensions/repetition-guard.ts`
- `/home/bolo/.pi/agent/extensions/session-prune.ts`
- `/home/bolo/.pi/agent/extensions/skill-anywhere.ts`

这些扩展中检查到的事件只有 session/message/input/agent 状态类事件, 没有发现 `tool_call` 或 `user_bash` 拦截器. 两个存在的显式 skill 扩展路径中也只发现 mailbox 的 `session_start`/`agent_settled`/`session_shutdown` 和 use-sandbox-worktree 的命令注册, 没有工具调用门禁.

结论是: 当前 settings 和用户扩展目录不能证明 Git 写操作, cwd 外写入或 Python 命令改写会在当前 pi 进程中生效. 一个显式扩展路径还已经失效, 应视为当前配置事实而不是可用护栏.

### 1.3 仓库中的扩展实现

[已证实存在, 当前加载状态未证实为启用]

- `/home/bolo/Workspace/review-old-sessions/pi/extensions/git-operation-gate.ts:124-181`
  - 注册 `tool_call`.
  - 只处理 bash 工具调用.
  - 匹配 force push, 删除远端分支, `reset --hard`, 强删分支, `clean -f`, `stash clear`, 丢弃文件, `gc --prune` 等危险操作, 以及 push/rebase/restore 等警告操作.
  - 通过 UI 选择允许或返回 `{ block: true, reason }`.
  - 用 `session_start` 清空本次会话放行列表.
  - 它不是 Git `pre-commit` hook, 也不覆盖所有 Git 命令. 例如源码规则没有把普通 `git commit` 本身列为拦截规则.

- `/home/bolo/Workspace/review-old-sessions/pi/extensions/filesystem-operation-gate.ts:36-106` 和 `:160-216`
  - 注册 `tool_call`.
  - 对 `write`/`edit` 的 cwd 外路径要求确认, 无 UI 时直接阻断.
  - 对 bash 中静态识别的 cwd 外写入, 全盘搜索, NUL 文件写入等场景进行处理.
  - 会放行临时目录子路径等明确例外.
  - 只静态识别一组已知命令, 不能等价于完整 shell 语义分析.

- `/home/bolo/Workspace/review-old-sessions/pi/extensions/python-operation-hook.ts:17-41`
  - 对 pi 工具调用的 bash 和用户 `!`/`!!` 命令注册 hook.
  - 识别 `python`/`python3` 后改写为通过 `uv run python` 执行.
  - 这是命令改写, 不是拒绝执行.

- `/home/bolo/Workspace/review-old-sessions/pi/extensions/repetition-guard.ts`, `skill-anywhere.ts`, `session-prune.ts`
  - 分别处理重复输出, skill 输入和会话清理/命令, 未发现它们承担 Git 或文件写入权限门禁.

仓库代码和实际生效之间有明确同步边界:

- `/home/bolo/Workspace/review-old-sessions/sync-to-pi.py:448-488` 的交互计划可以把仓库 `pi/AGENTS.md` 和 `pi/extensions/` 复制到 pi agent 目录, 但需要用户在同步时选择.
- `/home/bolo/Workspace/review-old-sessions/sync-to-pi.py:315-366` 的自动登记只扫描 `~/.agents/skills/*/pi-extension`, 不扫描仓库 `pi/extensions/`.
- 当前 `/home/bolo/.pi/agent/extensions/` 中只有仓库上述 3 个普通扩展里的 `repetition-guard.ts`, `session-prune.ts`, `skill-anywhere.ts`, 且三者与仓库版本相同; `filesystem-operation-gate.ts`, `git-operation-gate.ts`, `python-operation-hook.ts` 均不存在.

### 1.4 pre-commit 类机制

[未发现 pi 内置机制]

已检查:

- `/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/docs/extensions.md` 的事件和设置说明.
- `/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/docs/settings.md`.
- `/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/docs/configuration.md`.
- `/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/docs/security.md`.
- 已安装包 `/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/dist/`.

对上述 pi 文档和已安装 dist 做 `pre-commit`, `precommit`, `commit hook`, `git hook` 搜索, 没有结果. 已证实的钩子边界是 pi 工具/输入/会话事件, 不是 Git 提交事件.

[未发现本仓库的 Git 自动检查]

- 根目录没有 `.pre-commit-config.yaml`.
- 根目录没有 `.github/workflows/`, `.gitlab-ci.yml` 或其他 CI 工作流.
- 当前仓库 `.git/hooks/pre-commit` 不存在, `.git/hooks/pre-push` 也不存在; `.git/hooks/` 只有 Git 提供的 `.sample` 模板.
- `git config --local`, `--global`, `--system` 都没有发现 `core.hooksPath` 或其他 hook 配置.
- 没有发现 Makefile, tox/ruff/mypy/flake8/black 等根级 lint 或检查入口.

## 2. 本仓库的检查入口和护栏

### 2.1 pytest 总入口

[已证实]

`/home/bolo/Workspace/review-old-sessions/pytest.ini:7-12` 定义:

- `workflow/navigate/tests`
- `general/present/tests`
- `tests`

并注册 `e2e` marker, 其定义是需要真实容器, 镜像构建, nft 或 netns 的慢层;快层使用 `-m "not e2e"`.

没有根级 `pyproject.toml`, `setup.cfg` 或 `tox.ini`. 当前只有:

- `/home/bolo/Workspace/review-old-sessions/general/access-web/browse/pyproject.toml`, 声明 browser-agent 和 pytest 测试可选依赖.
- `/home/bolo/Workspace/review-old-sessions/general/present/pyproject.toml`, 声明 present-helper, 没有 lint 配置.

### 2.2 `tests/run` 按改动面选套件

[已证实]

入口文件是 `/home/bolo/Workspace/review-old-sessions/tests/run`.

其实际行为:

- 先读取 `git status --porcelain`, 所以只根据当前未提交状态选套件.
- 不带参数时按内置 `RULES` 选择套件.
- `--fast` 在选中的套件上追加 `-m not e2e`.
- `--all` 直接运行 `uv run --with pytest python -m pytest -q`, 即全量串行入口.
- 其他参数原样交给 pytest.
- 选中 `tests/test_swt_m12.py` 且不是 `--fast` 时, 自动加入 `uv run --with pytest-xdist` 和 `-n 12`.
- 改到 `tests/conftest.py` 或 `pytest.ini` 时标记为 GLOBAL, 触发快层全量兜底, 并提示关账前仍需 `tests/run --all`.
- 没有命中规则时返回成功但不跑测试, 同时打印需要全量时使用 `tests/run --all`.

当前工作区唯一已有改动是 `/home/bolo/Workspace/review-old-sessions/docs/changes/review-session-skill/roadmap/ROADMAP.json`. 实测运行:

```text
./tests/run --fast
[tests/run] 改动面 docs/changes/review-session-skill/roadmap/ROADMAP.json 不命中任何测试套件, 无可跑项; 需要全量用 tests/run --all
```

这说明`命令返回成功`不等于`已经跑过测试`. 本次调查没有运行 `tests/run --all`.

### 2.3 改动面映射的已证实缺口

[已证实存在映射不一致]

`/home/bolo/Workspace/review-old-sessions/tests/run:23-31` 自己维护一份较短的 `RULES`, 但文件头说唯一事实源是 `tests/README.md`. 两者当前不完全一致:

- `/home/bolo/Workspace/review-old-sessions/tests/README.md:39-43` 声明 mailbox 脚本应映射到 `tests/test_mailbox_*.py`, 展示链应映射到 `test_swt_web_access.py` 和 `test_swt_m08_*.py`; `tests/run` 的 `RULES` 没有这些映射.
- `tests/run` 写的是 `workflow/use-sandbox-worktree/scripts/swt-mailbox.py` -> `tests/test_swt_mailbox_*.py`, 但当前文件清单中未发现该脚本或该测试 glob;实际 mailbox 脚本位于 `/home/bolo/Workspace/review-old-sessions/workflow/mailbox/scripts/mailbox.py`.
- `workflow/navigate/tests/` 下测试文件的改动没有专门映射.
- `pi/`, `sync-to-pi.py`, `workflow/mailbox/` 等重要代码改动也不会自动触发对应测试, 除非改动同时落在 `tests/*.py`, `general/present/`, `tests/conftest.py` 或 `pytest.ini`.
- 因此 `tests/run` 是一个便利的选择器, 不是完整的依赖图, 不能把`不命中任何套件`解释为`无需测试`.

### 2.4 pytest 快慢层实际规则

[已证实]

权威说明是 `/home/bolo/Workspace/review-old-sessions/tests/README.md:12-55`, 实现位于 `/home/bolo/Workspace/review-old-sessions/tests/conftest.py:176-205`.

- 快层命令约定为 `uv run --with pytest pytest -m "not e2e" -q`.
- 慢层命令约定为按改动面选择 `uv run --with pytest pytest -m e2e -q tests/test_swt_mXX.py`.
- `tests/run --all` 是全量两层回归, 但串行.
- 用例归为 e2e 的条件包括: 类名以 `E2E` 结尾, 继承链含 `SwtBirthFixture`, 或命中 `tests/conftest.py` 的显式表. 显式表当前覆盖 m04 的网络/nft/pasta 类和 m12 的两个真实容器类.
- 判据是是否创建真实容器, 镜像, netns 或 nft; fake run/fake bin/mock env 属于快层.
- `pytest.ini` 只注册 `e2e` marker, 没有发现其他性能层或 lint marker.

### 2.5 其他检查和护栏

[已证实]

- `/home/bolo/Workspace/review-old-sessions/tests/conftest.py` 有测试卫生兜底: 固定测试用 fleet key 缺失路径, 会话结束清理 m12 残留 git daemon/socat 进程和新建 podman volume.
- `/home/bolo/Workspace/review-old-sessions/workflow/navigate/tests/conftest.py` 对 web server 做 stop/TERM/KILL 收尾.
- `/home/bolo/Workspace/review-old-sessions/general/access-web/browse/tests/` 和 `general/present/tests/` 里有针对各自脚本的 pytest 用例.
- 这些是测试夹具和测试后的资源卫生, 不是提交前门禁, 也不自动保证所有源代码改动被覆盖.

[未发现]

- 没有发现独立 lint 命令或统一格式化命令.
- 没有发现 CI 在 push/merge 时重新运行 `tests/run --all`.
- 没有发现 pre-commit 框架或活动 Git hook.

## 3. AGENTS.md 的加载关系和影响范围

### 3.1 pi 的加载规则

[已证实]

证据:

- `/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/docs/configuration.md`, `Context files` 小节: Pi 从 agent directory, 当前工作目录和父目录加载 context files;文件在其目录或其子目录运行时生效.
- `/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/docs/security.md`, `Understand project trust` 小节: `AGENTS.override.md`, `AGENTS.md`, `CLAUDE.md` 等 context files 不因 project trust 拒绝而停止加载.
- `/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/docs/configuration.md` 同一小节: `AGENTS.override.md` 只替换同一目录的 `AGENTS.md`/`CLAUDE.md`, 不会抑制 agent directory 或其他目录的 context file.
- `/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/docs/cli.md`, `--no-context-files` 选项: 可关闭 `AGENTS.md` 和 `CLAUDE.md` 发现.
- `/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/docs/how-pi-works.md`, `Context` 小节: 发现的 context files 会进入 system prompt.

因此在当前仓库根目录启动 pi 时, 全局文件和仓库根目录文件都属于发现范围. 仓库根文件不会自动替换全局文件. 文档说明它们都参与 context 组装, 但没有在这些小节中承诺冲突条文的特殊优先级;不应把它们当成权限覆盖机制.

### 3.2 当前文件和大小

[已证实]

- 全局文件: `/home/bolo/.pi/agent/AGENTS.md`, 2537 bytes, 15 行. 作用域是该用户启动的 pi 的所有工作目录, 除非使用 `--no-context-files` 或等效配置关闭.
- 仓库根文件: `/home/bolo/Workspace/review-old-sessions/AGENTS.md`, 380 bytes, 3 行. 作用域是仓库根目录及其所有子目录, 因为它位于当前工作目录及其祖先发现链中.
- 仓库嵌套文件: `/home/bolo/Workspace/review-old-sessions/pi/AGENTS.md`, 1041 bytes, 8 行. 它只在以仓库 `pi/` 为当前目录或其下方目录时进入发现范围;从仓库根目录启动时, 不会因为它位于子目录而被发现.
- `/home/bolo/AGENTS.md` 当前不存在, 因而没有额外的 home 目录祖先文件参与本次范围.

内容职责也不同:

- 全局 `AGENTS.md` 包含语言和标点, sandbox/网络, headed 浏览器, mailbox, Git remote/提交推送和密钥存放等跨项目工作规则.
- 仓库根 `AGENTS.md` 说明本仓库是 skill/pi 配置仓库, 要用 `uv run python sync-to-pi.py` 同步, 并规定本仓库内的 skill 需求只能改本仓库内容.
- `pi/AGENTS.md` 是仓库中用于生成/同步到 pi agent 目录的规则源, 内容与实际全局文件不完全相同.

### 3.3 同步关系和实际风险

[已证实]

- `/home/bolo/Workspace/review-old-sessions/sync-to-pi.py:448-458` 把仓库 `pi/AGENTS.md` 作为可选单文件复制到 `/home/bolo/.pi/agent/AGENTS.md`.
- 这是交互式同步动作, 不是 pi 启动时自动读取仓库 `pi/AGENTS.md`.
- 当前仓库 `pi/AGENTS.md` 与全局文件 sha256 不同, 且全局多出 sandbox/网络/Git/密钥规则. 它们不是当前工作树中的同一份文件.
- 因此修改仓库根 `AGENTS.md` 只影响仓库 context;修改仓库 `pi/AGENTS.md` 也不会自动改变当前全局 pi, 除非运行同步并选择复制. 反过来, 直接修改全局文件不会回写本仓库.

[影响边界]

- AGENTS 文件能约束模型如何理解任务和选择命令, 但不会限制 bash, write, Git 或子进程的操作系统权限.
- 真正能在工具调用前阻断操作的是 pi 扩展的 `tool_call`/`user_bash` handler, Git hook, CI 或外部 sandbox;本仓库当前没有活动 Git hook/CI, 且仓库 3 个门禁扩展当前未在全局扩展目录中.
- 本次用户明确要求`不提交`, 该任务要求优先于全局 AGENTS 中`收口后提交并推送`的一般规则;本次没有提交.

## 4. 最终判定

[已证实]

- 能力层: pi 有可阻断工具调用的扩展事件.
- 源码层: 本仓库写有 Git, 文件系统和 Python 命令护栏.
- 实际运行层: 当前全局 settings/扩展目录没有证明这些 3 个仓库护栏正在加载, 因而不能依赖它们.
- 检查层: pytest 有明确快慢分层和 `tests/run` 入口, 但按改动面选择的规则不覆盖 README 声明的全部范围.
- 提交层: 没有发现 pre-commit, CI 或活动 Git hooks 自动兜底.
- 指令层: 全局 AGENTS 和仓库根 AGENTS 都会影响 prompt, 范围不同, 都不是硬安全边界.

[未发现]

- pi 内置 Git `pre-commit` 生命周期.
- 本仓库自动在 commit/push 前运行 pytest 或 lint 的机制.
- 当前配置中已登记并实际存在的仓库 `git-operation-gate`, `filesystem-operation-gate`, `python-operation-hook`.
