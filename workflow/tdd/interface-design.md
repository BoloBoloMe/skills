# 面向可测试性的接口设计

好的接口会让测试变得自然：

1. **接收依赖，不要创建依赖**

   ```typescript
   // 易于测试
   function processOrder(order, paymentGateway) {}

   // 难以测试
   function processOrder(order) {
     const gateway = new StripeGateway();
   }
   ```

2. **返回结果，不要制造副作用**

   ```typescript
   // 易于测试
   function calculateDiscount(cart): Discount {}

   // 难以测试
   function applyDiscount(cart): void {
     cart.total -= discount;
   }
   ```

3. **小表面积**
   - 方法更少 = 需要的测试更少
   - 参数更少 = 测试搭建更简单
