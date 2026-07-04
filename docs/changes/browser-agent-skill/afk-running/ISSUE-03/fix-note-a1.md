# ISSUE-03: get_page_structure 修复

## 问题
`page.accessibility.snapshot()` 在 Python Playwright sync API 中不存在, 导致 6 个 get_page_structure 测试全败.

## 修复

### `_structure.py` — 重写为 JS DOM 提取
- 移除 `parse_snapshot()` (依赖不存在的 accessibility API)
- 新增 `extract_structure(page, max_depth, max_elements)`, 通过 `page.evaluate()` 执行内联 JS
- JS 代码从 `document.body` 递归遍历 DOM, 提取 role (aria-role / tagName) 和 name (aria-label / textContent 前 50 字符)
- 深度 ≤ 4 (D014), 元素数 ≤ max_elements, 超限截断
- 返回 `(elements, truncated)` 元组

### `operations.py` — 适配新接口
- 导入从 `parse_snapshot` 改为 `extract_structure`
- `get_page_structure()` 直接传 `page` 对象调用 `extract_structure(page, max_elements=max_elements)`
- 返回格式不变: `{url, title, elements, truncated}`

## 验证
```bash
cd browser-agent && PYTHONPATH=. python3 -m pytest tests/test_extraction.py -v
# 15 passed in 4.39s
```
extract_text/screenshot 测试未受影响.

## 变更文件
- `browser-agent/browser_agent/_structure.py` — 重写
- `browser-agent/browser_agent/operations.py` — 3 处小改 (import, docstring, 调用行)