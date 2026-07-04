## 执行(Execution)

- [x] 已实现

## 要构建什么

元素交互能力: 实现三级回退定位器 (`_locator.py`), 以及 `click_element(description, timeout=30.0)` 和 `type_text(description, text, timeout=30.0)` 两个操作. Agent 可以用自然语言描述目标元素 ("登录按钮", "搜索框"), skill 内部按 accessible name → 文本内容 → CSS selector 顺序定位.

此切片适合 AFK: 定位策略已决策 (D010), 操作语义已定义 (D002), 无新设计问题.

## 相关决策

D002, D003, D006, D007, D008, D009, D010

## 允许范围

- `browser_agent/_locator.py` — 三级回退定位策略
- `browser_agent/operations.py` — 追加 `click_element()`, `type_text()`
- `tests/test_interaction.py` — 交互操作测试

## 禁止范围

- 不实现提取类操作 (extract_text, get_page_structure, screenshot)
- 不修改 ISSUE-01 中已有的 navigate 实现 (除非修复 bug)
- 不引入 Playwright 以外的浏览器依赖

## 验证入口

```bash
pytest tests/test_interaction.py -v
```

测试至少覆盖:
- click_element 用语义描述定位按钮, 点击成功, 验证页面状态变化
- click_element 定位不到元素, 返回 success=False
- type_text 定位输入框, 输入文本, 验证输入框 value
- 三级回退: 同一元素分别用 accessible name / 文本 / CSS selector 应都能定位

## 风险提示

- 三级回退中的 CSS selector 兜底可能匹配到意外元素 (如 class 名恰好与描述相同), 需在定位器中日志记录使用的策略
- 动态加载页面可能需要额外等待; 等待逻辑是否在此切片实现取决于 D006 (默认 30s 超时在 Playwright 层的生效方式)

## 停止条件

- 如果 Playwright 的 `get_by_role` / `get_by_text` 语义与 D010 三级回退预期行为不一致
- 如果需要为 click/type 引入 D001-D010 未覆盖的新决策

## 适合 AFK 的原因

定位策略已决策, 操作行为已定义. 实现是确定性的: 封装 Playwright 定位 API, 按优先级回退, 返回统一 OperationResult.

## 验收标准

- [ ] `click_element("submit button")` 对含 `<button>Submit</button>` 的页面点击成功
- [ ] `type_text("search box", "hello")` 对含 `<input aria-label="search box">` 的页面输入成功
- [ ] 对不存在的元素描述, 两者均返回 `success=False` 且 error 描述明确
- [ ] 已有关联决策 (D002, D010) 的实际影响已更新到 DECISIONS.md

## 被阻塞于

- ISSUE-01: 浏览器生命周期 + 导航
