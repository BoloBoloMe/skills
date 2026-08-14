# 抓取参数参考

## `browse` 参数

| 参数 | 默认值 | 说明 |
|---|---:|---|
| `--mode` | `extract` | `extract` 提取正文, `full` 整页转 Markdown, `raw` 返回原始 HTML / 文本 |
| `--format` | `markdown` | 当前仅支持 `markdown` |
| `--include-links` / `--no-include-links` | `true` | 是否在正文中保留链接 |
| `--include-images` / `--no-include-images` | `true` | 是否保留图片 Markdown 和图片资源 |
| `--include-tables` / `--no-include-tables` | `true` | 是否保留表格 |
| `--no-fallback` | `false` | 抽取失败时禁止整页转换 fallback |
| `--max-chars` | 无 | 限制返回 Markdown 最大字符数 |

## 输出字段

`browse` 对 HTML 页面返回以下关键字段:

```json
{
  "url": "最终 URL",
  "title": "页面标题",
  "author": "作者",
  "date": "发布日期",
  "content_type": "text/html; charset=utf-8",
  "markdown": "提取后的 Markdown 正文",
  "resources": [
    {"type": "image", "url": "https://example.com/image.png", "alt": "图片说明"}
  ],
  "metadata": {"description": "页面描述"},
  "extraction": {
    "ok": true,
    "method": "heuristic",
    "mode": "extract",
    "confidence": "medium",
    "warnings": []
  },
  "status": 200
}
```

非 HTML 文本资源会把原始文本放入 `markdown` 字段. 二进制资源会返回结构化描述和资源清单.

## 抽取策略

HTML 内容按以下顺序处理:

1. `trafilatura`, 如果已安装.
2. `readability-lxml` + `markdownify`, 如果已安装.
3. 标准库启发式正文抽取.
4. `full_html_fallback`, 整页 HTML 转 Markdown.

增强依赖是可选项, 未安装时自动降级到后续策略, 脚本仍可运行, 但真实网页正文抽取质量有限. 脚本无 pyproject, 用 `uv run --with` 临时注入依赖:

```bash
uv run --with trafilatura --with readability-lxml --with markdownify python scrape/scripts/scrape.py browse <url>
```

## 限制

- 不执行 JavaScript, 不渲染 SPA.
- 不管理 Cookie/Session.
- 不处理登录后内容.
- 不解析 PDF, 不做图片 OCR.
- 不支持 FTP / 非 HTTP(S) 协议.
- 对强反爬网站, 客户端渲染页面, 复杂列表页, 商品页, 搜索结果页, 正文抽取可能低置信.

## `search` 输出

成功返回结果 list: `[{"title", "url", "snippet"}, ...]`. DuckDuckGo 与 Brave 两引擎都无果时返回 `{"results": [], "warnings": ["<各引擎诊断>"]}`, 调用方先判断返回类型.

## 体积上限与安全

- `MAX_RESPONSE_BYTES = 20MiB`: browse/search 响应体上限, 超限截断, warning `response truncated at {N} bytes`; gzip/deflate 解压后同限.
- `MAX_DOWNLOAD_BYTES = 200MiB`: download 流式写盘, 超限中止, 返回 `{"status": 0, "error": "download exceeded max size ...", "url": ...}`. 显式路径先写同目录 `<basename>.<随机>.part` 临时文件, 成功后 `os.replace` 原子替换; 任何失败 (HTTP 错误/超限/解压失败/网络错误) 只删 `.part`, 既有目标文件内容保留.
- 压缩响应体 (gzip/deflate) 解压失败时不写盘, 返回 `{"status": 0, "error": "<编码> decompression failed", "url": ...}` (含响应体 < 2 字节无法解码的情况).
- 重定向最多 10 跳, 超限返回 `{"status": 0, "error": "redirect limit exceeded (10)"}`. 跨域重定向剥离 `authorization`, `cookie`, `proxy-authorization`, `x-api-key`.
- SSRF 防护: 默认拦截解析到私网/环回/链路本地地址的 host; 经 `http_proxy`/`https_proxy` 等代理的请求跳过对端地址 (getpeername) 检查: 对端是用户自选代理, 目标 host 已过 `validate_url` 的 DNS 校验; `no_proxy` 命中而直连的 host 仍做检查. 可信环境 (测试/内网抓取) 可设 `SCRAPE_ALLOW_PRIVATE_HOSTS=1` 关闭.

## 错误与退出码

- 正常运行路径 exit 0, 运行错误一律 stdout JSON `{"status": 0, "error": "..."}`; Python < 3.9 时启动即 `sys.exit(1)`, argparse 用法错误 exit 2.

## 下载输出示例

成功:

```json
{"path": "/home/user/downloads/logo.png", "url": "https://example.com/logo.png", "size": 12345, "content_type": "image/png", "status": 200}
```

`status >= 400` 时不写盘:

```json
{"status": 404, "error": "http status 404", "url": "https://example.com/logo.png", "content_type": "text/html"}
```
