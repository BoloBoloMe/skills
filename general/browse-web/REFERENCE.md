# browse-web 参考说明

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

增强依赖安装:

```bash
pip install trafilatura readability-lxml markdownify
```

增强依赖是可选项. 缺失时脚本仍可运行, 但真实网页正文抽取质量有限.

## 限制

- 不执行 JavaScript, 不渲染 SPA.
- 不管理 Cookie/Session.
- 不处理登录后内容.
- 不解析 PDF, 不做图片 OCR.
- 不支持 FTP / 非 HTTP(S) 协议.
- 对强反爬网站, 客户端渲染页面, 复杂列表页, 商品页, 搜索结果页, 正文抽取可能低置信.
- 当 `extraction.confidence` 为 `low` 时, 调用者应谨慎使用结果.

## 下载输出示例

```json
{"path": "./downloads/logo.png", "url": "https://example.com/logo.png", "size": 12345, "content_type": "image/png"}
```
