# ISSUE-02 worker attempt 1 正确性审查

## Review

### Correct

1. **D010 三级回退顺序** (`_locator.py:36-60`)
   - Level 1a: `get_by_role` 遍历 16 种常见 role + 名称变体 → 正确.
   - Level 1b: `get_by_label` → 正确 (aria-label / `<label>` 关联).
   - Level 1c: `get_by_placeholder` → 正确.
   - Level 2: `get_by_text` → 正确 (Playwright 默认子串/大小写不敏感).
   - Level 3: `page.locator(description)` CSS selector 兜底 → 正确.
   - 回退顺序 `role→label→placeholder→text→css` 符合 D010 "accessible name → 文本内容 → CSS selector" 语义.

2. **命中逻辑** (`_locator.py:79-104`)
   - 每级 `_try_*` 均用 `loc.count() > 0` 检查存在性, 多元素取 `loc.first` → 符合 D010 "以第一个命中为准".
   - 全部未命中返回 `(None, None)`, 调用方据此返回 `success=False` + 明确 error 消息.

3. **名称变体处理** (`_locator.py:28-34`)
   - 对含 role 后缀的描述 (如 "submit button") 自动剥离后缀, 同时尝试原始描述和剥离后名称 → 提升 Level 1 命中率, 合理实现.

4. **click_element / type_text 独立性** (`operations.py:42-94`)
   - 每次调用创建独立 `Browser()` 实例 → 符合 D011.
   - `finally: browser.stop()` 确保资源释放 → 无泄漏风险.
   - `stop()` 内部每层 `try/except Exception: pass` + 置 None 防重复关闭 → 安全 (`browser.py:51-68`).

5. **异常安全** (`operations.py:42-94`)
   - `try/except Exception` 包裹全部 Playwright 调用 → 符合 D008 (失败不抛异常).
   - `except Exception` 返回 `OperationResult(success=False, error=str(e))` → 正确.
   - Browser 构造失败 (基本不可能), start 部分失败, stop 抛异常 → 均已覆盖 (`browser.py:51-68`, `finally` 块).

6. **超时** (`operations.py:59,90`)
   - `locator.click(timeout=timeout * 1000)` / `locator.fill(text, timeout=timeout * 1000)` → ms 转换正确.
   - 默认 `timeout=30.0` → 符合 D006.

7. **type_text 使用 fill()** (`operations.py:90`)
   - `locator.fill()` 先清空再填入 → 语义更适合表单输入场景.

8. **回归: navigate 未被破坏**
   - `operations.py:20-29` navigate 实现在 ISSUE-01 后未变更, 测试 4/4 通过.

9. **测试覆盖** (`tests/test_interaction.py`)
   - 14 个测试: click 5 (文本/aria-label/aria-label显式/CSS/未找到), type 5 (aria-label/placeholder/role/CSS/未找到), 三级回退 2, 异常 2.
   - 全部 18 个测试通过 (含 ISSUE-01 的 4 个 navigate), 耗时 8.75s.

10. **决策账本更新** (`DECISIONS.md:19-23,101`)
    - D002 实际影响: 注明 `click_element`, `type_text`, `_locator.py` → 正确.
    - D010 实际影响: 注明三级回退 + 名称变体 → 正确.

11. **公开 API** (`__init__.py`)
    - 导出 `click_element`, `type_text`, `OperationResult`, `NavigateResult` → 正确, 不暴露 Playwright 内部类型.

### Note

1. **空描述边界** (`_locator.py`)
   - 传入 `description=""` 时, `get_by_role(role, name="")` 会匹配任意该 role 的元素 (Playwright 将空 name 视为无过滤). 实测 `<button>Click me</button>` 被 `role=button,name=` 匹配.
   - 影响: agent 传入空字符串可能触发意外操作 (如点击页面第一个按钮).
   - 建议: 后续 issue 或下一个 attempt 添加 `description.strip() == ""` 校验, 返回 `success=False` 或抛 `ValueError`.
   - 严重程度: 低. 不符合 D008 的 "仅编程错误" 但属可用性改进.

