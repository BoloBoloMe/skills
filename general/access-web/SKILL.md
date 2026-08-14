---
name: access-web
description: '网页访问: 搜索, 正文提取, 文件下载, 截图, 登录, 表单交互, JS 渲染页面.'
---

# access-web

两种模式, 按任务分派:

## 只读抓取

提取正文, 搜索, 下载文件. 无 JS, 无登录态, 轻量.

读 [scrape/scrape.md](scrape/scrape.md).

## 交互浏览

点击, 输入, 截图, 登录, JS 渲染页面. 全浏览器, 有 session.

读 [browse/browse.md](browse/browse.md).

完成标准: 正确分派到参考文件, 按其中指令执行. 不确定用哪种模式时, 选只读抓取 (更轻量).
