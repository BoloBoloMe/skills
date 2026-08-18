# 提案: browser_agent 会话接口契约化, 支撑展示会话 (open/state/status)

- 日期: 2026-08-18
- 状态: 提案待审 (未决策)
- 涉及路径:
  - `general/access-web/browse/browser_agent/` (被提议方)
  - `general/adaptive-presentation/scripts/browser_session.py` (调用方)
  - `general/adaptive-presentation/SKILL.md` (CLI 契约, 本提案不改)

## 1. 背景与问题

### 1.1 现状

`adaptive-presentation` skill 通过 `scripts/browser_session.py` 提供三个 CLI 命令:

| 命令 | 语义 |
|---|---|
| `open <session-dir> <html-file>` | 在绑定 session-dir 的 headed 浏览器中打开本地 HTML |
| `state <session-dir>` | 读取已运行会话中 `window.__PRESENTATION_STATE__`, **不启动浏览器** |
| `status <session-dir>` | 双检存活 + 读 URL, 无副作用 |

该脚本不是 browser_agent 的重复实现, 而是其**组合封装**: 直接 import
`browser_agent.browser.Browser` 与 `browser_agent.config.BrowserConfig`, 复用脱离式
Chromium 启动/复用/自愈/headed 全部机制, 只补领域层 (路径校验, state 结构校验,
统一 JSON+错误码, 凭据脱敏).

### 1.2 能力覆盖比对

| browser_session.py 需求 | browser_agent 公开 API | 覆盖? |
|---|---|---|
| open: headed 启动 + 打开 file:// HTML | `navigate` 接受任意 URL, `BROWSER_HEADED` 支持 headed | 大体覆盖 |
| state: 只读求值 `__PRESENTATION_STATE__`, 不启动 | `evaluate_js` 可求值但**会隐式启动浏览器**; 无结构校验 | 部分覆盖 |
| status: 双检存活 + URL, 不启动 | `status()` 同语义且字段更全 (title/pid/pages) | 覆盖 |

### 1.3 三个问题

**P1: 半公开接口依赖 (稳定性风险).** browser_session.py 依赖的
`BrowserConfig(cwd=...)`, `config.read_metadata()`, `browser.page`,
`connect_over_cdp` 均不在 `__init__.py` 的 `__all__` 中, 未文档化. browser_agent
内部重构可能静默破坏 skill, 且两个目录独立演进, 无版本约束.

**P2: 能力缺口 A - attach-only 只读求值.** `state` 命令的语义是 "浏览器没在跑
就报 `browser_not_running`, 绝不启动" (SKILL.md 明确要求). browser_agent 没有
"连接已有会话求值任意 JS 而不启动" 的公开操作: `evaluate_js` 走 `get_session().page`
会触发启动; `status()` 不启动但只读 url/title, 不能求值任意表达式.

**P3: 能力缺口 B - 任意目录会话绑定.** 展示会话必须绑定到
`tempfile.mkdtemp` 生成的 session-dir, 与 agent 工作目录的浏览会话隔离 (不同
session-key). browser_agent 公开操作全部绑定进程 cwd; `get_session(cwd=...)` 已存在
但未导出、未文档化、仅首次调用生效.

## 2. 目标与非目标

### 目标

- browser_agent 公开 API 完整覆盖展示会话三命令的语义 (含 side-effect-free 只读).
- browser_session.py 退化为薄 CLI 壳: 路径校验, 协议层 (JSON/错误码/脱敏), 领域
  state 校验, 核心动作全部走 browser_agent 公开 API.
- CLI 契约与 SKILL.md 调用方式保持不变, 展示行为零变化.

### 非目标

- 不把 `__PRESENTATION_STATE__` 版本校验, JSON 错误码协议, 凭据脱敏下沉到
  browser_agent (presentation 领域概念, 污染通用库).
- 不改会话隔离语义 (session-key 仍由 cwd 派生, 展示会话与浏览会话互不可见).
- 不合并 `general/adaptive-presentation` 与 `general/access-web` 两个项目.

## 3. 方案选项

### 方案 A: 最小契约化

- `__init__.py` 导出 `get_session(cwd=...)`, browse.md 文档化 "首次调用前绑定会话
  目录" 模式.
- `status()` 增加可选 `cwd` 参数.
- browser_session.py 的 open 改为 `get_session(cwd=session_dir)` + `navigate`.

