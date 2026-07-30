# 何时 mock

只在**系统边界** mock:

- 外部 API (payment, email 等)
- 数据库 (有时可以, 但优先用测试数据库)
- 时间或随机性
- 文件系统 (有时可以)

不要 mock:

- 你自己的类或模块
- 内部协作者
- 任何你控制的东西

## 为易于 mock 而设计

在系统边界上设计接口. 这些接口要容易 mock.

**1. 使用依赖注入**

把外部依赖作为参数传入. 不要在内部创建:

```typescript
// 容易 mock
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}

// 很难 mock
function processPayment(order) {
  const client = new StripeClient(process.env.STRIPE_KEY);
  return client.charge(order.total);
}
```

**2. 优先用 SDK 风格接口, 不用通用 fetcher**

为每个外部操作创建专门函数. 不要写一个带条件逻辑的通用函数:

```typescript
// 好: 每个函数都可以独立 mock
const api = {
  getUser: (id) => fetch(`/users/${id}`),
  getOrders: (userId) => fetch(`/users/${userId}/orders`),
  createOrder: (data) => fetch('/orders', { method: 'POST', body: data }),
};

// 坏: mock 里需要条件逻辑
const api = {
  fetch: (endpoint, options) => fetch(endpoint, options),
};
```

SDK 做法意味着:

- 每个 mock 返回一种具体形状
- 测试设置中没有条件逻辑
- 更容易看出测试调用哪些端点
- 每个端点各自保留类型安全
