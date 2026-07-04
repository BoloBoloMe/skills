## 执行(Execution)

- [x] 已实现

## 要构建什么

补齐最后两个操作 `scroll(direction, amount, timeout=30.0)` (按 D012: direction ∈ {up,down}, amount 像素值) 和 `wait_for_element(description, state="visible", timeout=30.0)` (按 D015: state ∈ {attached,visible,hidden}), 并编写端到端集成测试, 验证全部 8 个操作在真实页面上的协作流程: 导航 → 等待元素出现 → 点击 → 输入文本 → 提取内容 → 截图 → 滚动 → 获取页面结构.

此切片适合 AFK: 最后两个操作逻辑简单, 集成测试是对已有能力的验证, 无需新设计决策.

## 相关决策

D006, D007, D008, D012, D015

## 允许范围

- `browser_agent/operations.py` — 追加 `scroll()`, `wait_for_element()`
- `tests/test_integration.py` — 端到端集成测试
- 其他测试文件的补充性修复 (如有)

## 禁止范围

- 不新增第 9 个操作
- 不引入新 Python 依赖
- 不修改公开 API 类型签名

## 验证入口

```bash
pytest tests/test_integration.py -v
```

集成测试至少覆盖一个完整流程:
1. navigate 到测试页面
2. wait_for_element 等待关键元素
3. click_element 点击按钮
4. type_text 输入文本
5. extract_text 提取结果
6. screenshot 截图
7. scroll 滚动页面
8. get_page_structure 获取最终结构

## 风险提示

- 集成测试依赖外部测试页面; 优先使用 Playwright `page.route()` mock 模拟页面, 避免外部网络依赖 (见 contract 测试策略约束)

## 停止条件

- 如果集成测试暴露 ISSUE-01/02/03 的实现缺陷需要重新打开已完成 issue

## 适合 AFK 的原因

剩余操作语义已由 D012/D015 明确, 集成测试是组合验证. 所有架构决策在 D001-D016 中覆盖.

## 验收标准

- [x] `scroll("down", 300)` 使页面垂直滚动 (test_scroll_actually_scrolls 验证 window.scrollY 从 0 → 300)
- [x] `wait_for_element("loading complete")` 等待指定元素出现后返回 success
- [x] 集成测试全部 8 步通过 (47/47 tests, 18.88s)
- [x] 全部 4 个 issue 的 `- [x] 已实现` 可标记为 `- [x] 已实现`

## 被阻塞于

- ISSUE-03: 信息提取操作
