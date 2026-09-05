---
name: present
description: 当我要求可视化或展示, 或你要向我解释的内容复杂到文字难以承载时使用.
---

本 skill 是展示层, 不改变调用方工作流, 决策顺序或确认规则. 总是生成 HTML.

## Setup

本 skill 无第三方依赖, 经 sibling 路径复用 `access-web` 的浏览器会话 (browser_agent 公共契约: `get_session`/`attached_context`). 首次使用前须确保 sibling `access-web` 已同步齐备且其 browse 依赖已安装:

```text
cd <access-web>/browse && uv sync && uv run playwright install chromium
```

`access-web` 缺失或 browser_agent 导入失败时 `<helper>` 会报错, 此时按本文步骤 6 的失败出口继续原工作流; 不要尝试自行安装或绕开.

## 远程 (ssh) 模式

进入流程前先判定是否远程 (ssh) 环境: `SSH_TTY` 或 `SSH_CONNECTION` 任一存在即远程; 两者都不存在但用户明示远程时, 同样按远程处理; 用户明示也可覆盖检测结果. 其余情况走 "1. 生成" 节的本地路径.

远程时完全不起 Chromium: 按本地路径相同规则生成自包含 HTML (含 `window.__PRESENTATION_STATE__`), 再用 `scripts/web_server.py` 把页面所在目录挂载到常驻 web 服务, 直接交付 URL. 该脚本纯标准库, 远程模式无需 Setup 节的 access-web 环境.

### 容器内分支

远程判定命中且 `/run/.containerenv` 存在 (podman 容器内, 即 sandbox-worktree 场景) 时走本分支: 完全不起 Chromium, HTML 生成与挂载复用与远程模式相同, 仅两处容器特有规则:

- bind 必须 `0.0.0.0` (端口映射只达容器公网监听, loopback bind 不可达); 容器端口必须复用容器创建时已映射的那个端口 — 映射在 create 时钉死容器端口, 服务换端口重启 host 侧即不可达 (实测), 不适用上方 "port_in_use 换端口重试" 的自由度.
- 输出 JSON 的 `url`/`hostname`/`lan_ip` 是容器视角, 不可直接交付: 在 chat 报告容器内端口与挂载根目录, 由 host 侧会话 `podman port <容器> <端口>` 发现映射端口并组装交付 URL, 容器内不猜测 host 地址.

add-dir/复用/stop 语义与远程模式一致 (容器内实测可用); 服务与运行时状态随容器生灭, 终结容器不必先 `stop`.

### 挂载或复用

```bash
uv run python <web-server> start <port> <页面所在目录绝对路径> --bind <addr>
```

`<web-server>` 是 `scripts/web_server.py` 相对本 skill 目录解析出的绝对路径. 成败以 stdout 单行 JSON (`success` 字段) 为准.

- 端口: 在 49152-65534 内随机选. 返回 `port_in_use` 时换端口重试, 上限 ≤10 次.
- bind: ssh 场景默认 `0.0.0.0`, 直接向用户交付可点击 URL. 该服务无认证无 TLS, 开放期间同网段任何主体可读全部已挂载目录, 选用此 bind 前向用户明示这一取舍一次. 用户要求仅本机可看时用 `--bind 127.0.0.1`, 此时成功输出 warning 含 `ssh -L` 端口转发指引, 原样转述给用户.
- 成功: 在 chat 给出可点击 URL, 原样转述输出中的 `url`/`hostname`/`lan_ip` 与 `port`, 一句话说明展示内容和待反馈问题.
- 复用: 同一用户的存活实例 bind 一致时幂等复用 (`reused: true`), 新目录自动经 add-dir 挂载, 忽略端口差异仅告警; bind 不一致返回 `bind_conflict`, 提示先 `stop` 再起新实例, 不静默复用.
- 失败出口: 重试与备选 bind 均失败后, 走既有失败出口 — 给出 HTML 本地绝对路径链接和内容摘要, 继续原工作流.

### 远程降级: 纯展示

远程模式降级为纯展示: 无 `__PRESENTATION_STATE__` 回读通道, 页面交互反馈与最终确认全部在 chat 完成. 页面仍须写 `__PRESENTATION_STATE__` (本地模式与未来兼容需要).

### 服务生命周期

