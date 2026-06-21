---
name: browse-web
description: 抓取, 搜索, 下载互联网资源, 并提取网页主要可读内容. 当我需要访问 URL, 搜索网页, 下载文件, 抽取文章正文, 清理网页噪声, 或将网页转为 Markdown/JSON 时使用.
---

# browse-web

轻量级 Web 抓取, 搜索, 下载工具. 默认从网页中提取主要可读内容, 并以 stdout JSON 返回.

本 skill 不执行 JavaScript, 不管理 Cookie/Session, 不处理登录后内容, 不解析 PDF, 不做 OCR. 无法可靠抽取时, 必须根据 `extraction.ok`, `extraction.confidence`, `extraction.warnings` 判断结果质量.

## 快速开始

```bash
# 提取网页主要正文, 默认模式
python scripts/browse_web.py browse https://example.com

# 保留旧行为: 整页 HTML 转 Markdown
python scripts/browse_web.py browse https://example.com --mode full

# 返回原始 HTML / 文本
python scripts/browse_web.py browse https://example.com --mode raw

# 搜索互联网
python scripts/browse_web.py search "python urllib" -n 5

# 下载文件到相对路径
python scripts/browse_web.py download https://example.com/logo.png ./downloads/logo.png
```

## 工作流

1. 优先用 `browse <url>` 获取网页主要正文.
2. 查看 `extraction` 字段判断可信度.
3. `confidence == low` 或出现 JavaScript/登录/正文过短 warning 时, 不要把结果当可靠事实来源.
4. 需要调试页面结构时用 `--mode raw`.
5. 需要旧版整页转换行为时用 `--mode full`.
6. 需要搜索入口时用 `search <query> -n <count>`.
7. 需要保存资源时用 `download <url> [path]`.

## 常用命令

### `browse <url>`

```bash
python scripts/browse_web.py browse https://example.com --mode extract --max-chars 12000
```

输出核心字段:

```json
{
  "url": "最终 URL",
  "title": "页面标题",
  "markdown": "提取后的 Markdown 正文",
  "resources": [],
  "metadata": {},
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

### `search <query> [-n 10]`

```bash
python scripts/browse_web.py search "python urllib" -n 5
```

### `download <url> [path]`

```bash
python scripts/browse_web.py download https://example.com/logo.png ./downloads/logo.png
```

## 结果质量规则

- 优先信任 `extraction.ok == true` 且 `confidence` 为 `high` 或 `medium` 的结果.
- `method == full_html_fallback` 表示返回整页转换结果, 可能包含导航, 页脚, 广告, 推荐链接等噪声.
- `confidence == low` 时, 应改用更可靠来源或浏览器渲染工具交叉验证.

## 进阶说明

参数清单, 抽取策略, 输出字段和限制见 [REFERENCE.md](REFERENCE.md).

## 依赖

- Python >= 3.9
- 可选增强依赖: `trafilatura`, `readability-lxml`, `markdownify`
