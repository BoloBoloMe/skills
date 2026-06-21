# UBIQUITOUS_LANGUAGE.md 格式

## 结构

```md
# {上下文名称}

{一两句话描述这个上下文是什么以及它为何存在.}

## 语言

**Order**:
{对该术语的一两句话描述}
_避免_: Purchase, transaction

**Invoice**:
交付后发送给客户的付款请求.
_避免_: Bill, payment request

**Customer**:
下订单的人或组织.
_避免_: Client, buyer, account
```

## 规则

- **要有立场.** 当同一概念有多个词时,选择最好的一个,并把其他词列为应避免的别名.
- **明确标出冲突.** 如果某个术语被含混使用,在"已标记歧义"中指出,并给出清晰的解决方式.
- **定义要紧凑.** 最多一两句话.定义它是什么,而不是它做什么.
- **展示关系.** 使用加粗的术语名称,并在明显时表达基数关系.
- **只包含此项目上下文特有的术语.** 通用编程概念(超时,错误类型,工具模式)不属于这里,即使项目大量使用它们.添加术语前先问:这是此上下文独有的概念,还是通用编程概念?只有前者属于这里.
- **在自然聚类出现时,用小标题分组术语.** 如果所有术语都属于一个单一内聚区域,扁平列表也可以.
- **写一段示例对话.** 用开发者和领域专家之间的对话,展示术语如何自然互动,并澄清相关概念之间的边界.

## 单上下文与多上下文仓库

**单上下文(大多数仓库):** `docs/language/UBIQUITOUS_LANGUAGE.md`.

**多个上下文:** `docs/language/UBIQUITOUS_LANGUAGE_MAP.md` 列出上下文,它们所在位置以及彼此关系:

```md
# 上下文地图

## 上下文

- [Ordering](./contexts/ordering.md) - 接收并跟踪客户订单
- [Billing](./contexts/billing.md) - 生成发票并处理付款
- [Fulfillment](./contexts/fulfillment.md) - 管理仓库拣货与发货

## 关系

- **Ordering -> Fulfillment**: Ordering 发出 `OrderPlaced` 事件;Fulfillment 消费它们以开始拣货
- **Fulfillment -> Billing**: Fulfillment 发出 `ShipmentDispatched` 事件;Billing 消费它们以生成发票
- **Ordering <-> Billing**: 共享 `CustomerId` 和 `Money` 类型
```

此技能会推断适用哪种结构:

- 如果存在 `docs/language/UBIQUITOUS_LANGUAGE_MAP.md`,读取它来查找上下文
- 如果只存在 `docs/language/UBIQUITOUS_LANGUAGE.md`,则为单上下文
- 如果两者都不存在,在解析第一个术语时惰性创建 `docs/language/UBIQUITOUS_LANGUAGE.md`

当存在多个上下文时,推断当前话题关联的是哪一个.如果不清楚,就询问.上下文名遵循项目领域语言: 项目领域语言是中文时使用中文上下文名; 代码或领域模型已使用英文术语时保持英文, 不强制翻译 `Ordering`,`Billing` 等既有术语.