- `status`: 探活; 服务已死时按原挂载清单重建, 可能换端口, 以输出 `port`/`rebuilt` 为准更新交付 URL.
- `add-dir <dir>`: 增挂目录, 同目录幂等.
- `stop`: 终止服务并删除运行时文件.
- 服务空闲 24h 自退; 运行时文件在系统临时目录, 重启后归零, 不承诺跨重启.

## 1. 生成

将 `scripts/browser_session.py` 相对本 skill 目录解析为绝对路径, 计为 `<helper>`. 不从调用方工作目录查找脚本.

**调用约定**: `<helper>` 的所有命令 (`open`/`state`/`status`) 在 browse 项目环境下执行, `<session-dir>` 与 `<html-file>` 一律绝对路径, `<html-file>` 位于 `<session-dir>` 内:

```bash
cd <access-web>/browse && uv run python <helper> <命令> ...
```

原因: `uv run` 按 cwd 解析项目环境, playwright 与 browser_agent 运行时只装在 browse 的环境里, 在本 skill 目录执行会落进无 playwright 的环境, 报 `No module named 'playwright'`; 相对路径则被入口校验直接拒绝. 成败以 stdout 的单行 JSON (`success` 字段) 为准: 成功时 stderr 仍会打 `Task was destroyed...`/`TargetClosedError` 等 playwright 进程退出噪声, 不表示失败.

### 输出目录

目录解析顺序: 调用上下文指定 (我明示位置, 或调用方 skill 给出目录) > 临时目录. 目录即浏览器会话键: 同一目录的反复展示复用同一浏览器窗口, 换目录即换会话, 所以同一话题的页面应落在同一目录.

- 指定: 用给定绝对路径, 不存在则创建. 页面持久留存, 归我处置, 不代我清理.
- 未指定: 首次生成页面时创建, 后续复用:

```python
import tempfile
session_dir = tempfile.mkdtemp(prefix="pi-present-")
```

路径丢失或目录不存在时重新创建. 不写死平台路径. 绝对路径保存在会话上下文的 `session_dir`.

完成标准: 有指定时页面落在指定目录; 未指定时目录由标准临时目录 API 在运行时得出, 唯一且位于该 API 返回的临时目录内.

### 信息架构

先确定信息架构再写: 这页分哪些部分, 每部分目标是什么, 用什么手法. 不固定段数和段名, 但必须有显式架构, 而非平铺所有信息. 部分间过渡平滑自然.

常见架构 (按信息形状选或组合, 非穷举):

- 解释型: 背景 → 本质 → 细节
- 对比型: 共性 → 差异 → 取舍
- 流程型: 输入 → 步骤 → 输出 → 边界
- 状态型: 状态集 → 转移 → 不变量 → 示例运行

完成标准: 每部分有一句话目标, 部分顺序有叙事逻辑而非按信息原始顺序. 信息形状不匹配上述示例时自行设计架构, 仍须显式.

### 写作

- 以 Martin Kleppmann 的清晰度和流畅感写作, 引人入胜, 经典风格.
- 聚焦本质, 而非完整细节. 用具体示例和 toy data 把抽象钉死.
- 对关键概念/定义, 重要边界情况使用 callout 标注.

### 图表

- 选取少量图表族, 在整个页面中复用以说明不同场景. 读者只需学一次图例.
- 务必包含示例数据! 空壳示意图无意义.
- 禁用 ASCII 图. 始终用 HTML/SVG 设计图表, 用 HTML 列表呈现清单.

### 页面

语义化不重复 `.html` 文件名, 以当天日期 `YYYY-MM-DD-` 开头, 便于排序且不入版本控制. 页面必须:

- 完整 HTML5, UTF-8, 可直接通过 `file://` 打开.
- 自包含 CSS 和必要脚本, 不依赖服务器/CDN/构建步骤/网络资源.
- 连续长页面, 含章节标题和目录. 顶层结构禁用 tab 切换.
- 响应式: 窄屏和宽屏下不重叠, 不截断关键文字.
- 键盘: 所有交互可通过键盘完成, 不依赖鼠标/触摸.
- 颜色: 状态表达不只用颜色, 同时使用图标, 文字或形状区分.
- 视觉形式服务当前问题: 流程突出方向, 层级突出从属, 对比保持共同尺度.
- 代码块始终用 `<pre>`. 若用自定义样式 div, CSS 必须含 `white-space: pre-wrap`. 保存前逐一扫描代码块, 确认其 CSS 含 `white-space: pre` 或 `pre-wrap`.
- 禁止 Mermaid. 可用 CSS, inline SVG, Canvas 或少量原生 JavaScript.

