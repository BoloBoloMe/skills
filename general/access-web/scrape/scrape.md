# 只读抓取

轻量级 Web 抓取, 搜索, 下载. 默认提取网页主要可读内容, stdout JSON 返回.

不执行 JavaScript, 不管理 Cookie/Session, 不处理登录后内容, 不解析 PDF/OCR. 无法可靠抽取时, 根据 `extraction.ok`, `extraction.confidence`, `extraction.warnings` 判断结果质量.

## 快速开始

命令在 `access-web/` 目录下执行.

```bash
# 提取网页主要正文
python scrape/scripts/browse_web.py browse https://example.com

# 整页 HTML 转 Markdown
python scrape/scripts/browse_web.py browse https://example.com --mode full

# 返回原始 HTML / 文本
python scrape/scripts/browse_web.py browse https://example.com --mode raw

# 搜索互联网
python scrape/scripts/browse_web.py search "python urllib" -n 5

# 下载文件
python scrape/scripts/browse_web.py download https://example.com/logo.png ./downloads/logo.png
```

## 工作流

1. 优先用 `browse <url>` 获取网页主要正文.
2. 查看 `extraction` 字段判断可信度.
3. `confidence == low` 或出现 JavaScript/登录/正文过短 warning 时, 不把结果当可靠事实.
4. 调试页面结构用 `--mode raw`.
5. 整页转换用 `--mode full`.
6. 搜索用 `search <query> -n <count>`.
7. 保存资源用 `download <url> [path]`.

## 常用命令

### `browse <url>`

```bash
python scrape/scripts/browse_web.py browse https://example.com --mode extract --max-chars 12000
```

输出核心字段:

```json
{
  "url": "最终 URL",
  "title": "页面标题",
  "markdown": "提取后的 Markdown 正文",
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
python scrape/scripts/browse_web.py search "python urllib" -n 5
```

### `download <url> [path]`

```bash
python scrape/scripts/browse_web.py download https://example.com/logo.png ./downloads/logo.png
```

## 结果质量规则

- 信任 `extraction.ok == true` 且 `confidence` 为 `high` 或 `medium` 的结果.
- `method == full_html_fallback` 表示整页转换, 可能含导航/页脚/广告噪声.
- `confidence == low` → 改用交互浏览或交叉验证.

完成标准: 输出来源 URL, 抽取模式, 置信度, warnings. 低置信结果不作为可靠事实.

## 进阶

参数, 抽取策略, 输出字段见 [REFERENCE.md](REFERENCE.md).
