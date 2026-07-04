# ISSUE-02 worker note a1

## 改动入口

| 文件 | 变更 |
|------|------|
| `browser_agent/_locator.py` | **新增** — 三级回退定位策略 |
| `browser_agent/operations.py` | 追加 `click_element()`, `type_text()` |
| `browser_agent/__init__.py` | 导出 `click_element`, `type_text` |
| `tests/test_interaction.py` | **新增** — 14 个测试 |
| `docs/.../DECISIONS.md` | 更新 D002, D010 实际影响 |

## 验证入口及结果

```bash
$ cd browser-agent && python -m pytest tests/ -v
18 passed (4 navigate + 14 interaction)
```

关键验证点:
- `click_element("submit button")` → `<button>Submit</button>` 点击成功 (通过 text 定位)
- `click_element("login button")` → `<button aria-label="login button">Login</button>` 点击成功 (通过 accessible name)
- `type_text("search box", "hello")` → `<input aria-label="search box">` 输入成功
- 不存在的元素 → 返回 `success=False`, error 含 "未找到匹配元素"
- 三级回退: `<button>Submit</button>` 分别用 "Submit"(accessible name), "Submit"(text), "button"(CSS) 均命中
- browser 启动失败 → 返回 `success=False`, 不抛异常

## 实现细节

### 定位策略 (`_locator.py`)

Level 1 accessible name:
- `get_by_role` 遍历 16 种常见 role (button/link/textbox/checkbox/...)
- `get_by_label` (aria-label / `<label>` 关联)
- `get_by_placeholder`
- 对含 role 后缀的描述 ("submit button") 自动提取潜在名称 (去 " button" 后缀) 提升匹配率

Level 2 text content:
- `get_by_text` 子串匹配 (Playwright 默认大小写不敏感)

Level 3 CSS selector:
- `page.locator(description)` 兜底

### 操作函数

`click_element` / `type_text` 均遵循 ISSUE-01 建立的模式:
- 每次调用创建独立 Browser 实例 (D011)
- try/except 包裹全部 Playwright 调用 (D008)
- 默认 30s 超时, 参数可覆盖 (D006)
- 返回 `OperationResult` (D003)

`type_text` 内部使用 `locator.fill()` 而非 `locator.type()` — fill 先清空再填入, 更适合表单输入场景.

## 风险/阻塞

- 无阻塞
- CSS selector 兜底可能误匹配: 如 description="submit button" 通过 CSS selector 匹配 `<button>` (descendant combinator 解析). 当前测试未触发此路径 (Level 1/2 先命中). 风险存在但属于 D010 已识别的已知风险, 按 contract 继续.

## 决策偏离

无偏离. 严格按 D010 三级回退实现, D008 失败不抛异常, D006 默认 30s 超时, D011 每次独立 Browser.