缺点: `state` 的 side-effect-free 语义仍无法表达 (evaluate_js 必启动), 缺口 A 未解决.

### 方案 B (推荐): 公开 attach-only 只读求值

在方案 A 基础上新增:

```python
def evaluate_js(script: str, cwd: str | None = None, start: bool = True) -> EvalResult
```

- `start=True`: 现有行为 (缺省, 兼容).
- `start=False`: 仅当 metadata 双检存活时经 CDP 连接求值; 否则返回
  `success=False`, `error="browser_not_running"` (与现 state 命令错误码一致).

备选变体: 独立函数 `evaluate_js_attached(script, cwd=None)`, 避免布尔参数双语义.
两者择一, 见 DECISIONS.md 决策点 D2.

配套改动:

- `status(cwd=None)` 与 `navigate(url, cwd=None)` 可选 cwd 参数 (透传给首次
  `get_session`).
- browse.md 增加 "绑定非 cwd 会话目录" 一节, 记录 `cwd` 参数与单例生效规则
  (仅首次调用生效, CLI 每进程一次调用无坑; 库内换会话需 `reset_session()`).
- `__init__.py` 导出 `get_session`.

browser_session.py 改造后形态 (每命令一行核心调用):

```python
# open
os.environ["BROWSER_HEADED"] = "true"
r = navigate(html_path.as_uri(), cwd=str(session_dir))

# state
r = evaluate_js("window.__PRESENTATION_STATE__", cwd=str(session_dir), start=False)

# status
r = status(cwd=str(session_dir))
```

领域层保留: html 绝对路径/containment/.html 校验, state 结构校验 (version==1,
values 为 dict), JSON 错误码映射, 凭据脱敏.

### 方案 C: 全量下沉 (不推荐)

把 open/state/status 作为 browser_agent 公开操作实现. 拒绝理由:
`__PRESENTATION_STATE__` 校验、错误码协议是 presentation 领域概念; 通用浏览库
不应内置单 skill 的页面状态协议; 方案 B 以更小改动面达成同一目标.

## 4. 语义不变量 (任何方案必须保持)

1. `state`/`status` 无副作用: 不启动浏览器, 不写 metadata.
2. CDP 连接只读路径不得调用 `browser.close()` (会杀远端 Chromium, 现有注释 NFR-003;
   用 `sync_playwright()` 上下文管理器清理本地句柄).
3. 展示会话与浏览会话隔离: session-key 派生自 session-dir, 与 agent 工作目录不同.
4. browser_session.py CLI 契约不变: stdout 单个 UTF-8 JSON, 退出码 0/非 0,
   错误对象含 `success/code/error` 且凭据脱敏.

## 5. 影响面与验证

### browser_agent (`general/access-web/browse/`)

- `browser_agent/operations.py`: `evaluate_js` 加 `cwd`/`start`, `status`/`navigate`
  加 `cwd`; 实现 attach-only 求值 (复用 `_check_alive` 等价双检 + CDP 连接).
- `browser_agent/__init__.py`: 导出 `get_session` 与新签名.
- `browse.md`: 文档化 cwd 绑定与 start=False 语义.
- `tests/`: 新增 attach-only 用例 (无存活会话返回 browser_not_running; 存活会话
  可求值且不杀浏览器; 连接后远端进程仍存活).

### skill (`general/adaptive-presentation/`)

- `scripts/browser_session.py`: 重写为薄壳 (保留校验/协议/脱敏), 核心调用走公开 API.
- `SKILL.md`: 不改 (CLI 调用方式不变).
- `tests/test_browser_session.py`, `tests/test_browser_session_integration.py`,
  `tests/test_skill_contract.py`: 回归验证 CLI 契约与行为不变.

## 6. 开放问题

1. `evaluate_js` 加 `start` 布尔参数 vs 独立 `evaluate_js_attached` 函数 (D2).
2. `cwd` 参数只加到三处 (`navigate`/`evaluate_js`/`status`) 还是全部操作统一加
   (点击/输入等无需绑定展示会话, 倾向只加三处, 减少 API 面).
3. browser_agent 侧是否需要在 attach-only 求值失败时区分 "无 metadata" 与
   "进程/端口已死" 两种错误码 (现 browser_session.py 统一 `browser_not_running`).
4. 是否将本提案拆为两个独立变更 (先做 A 解决稳定性, 再做 B 解决能力缺口),
   以便各自独立评审与回滚.
