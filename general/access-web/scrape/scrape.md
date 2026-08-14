# 只读抓取

轻量级 Web 抓取, 搜索, 下载. 默认提取网页主要可读内容, stdout JSON 返回.

不执行 JavaScript, 不处理登录后内容; 完整能力限制清单见 [REFERENCE.md](REFERENCE.md). 无法可靠抽取时, 根据 `extraction.ok`, `extraction.confidence`, `extraction.warnings` 判断结果质量.

## 工作流

1. 优先用 `browse <url>` 获取网页主要正文.
2. 查看 `extraction` 字段判断可信度, 按下方 结果质量规则 处置.
3. 调试页面结构用 `--mode raw`.
4. 整页转换用 `--mode full`.
5. 搜索用 `search <query> -n <count>`.
6. 保存资源用 `download <url> [path]`.

## 常用命令

命令在 `access-web/` 目录下执行.

### `browse <url>`

```bash
uv run python scrape/scripts/scrape.py browse https://example.com --mode extract --max-chars 12000
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
uv run python scrape/scripts/scrape.py search "python urllib" -n 5
```

成功返回结果 list. DuckDuckGo 与 Brave 两引擎都无果时返回 `{"results": [], "warnings": ["<各引擎诊断>"]}` 而非 list, 消费前先判断返回类型.

### `download <url> [path]`

```bash
uv run python scrape/scripts/scrape.py download https://example.com/logo.png ./downloads/logo.png
```

成功输出含 `path`, `url`, `size`, `content_type`, `status`, `path` 恒为绝对路径. `status >= 400` 时不写盘, 返回 `{"status": http码, "error": ..., "url": ...}`. 下载流式写盘, 超 200MiB 中止并删除半成品文件 (显式路径只删同目录 `<basename>.<随机>.part` 临时文件, 既有目标文件内容保留), 返回 error.

## 错误与退出码

- 正常运行路径 exit 0, 运行错误以 stdout JSON 表达: `{"status": 0, "error": "..."}`. Python < 3.9 时启动即 `sys.exit(1)`, 仅 argparse 用法错误 exit 2.
- 响应体超 20MiB 截断, warning `response truncated at {N} bytes` 合并进 `extraction.warnings`.
- 重定向最多 10 跳, 超限返回 `{"status": 0, "error": "redirect limit exceeded (10)"}`; 跨域重定向自动剥离 authorization/cookie 等敏感头.
- 默认拦截私网地址 (SSRF 防护); 可信内网/测试场景可设环境变量 `SCRAPE_ALLOW_PRIVATE_HOSTS=1` 关闭.

## 结果质量规则

- 信任 `extraction.ok == true` 且 `confidence` 为 `high` 或 `medium` 的结果.
- `method == full_html_fallback` 表示整页转换, 可能含导航/页脚/广告噪声.
- `confidence == low` → 不把结果当可靠事实, 改用交互浏览或交叉验证.

完成标准: 输出来源 URL, 抽取模式, 置信度, warnings. 低置信结果不作为可靠事实.

## 进阶

参数, 抽取策略, 输出字段见 [REFERENCE.md](REFERENCE.md).
