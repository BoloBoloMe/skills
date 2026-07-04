# ISSUE-03 Worker Note (combined a1 + fix-a1)

## 改动入口

| 文件 | 变更 |
|------|------|
| `browser_agent/operations.py` | 追加 extract_text(), get_page_structure(), screenshot() |
| `browser_agent/_structure.py` | 新增 — JS DOM 提取 (替代不可用的 page.accessibility) |
| `browser_agent/result.py` | 追加 ExtractResult, StructureResult, ScreenshotResult |
| `browser_agent/__init__.py` | 导出 extract_text, get_page_structure, screenshot |
| `tests/test_extraction.py` | 新增 — 15 个测试 |

## 关键决策偏离

- D014 原定使用 `page.accessibility.snapshot()`, 但 Python Playwright sync API 无此接口.
  改用 `page.evaluate()` JS DOM 提取, 保持相同输出格式 {url, title, elements, truncated}.
  elements 每项含 role (aria-role / tagName) 和 name (aria-label / textContent), depth ≤ 4.

## 验证

```bash
cd browser-agent && PYTHONPATH=. python3 -m pytest tests/ -v
# 33 passed in 13.01s
```

## 风险

- JS DOM 提取与真实可访问性树存在语义差异 (不含隐式 role, 不含 CSS 生成的 content)
  但满足 Agent 理解页面结构的需求, 属于 D014 "可调整" 范围内.