### 视觉风格

页面整体遵循 Saul Steinberg 式概念插画风格: 简洁手绘线条, 极简构图, 用隐喻性视觉符号表达复杂思想. 低饱和自然色调, 文学出版物般的排版气质, 营造安静, 智慧, 有哲学意味的氛围. 
视觉气质参照: 一本现代思想书籍, 一份高质量杂志插图, 一间充满阳光的创意工作室.
字体: 兼顾中英文, 中文用思源宋体, 英文用 Spectral. 手绘温度由线条装饰承担, 字体保持安静耐看, 中西混排平衡统一.
风格最小范例见 [`examples/less-is-more.html`](examples/less-is-more.html): 单屏页示范手绘线条, 留白, 字体栈与最小合规 `__PRESENTATION_STATE__`. 它只是视觉参照, 信息架构和页面结构要求不因此放松.

避免: 赛博朋克/霓虹渐变/未来机械感等廉价 AI 视觉套路; 
禁止: 用卡片和条条框框营造秩序感. 我更喜欢无限画布上的自由思考, 而非被框架束缚的条条框框.

### 页面状态对象

每个页面必须提供:

```javascript
window.__PRESENTATION_STATE__ = {
  version: 1,
  values: {}
};
```

- `version` 是整数, 当前只接受 `1`.
- `values` 是可 JSON 序列化的对象, 保存当前选择, 筛选和视图状态.
- 不保存完整事件历史.
- 无交互页面也必须提供空 `values`.
- 一次 JavaScript 求值读取整个对象.

### 有界交互

交互只在缩放, 筛选, 切换状态或比较视图能明显改善理解时才加入. 动效只用于表达状态变化或降低理解成本, 不添加与当前问题无关的彩蛋.

**允许**: 方案选择, 视图切换, 细节展开/折叠, 筛选, 缩放/平移.
**禁止**: 复杂表单, 多步骤操作流, 拖拽编辑, 应用级原型.

最终确认必须在 chat 中完成, 页面交互状态只是辅助反馈.

### 安全

- 不写入密钥, Cookie, token, 认证头或无关仓库内容.
- 原始日志和业务数据只保留理解当前问题所需的最小片段.
- 外部输入按文本处理: 用 `textContent` 或安全 JSON 编码写入, 不拼成可执行 HTML/event handler/脚本.
- 关键结论和待确认事项不只在页面中, chat 中必须同步说明.

### 步骤

1. 按输出目录规则创建或复用 `session_dir`.
2. 过滤凭据, 最小化原始日志/业务数据, 写入自包含 HTML 含 `window.__PRESENTATION_STATE__`.
3. 语义化不重复文件名, 新版本不覆盖旧版本.
4. 按调用约定执行 `uv run python <helper> open <session-dir> <html-file>`.
5. 成功时在 chat 给出: 本地绝对路径链接, 一句话说明展示内容, 待我观察/回答的具体问题. 关键结论和待确认决策仍须在 chat 中说明.
6. 失败时提供本地绝对路径链接和 chat 摘要, 继续原工作流.

完成标准: 信息已展示; HTML 路径可打开; chat 中保留了目的摘要和待反馈内容.

### 读取页面反馈

收到我的回复后, 只有页面含交互且 DOM 状态对当前反馈有帮助时才调用:

```text
uv run python <helper> state <session-dir>
```

- 合并 DOM 状态和 chat; 冲突时以 chat 为准.
- 最终决策仍按调用方工作流在 chat 中确认.
- 浏览器已关闭时 state 返回 `browser_not_running`, 不重启.

### 检查浏览器存活

```text
uv run python <helper> status <session-dir>
```

- `alive: false` 时不触发浏览器启动.
- 后续视觉展示调用 `open`, access-web 自愈路径清理旧 metadata 并重新启动.

## 2. 返回

展示不构成新的审批阶段. 处理我的反馈后回到调用前的工作流位置, 沿原有提问, 决策和确认规则继续.
完成标准: 后续动作由原工作流或我的最新指示决定, 本 skill 未改变其状态机.
