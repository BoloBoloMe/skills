# 何时 Mock（模拟）

只在**系统边界** mock（模拟）：

- 外部 API（payment、email 等）
- 数据库（有时——优先使用测试 DB）
- 时间/随机性
- 文件系统（有时）

不要 mock（模拟）：

- 你自己的类/模块（classes/modules）
- 内部协作者
- 任何你控制的东西

## 面向可 Mock（模拟）性的设计

在系统边界，设计易于 mock（模拟）的接口：

**1. 使用依赖注入**

传入外部依赖，而不是在内部创建：

```typescript
// 易于 mock
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}

// 难以 mock
function processPayment(order) {
  const client = new StripeClient(process.env.STRIPE_KEY);
  return client.charge(order.total);
}
```

**2. 相比通用获取器（fetcher），更偏好 SDK 风格接口**

为每个外部操作创建具体函数，而不是创建一个带条件逻辑的通用函数：

```typescript
// 好：每个函数都可以独立 mock（模拟）
const api = {
  getUser: (id) => fetch(`/users/${id}`),
  getOrders: (userId) => fetch(`/users/${userId}/orders`),
  createOrder: (data) => fetch('/orders', { method: 'POST', body: data }),
};

// 坏：mock（模拟）时需要在 mock 内部写条件逻辑
const api = {
  fetch: (endpoint, options) => fetch(endpoint, options),
};
```

SDK 方式意味着：
- 每个 mock 返回一种具体形状
- 测试搭建中没有条件逻辑
- 更容易看出一个测试覆盖了哪些端点（endpoints）
- 每个端点（endpoint）都有类型安全
