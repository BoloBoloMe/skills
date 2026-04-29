# 测试驱动开发

## 适用时机

实现新功能、修复 bug、重构行为或改变外部可观察行为前使用。执行交接明确不要求测试的纯文档或配置变更，可只运行执行交接列出的验证命令。

## 输入契约

- HILP execution handoff asset_ref。
- 当前任务的文件范围、验收标准和禁止越界项。
- 可运行的测试命令或执行交接允许的替代验证命令。
- 若无法写测试，必须有用户许可或执行交接明确允许的替代验证。

## 执行规则

铁律：没有先失败的测试，不写生产代码。违反时删除并从测试重来，不保留为参考，不边看边改。

RED-GREEN-REFACTOR：
1. RED：写一个最小失败测试，表达目标行为。
2. RED 验证：运行测试并确认失败原因是目标行为缺失，而不是拼写、导入或环境错误。
3. GREEN：写最小实现，只满足测试，不加入蓝图外能力。
4. GREEN 验证：运行同一测试和相关回归测试，确认输出干净。
5. REFACTOR：只有测试保持通过时才清理命名、重复和结构；不改变行为。

好测试 / 坏测试 TypeScript 风格对照：

```typescript
// 好：断言真实行为。
test('rejects empty name', () => {
  const result = validateName('');
  expect(result).toEqual({ ok: false, error: 'name required' });
});

// 坏：只断言 mock 被调用，没有证明真实行为。
test('calls validator mock', () => {
  const validator = vi.fn();
  saveName('', validator);
  expect(validator).toHaveBeenCalled();
});
```

最小 GREEN / 过度实现对照：

```typescript
// 最小 GREEN：只满足当前失败测试。
function validateName(value: string) {
  if (value === '') return { ok: false, error: 'name required' };
  return { ok: true };
}

// 过度实现：加入蓝图外配置和格式策略，超出当前测试与执行交接范围。
function validateName(value: string, options?: { locale?: string; policy?: string }) {
  // 蓝图未批准的扩展能力不得在 GREEN 阶段加入。
}
```

常见借口表：

| 借口 | 处理 |
|---|---|
| 太简单 | 简单代码也会坏，仍先写失败测试。 |
| 稍后补测试 | 这不是 TDD；删除并从测试重来。 |
| 手工测过 | 手工测试不能替代可重复证据。 |
| 赶时间 | 猜测实现会制造返工，仍按 RED-GREEN-REFACTOR。 |
| 测试难写 | 先写期望 API；若需要改设计，回到 HILP 重审。 |

## 禁止事项

- 不得先写生产代码再补测试。
- 不得让测试一开始就通过。
- 不得测试 mock 自身行为。
- 不得为了测试向生产类加入测试专用方法。
- 不得在发现蓝图缺口时用 TDD 自行设计新范围。

## 输出契约

输出 RED 命令、失败摘要、GREEN 命令、通过摘要、回归命令和未覆盖项。若使用替代验证，说明用户许可或执行交接依据、命令、退出码和输出摘要。

## 检查清单

- [ ] 失败测试先出现。
- [ ] 失败原因正确。
- [ ] 最小实现通过测试。
- [ ] 回归命令已运行。
- [ ] 未越过 HILP 执行交接范围。
