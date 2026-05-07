# 失败取证审核检查表

用于判断失败后是继续执行、请求人工判断，还是回到 HILP。

## 必须回答

1. 失败发生在哪个 execution unit？
2. 失败是否重复出现或属于同类失败？
3. 修复是否需要改 allowed_files 之外的文件？
4. 是否需要改变接口、验证契约、范围或蓝图假设？
5. 失败归因是 implementation bug、blueprint gap、design gap、environment、test issue 还是 unknown？
6. 推荐路由是继续 within scope、回 HILP phase-04、回 HILP phase-05，还是人工判断？

如果需要 HILP 决策，HILE 不得继续修复。
