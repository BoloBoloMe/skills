# ISSUE-04 Worker Note a1

## 实现摘要

ISSUE-04 补齐 `scroll` 和 `wait_for_element` 两个操作, 并编写集成测试.

## 变更文件

| 文件 | 变更 |
|------|------|
| `browser_agent/operations.py` | 追加 `scroll()`, `wait_for_element()` 两个函数 |
| `browser_agent/__init__.py` | 导出 `scroll`, `wait_for_element` |
| `tests/test_integration.py` | 新建, 14 个测试 (含 8 步集成 + 6 个 scroll 专项 + 5 个 wait 专项) |
| `docs/.../issues/04-utility-operations-integration.md` | 标记验收标准通过 |

## 实现细节

### scroll(direction, amount, timeout=30.0)

- D012: direction ∈ {"up", "down"}, amount 像素值
- 不合法 direction 抛 ValueError (编程错误)
- 使用 `page.evaluate(f"window.scrollBy(0, {delta})")` 实现
- D008: 操作失败返回 success=False, 不抛异常
- D011: 每次独立 Browser

### wait_for_element(description, state="visible", timeout=30.0)

- D015: state ∈ {"attached", "visible", "hidden"}, 默认 visible
- 不合法 state 抛 ValueError
- 使用 `_locator.py` 定位后调用 `locator.wait_for(state=...)`
- D008/D011 同上

### 集成测试

- 完整 8 步: navigate → wait_for_element → click_element → type_text → extract_text → screenshot → scroll → get_page_structure
- navigate 使用 page.route() mock URL 响应, 其他步骤使用 set_content()
- 每个步骤独立创建 Browser (D011)

## 测试结果

```
47 passed in 18.88s
```

33 个已有测试 + 14 个新增测试, 全部通过.

## 验收标准对照

- [x] `scroll("down", 300)` 使页面垂直滚动 — `test_scroll_actually_scrolls` 验证 window.scrollY 0→300
- [x] `wait_for_element(...)` 等待元素返回 success — `test_wait_for_element_visible/attached/hidden`
- [x] 集成测试全部 8 步通过 — `test_integration_full_8_step_flow`
- [x] 全部 4 个 issue 标记已实现

## 残余风险

- 无. 两个操作语义已由 D012/D015 明确, 实现无歧义.

## 下一步

全部 4 个 issue 已完成. browser-agent skill 具备完整 8 个操作, 47 个测试通过.
可进入文档/发布阶段.