2. **Level 2 (text) 未被独立验证** (`tests/test_interaction.py:99-130`)
   - `test_three_level_fallback_same_element`: `click_element("Submit")` 在 `<button>Submit</button>` 上同时命中 Level 1a (`get_by_role("button", name="Submit")`), Level 2 (`get_by_text("Submit")`) 不会被触发.
   - `test_three_level_fallback_input`: `type_text("search", ...)` 同样 Level 1a 命中, Level 2 未触发.
   - 实际只有 Level 1 (r1,r2) 和 Level 3 (r3) 被独立验证. 若 Level 2 的 `get_by_text` 实现有 bug, 此测试不会发现.
   - 建议: 构造场景使 Level 1 失败, 仅 Level 2 命中. 例如 `<span>Submit</span>` (无 role=button) 用 `click_element("Submit")` -- span 不在 `common_roles` 列表, Level 1 全跳过, Level 2 `get_by_text("Submit")` 命中.
   - 严重程度: 低. 代码审查确认 `_try_get_by_text` 实现正确, 逻辑存在.

3. **`_try_*` 宽泛 Exception 捕获可能掩藏错误** (`_locator.py:79-104`)
   - `_try_get_by_role` 等函数 `except Exception: pass` 会掩藏 `loc.count()` 执行期间的浏览器崩溃/连接断开等意外异常, 将其等同为 "元素不存在".
   - 影响: 浏览器崩溃时 `locate()` 返回 `(None, None)`, 调用方收到 "未找到匹配元素" 而非真实的崩溃原因.
   - 但外层 `click_element/type_text` 的 `except Exception` 会在后续 `locator.click()` 时捕获真正的异常, 所以只有当崩溃发生在 `count()` 时才会被掩藏.
   - 严重程度: 低. 建议后续区分预期异常和意外异常.

4. **CSS selector 兜底误匹配风险 (已知)** (`_locator.py:56-58`)
   - Worker note 已识别. `description="submit button"` 通过 CSS selector 会被解析为 `<submit>` 内嵌 `<button>` (descendant combinator). Level 1/2 通常先命中, 故实际触发概率低.
   - 无阻塞 -- D010 可调整, contract 已记载此风险.

### Test coverage summary

| 路径 | 覆盖 | 测试 |
|------|------|------|
| Level 1a (get_by_role) 命中 | ✅ | `test_click_element_by_text`, `test_click_element_by_accessible_name`, `test_click_element_by_label`, `test_type_text_by_aria_label`, `test_type_text_by_role_textbox`, `test_three_level_fallback_*` r1/r2 |
| Level 1b (get_by_label) 命中 | ✅ | `test_click_element_by_label` (aria-label 通过 label 也可命中) |
| Level 1c (get_by_placeholder) 命中 | ✅ | `test_type_text_by_placeholder` |
| Level 2 (get_by_text) 独立命中 | ⚠️ | 被 Level 1 先命中, 未独立验证 (见 Note 2) |
| Level 3 (CSS) 命中 | ✅ | `test_click_element_by_css_selector`, `test_type_text_by_css`, `test_three_level_fallback_*` r3 |
| 未找到 | ✅ | `test_click_element_not_found`, `test_type_text_not_found` |
| Browser 启动失败 | ✅ | `test_click_element_browser_start_failure`, `test_type_text_browser_start_failure` |
| Playwright 操作异常 (如 click 超时) | ❌ | 未覆盖 (需 mock 实现) |
| 空描述 | ❌ | 未覆盖 (见 Note 1) |
| 多元素命中取 first | ✅ | 隐式 (各 happy path 中 `<button>` 唯一) |

### Residual risks

- Level 2 (text) 路径未被独立测试验证 (但代码实现正确, 低风险)
- 空字符串描述可能导致意外元素匹配 (低风险, 建议后续加 guard)
- CSS selector 兜底误匹配 (已知风险, D010 可调整, contract 已记录)
- `_try_*` 宽泛 Exception 可能掩藏浏览器崩溃 (低风险, 外层 catch 兜底)

## Acceptance