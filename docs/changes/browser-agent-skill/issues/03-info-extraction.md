## 执行(Execution)

- [x] 已实现

## 要构建什么

信息提取操作: 在已有导航和交互能力之上, 增加 `extract_text(description, timeout=30.0)`, `get_page_structure(max_elements=500, timeout=30.0)` (按 D014: 返回 dict {url, title, elements, truncated}, elements 取自可访问性树, depth ≤ 4), `screenshot(path=None, full_page=True, timeout=30.0)` (按 D013: path 为 None 返回 PNG bytes; 非 None 写入文件). Agent 可提取文本, 获取页面结构, 截图.

此切片适合 AFK: 提取操作不改变页面状态, 仅读取和序列化已有信息, 无 API 歧义.

## 相关决策

D003, D006, D007, D008, D013, D014

## 允许范围

- `browser_agent/operations.py` — 追加 `extract_text()`, `get_page_structure()`, `screenshot()`
- 如需要, 新增 `browser_agent/_structure.py` 用于可访问性树解析
- `tests/test_extraction.py` — 提取操作测试

## 禁止范围

- 不实现 scroll, wait_for_element (留给 ISSUE-04)
- 不修改已有操作签名
- 不引入图像处理库 (Pillow 等) — screenshot 仅保存文件, 不做像素分析

## 验证入口

```bash
pytest tests/test_extraction.py -v
```

测试至少覆盖:
- extract_text 对含文本的元素返回非空文本
- extract_text 对不存在的元素返回 success=False
- get_page_structure 返回非空结构 (至少含页面标题或 body 区域)
- screenshot 保存文件到指定路径, 文件存在且非空

## 风险提示

- `get_page_structure()` 截断策略已由 D014 定义 (max_elements=500, depth ≤ 4). 若实际测试仍超 200KB 需停止.
- `extract_text()` 对动态内容 (SPA) 可能需额外等待; 依赖 Playwright 自动等待 + D006 超时

## 停止条件

- 如果 Playwright 可访问性树 API 无法按 D014 格式返回有效数据, 需讨论替代方案
- 如果 500 元素截断后 get_page_structure 返回体积仍 >200KB, 需调整 D014 参数
- 如果需要为截图引入新依赖或改变 D007 操作集合

## 适合 AFK 的原因

读取操作不改变系统状态, 接口明确. 全部依赖 Playwright 内置 API, 无需新设计决策.

## 验收标准

- [ ] `extract_text("main heading")` 返回页面主标题文本
- [ ] `get_page_structure()` 返回可解析的结构化数据
- [ ] `screenshot("test.png")` 生成有效 PNG 文件
- [ ] 三个操作在正常和异常场景下均返回 OperationResult

## 被阻塞于

- ISSUE-02: 元素交互 + 定位策略
