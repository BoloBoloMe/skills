# 好测试和坏测试

## 好测试

**集成式**: 通过真实接口测试. 不 mock 内部部件.

```typescript
// 好: 测试可观察行为
test("有效购物车可以结账", async () => {
  const cart = createCart();
  cart.add(product);
  const result = await checkout(cart, paymentMethod);
  expect(result.status).toBe("confirmed");
});
```

特征:

- 测试用户或调用方关心的行为
- 只使用公开 API
- 能扛住内部重构
- 描述做什么, 不描述怎么做
- 每个测试只有一个逻辑断言

## 坏测试

**实现细节测试**: 绑定内部结构.

```typescript
// 坏: 测试实现细节
test("checkout 调用 paymentService.process", async () => {
  const mockPayment = jest.mock(paymentService);
  await checkout(cart, payment);
  expect(mockPayment.process).toHaveBeenCalledWith(cart.total);
});
```

警示信号:

- mock 内部协作者
- 测试私有方法
- 断言调用次数或调用顺序
- 行为没变, 重构却弄坏测试
- 测试名称描述怎么做, 不描述做什么
- 绕过接口验证

```typescript
// 坏: 绕过接口验证
test("createUser 保存到数据库", async () => {
  await createUser({ name: "Alice" });
  const row = await db.query("SELECT * FROM users WHERE name = ?", ["Alice"]);
  expect(row).toBeDefined();
});

// 好: 通过接口验证
test("createUser 让调用方能读取用户", async () => {
  const user = await createUser({ name: "Alice" });
  const retrieved = await getUser(user.id);
  expect(retrieved.name).toBe("Alice");
});
```

**同义反复测试**: 预期值重述实现. 所以测试按构造通过.

```typescript
// 坏: 用实现同法重算预期值
test("calculateTotal 汇总行项目", () => {
  const items = [{ price: 10 }, { price: 5 }];
  const expected = items.reduce((sum, i) => sum + i.price, 0);
  expect(calculateTotal(items)).toBe(expected);
});

// 好: 预期值是已知字面量
test("calculateTotal 汇总行项目", () => {
  expect(calculateTotal([{ price: 10 }, { price: 5 }])).toBe(15);
});
```
