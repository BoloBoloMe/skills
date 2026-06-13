---
name: browse-web
description: |
  零配置, 零依赖的 Web 浏览/搜索/下载工具, 可完全替代 curl/wget.
  网页自动转 Markdown, 非 HTML 原样返回, 多媒体资源以引用清单呈现.
  内建 SSRF 防护, 自动处理 gzip/deflate 和字符编码.
  当用户需要从互联网抓取网页, 搜索信息, 或下载资源时使用此 skill.
---

# browse-web

零依赖, 开箱即用的 Web 访问工具. 所有输出为 stdout JSON.

## 快速开始

```bash
# 抓取网页 -> Markdown
python scripts/browse_web.py browse https://example.com

# 搜索互联网
python scripts/browse_web.py search "python urllib" -n 5

# 下载文件
python scripts/browse_web.py download https://example.com/logo.png ./logo.png
```

## 子命令

### `browse <url>`

抓取 URL, HTML 自动转 Markdown, 非 HTML 内容原样返回, 二进制资源以结构化描述 + 引用清单呈现.

```json
{
  "url": "最终 URL (跟随重定向后)",
  "title": "页面标题",
  "content_type": "text/html",
  "markdown": "转换后的 Markdown 文本",
  "resources": [
    {"type": "image", "url": "...", "alt": "..."}
  ],
  "status": 200
}
```

### `search <query> [-n 10]`

通过免费搜索引擎执行网络搜索. `-n` 控制返回条数 (上限 50).

```json
[
  {"title": "...", "url": "...", "snippet": "...", "source": "ddg"}
]
```

### `download <url> [path]`

下载资源到本地. `path` 省略时使用 tempfile; 相对路径以 CWD 解析; 父目录不存在时自动创建.

```json
{"path": "/absolute/local/path", "url": "...", "size": 12345, "content_type": "image/png"}
```

## 限制

- 不执行 JavaScript, 不渲染 SPA.
- 不管理 Cookie/Session.
- 不解析 PDF, 不做图片 OCR.
- 不支持 FTP / 非 http(s) 协议.

## 依赖

- Python >= 3.9
