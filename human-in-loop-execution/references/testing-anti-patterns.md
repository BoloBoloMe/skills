# 测试反模式

## 适用时机

编写或修改测试、准备引入 mock、测试工具、测试辅助方法，或测试失败原因不清时使用。

## 输入契约

- HILP execution handoff asset_ref。
- 当前测试目标与目标行为。
- 被测代码路径、依赖边界和禁止越界项。

## 执行规则

测试必须验证真实行为，而不是 mock 的存在。五类反模式必须逐项排除：

1. 测试 mock 行为。违规信号：断言 `*-mock`、只验证 mock 被调用。错误原因：测试的是替身。修复方式：断言用户可见行为或真实输出。Gate function：问“这是否仍能在真实依赖下证明行为”。
2. 向生产类加入测试专用方法。违规信号：方法只被测试调用。错误原因：污染生产 API。修复方式：放入测试工具或通过公开行为验证。Gate function：问“生产代码是否真的需要这个方法”。
3. 不理解依赖就 mock。违规信号：为了快而 mock 高层方法。错误原因：隐藏副作用。修复方式：先读依赖，保留测试需要的真实副作用，只 mock 外部慢边界。Gate function：列出真实方法的输入、输出、副作用。
4. 不完整 mock。违规信号：只填当前断言字段。错误原因：真实结构假设被隐藏。修复方式：按真实 API 或样例构造完整结构。Gate function：对照真实 schema。
5. 把集成测试当附加事项。违规信号：实现完成后才说等待集成测试。错误原因：测试是实现的一部分。修复方式：按 TDD 或执行交接替代验证先建立证据。

mock 行为测试 before / after：

```typescript
// before：测试替身存在，不测试真实行为。
test('renders sidebar', () => {
  renderPageWithMockSidebar();
  expect(screen.getByTestId('sidebar-mock')).toBeInTheDocument();
});

// after：验证用户可观察行为。
test('shows navigation links', () => {
  renderPage();
  expect(screen.getByRole('link', { name: 'Settings' })).toBeVisible();
});
```

测试专用生产方法 before / after：

```typescript
// before：生产类暴露只给测试清理用的方法。
class Session {
  destroyForTestOnly() { cleanupTempState(this.id); }
}

// after：测试辅助放在测试工具里，生产 API 不扩张。
function cleanupSessionFixture(session: Session) {
  cleanupTempState(session.id);
}
```

after 版本通过真实页面行为或测试工具边界验证目标，不要求生产代码增加蓝图外 API。

## 禁止事项

- 不得断言 mock 元素或 mock 调用本身来替代行为验证。
- 不得向生产类加入仅测试使用的方法。
- 不得在不了解依赖副作用时 mock 高层方法。
- 不得用不完整 mock 制造通过。
- 不得把集成测试视为实现后的附加事项。

## 输出契约

输出测试目标、真实行为断言、mock 边界说明、风险和验证命令。发现测试设计会改变执行范围时，停止并回到 HILP 重审。

## 检查清单

- [ ] 测试断言真实行为。
- [ ] mock 副作用已理解。
- [ ] 没有测试专用生产方法。
- [ ] mock 数据结构完整。
- [ ] 集成证据未被后置。
