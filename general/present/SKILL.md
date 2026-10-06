---
name: present
description: 把内容做成自包含 HTML 页面展示给我 (本地起浏览器, 远程交付网页地址).
disable-model-invocation: true
---

展示只是输出形式, 不另起审批阶段, 也不改变调用方的工作流和确认规则.

## 选择模式
若 `SSH_TTY` 或 `SSH_CONNECTION` 任一存在, 或我明确说明是远程, 走远程分支; 我的明确说明优先. 远程先读 [`REMOTE.md`](REMOTE.md), 其余走本地流程.

## 本地环境
首次本地展示前, 确保 sibling `access-web` 已同步且浏览器依赖已安装:

```bash
cd <access-web>/browse && uv sync && uv run playwright install chromium
```

若 `access-web` 缺失或 `browser_agent` 导入失败, 走本地失败出口, 不自行安装或绕过.

## 输出目录
优先使用调用上下文指定的位置, 不存在则创建; 否则用 `tempfile.mkdtemp(prefix="pi-present-")` 创建唯一目录. 将绝对路径记为 `output_dir`, 同一话题复用. 本地模式下它也是浏览器会话键, 换目录会换浏览器; 指定目录中的页面留存, 不代我清理. 完成标准: 页面写入指定目录, 或运行时新建的临时目录.

## 页面内容与样式
先确定页面结构和讲述顺序, 让每部分有明确目标, 不平铺原始信息. 可参考解释 (背景->本质->细节), 对比 (共性->差异->取舍), 流程 (输入->步骤->输出->边界) 或状态 (状态->转移->不变量->示例); 不匹配时自行设计.

以 Martin Kleppmann 的清晰度和流畅感写作, 聚焦本质, 用具体例子解释抽象, 并为关键概念和重要边界加重点提示. 图表只选少量可复用的类型, 带真实示例数据; 清单用 HTML 列表, 不画 ASCII 图.

整体采用 Saul Steinberg 式概念插画: 简洁手绘线条, 极简构图, 用隐喻表达复杂思想; 低饱和自然色, 留白, 文学出版物般的气质. 中文用思源宋体, 英文用 Spectral. 避免赛博朋克, 霓虹渐变和机械感, 不用卡片或条框制造秩序. [`examples/less-is-more.html`](examples/less-is-more.html) 是风格参考, 不替代以下要求.

将 `scripts/embed_mermaid.py` 相对本 skill 目录解析为绝对路径, 记为 `<embed>`. 它只依赖标准库, 本地和远程通用.

每页必须满足:
- 文件名语义明确且不重复, 以当天日期 `YYYY-MM-DD-` 开头, 不入版本控制; 新版本不覆盖旧文件.
- 完整 HTML5, UTF-8, 可直接用 `file://` 打开; CSS 和必要脚本内嵌, 不依赖服务器, CDN, 构建步骤或网络资源.
- 使用连续长页面, 有章节标题和目录, 顶层不使用 tab; 窄屏和宽屏都不重叠或截断关键文字.
- 交互可用键盘完成; 状态不能只靠颜色表达, 还要有文字, 图标或形状.
- 图表用 HTML/SVG/Canvas. 需要流程图或组件关系图时可用 Mermaid: 用 `<pre class="mermaid">` 写图表, 生成后运行 `uv run python <embed> <html-file>` 把渲染库内联进页面, 由页面内的 Mermaid 组件渲染; 不输出裸 Mermaid 源码. 代码用 `<pre>`; 自定义代码样式须设置 `white-space: pre` 或 `pre-wrap`, 保存前确认换行保留.

每页都提供 `window.__PRESENTATION_STATE__ = { version: 1, values: {} };`. `version` 固定为整数 `1`, `values` 是可 JSON 序列化的对象, 只存当前选择/筛选/视图状态, 不存事件历史; 无交互页也提供空对象.

只在筛选, 缩放, 切换状态或比较视图能明显帮助理解时加入交互; 可做方案选择, 细节展开, 筛选, 缩放/平移, 不做复杂表单, 多步操作流, 拖拽编辑或应用级原型. 动效只表达状态变化或降低理解成本. 页面状态仅辅助反馈, 最终确认在 chat 完成.

不写入密钥, Cookie, token, 认证头或无关仓库内容; 原始日志和业务数据只保留理解问题所需的最小片段. 外部输入按文本处理, 用 `textContent` 或安全 JSON 编码, 不拼成可执行 HTML/事件处理器/脚本. 关键结论和待确认事项也要在 chat 中说明.

## 本地展示流程
1. **生成页面**: 按上方内容与样式要求写入自包含 HTML, 文件放在 `output_dir` 内, 并将该绝对路径作为 `session_dir`. 页面含 Mermaid 时运行 `uv run python <embed> <html-file>` 内联渲染库. 完成标准: 页面可独立打开, 且具备所需结构, 状态对象和安全处理.
2. **打开页面**: 将 `scripts/browser_session.py` 相对本 skill 目录解析为绝对路径, 记为 `<helper>`. `<helper>` 的所有命令都在 browse 环境运行; `<session-dir>` 和 `<html-file>` 使用绝对路径, HTML 文件位于 session 目录内:

   ```bash
   cd <access-web>/browse && uv run python <helper> open <session-dir> <html-file>
   ```

   以 stdout 单行 JSON 的 `success` 字段判断结果; 成功时 stderr 即使出现 `Task was destroyed...`/`TargetClosedError` 等退出提示, 也不表示失败. 完成标准: JSON 报告成功, 或执行失败出口.
3. **交付**: 成功时在 chat 给出本地绝对路径链接, 用一句话说明内容并提出具体待反馈问题. 失败时给出本地绝对路径链接和内容摘要, 然后继续原工作流. 完成标准: 页面已展示或可从文件打开, chat 保留目的摘要和待反馈内容.
4. **处理反馈**: 只有当页面有交互且 DOM 状态有助于处理我的回复时, 才运行 `uv run python <helper> state <session-dir>`. 合并页面状态和 chat, 冲突时以 chat 为准; 浏览器已关闭时不重启. 完成标准: 反馈已并入调用方原有流程, 最终决策按原有规则确认.
5. **检查浏览器存活**: 需要再次展示前运行 `uv run python <helper> status <session-dir>`; `alive: false` 时不主动启动浏览器, 后续 `open` 自愈并清理旧 metadata. 完成标准: 存活状态已确认, 或已由 `open` 自愈.
