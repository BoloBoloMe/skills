# 个人代码风格提炼记录

## 文档定位

本文记录从 `cz-risk-discern` 代码库中观察到的个人代码风格.

本文不是代码规范, 也不是提供给 AI 的编码指导文件. 它只回答以下问题:

- 当前代码体现了哪些稳定的个人选择
- 哪些特点只是框架或工具带来的结果
- 哪些特点正在演化, 尚未成为稳定风格
- 哪些局部现象不应被过度概括

## 探索范围

本轮只读分析覆盖:

- Server 主代码 412 个 Java 文件, 其中 80 个为 MyBatis 生成文件
- Server 测试 106 个 Java 文件
- Groovy 脚本 40 个
- SDK 主代码 25 个 Java 文件
- 2025-04 至 2026-07 的代表性 Git 历史
- Checkstyle, ArchUnit, Maven 配置, benchmark 和故障分析文档

以下内容未作为个人风格的主要证据:

- MyBatis Generator 生成代码
- `Blake2b.java` 等移植或第三方算法实现
- 仅由 Spring/MyBatis/Lombok 语义决定的固定写法
- 单个实验文件或孤立反例

## 核心画像

整体风格可以概括为:

> 业务语义和运行时行为优先的实用型分层风格. 重视明确边界, 可观测性, 性能和故障隔离, 但不追求形式上的绝对整洁, 纯函数或全面抽象.

这套风格的中心不是格式一致性, 而是让业务流程可定位, 运行结果可解释, 性能边界可控制, 故障影响可限制.

## 我的代码风格不是什么样的

从反面看, 这套风格不适合被归纳为以下几类.

### 1. 不是洁净架构或洋葱架构原教旨风格

代码有清晰分层, 但分层服务于职责可辨识和依赖可控, 不是为了满足某套架构图而把所有对象都拆进接口, 用例层, 端口层和适配器层.

Service 直接编排 Repository, Component 和 Integration 很常见. Repository 有接口, 但 Service 通常不是接口加实现类的成套结构. 核心模板也没有被拆成大量微型 use case 或 pipeline step.

- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/service/EventReceiveService.java:52 ~167`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/components/strategy/StrategyTemplate.java:41 ~120`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/repository/impl/StrategyRepositoryImpl.java:37 ~525`

因此, 这不是追求架构形式完备的风格. 边界重要, 但边界需要有业务或演化理由.

### 2. 不是小类, 短方法和全面拆分洁癖

代码并不把类长度或方法长度本身当作首要问题. `StrategyTemplate`, `CumulativelyVariableTemplate`, `StrategyRepositoryImpl` 和复杂脚本都可以很长, 只要主流程仍能按业务阶段阅读, 状态集中管理也没有失控.

这种风格会接受一个稳定模板集中承担编排, 并通过 guard clause, 私有方法, 注释分段和具名中间变量维持可读性. 它不是每遇到十几行逻辑就提取类, 也不是为了让每个方法都短而牺牲局部上下文.

- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/components/strategy/StrategyTemplate.java:83 ~172`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/components/cumulative/CumulativelyVariableTemplate.java:91 ~220`
- `cz-risk-discern-server/src/test/groovy/PeriodicScript/AccountRiskScoreScript.groovy:38 ~272`

### 3. 不是纯函数式或全面不可变风格

代码会使用 stream, record 和 sealed interface, 但没有把函数式写法当作统一审美. 热路径, 需要索引, 需要提前返回, 需要写入上下文或需要异常隔离时, 普通循环和可变状态更常见.

`EventReceiveContext` 是典型的请求内可变状态容器, 同时承载输入, 输出, 缓存, trace 和回调 Future. DTO 也大量使用 Lombok setter 和链式构造. record 更多用于值对象, key 和局部载体, 而不是替代全部数据模型.

- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/model/EventReceiveContext.java:24 ~118`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/model/StrategyAddParameters.java:13 ~74`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/model/OperationResult.java:14 ~74`

所以, 这不是 `能 immutable 就 immutable, 能 stream 就 stream` 的风格. 可变性只要被限制在清楚的生命周期和边界内, 就是可接受工具.

### 4. 不是模式优先或抽象优先风格

代码里有 Builder, Template, Repository, Strategy 等命名, 但这些模式多半来自真实使用场景, 不是为了凑设计模式清单.

没有稳定变化点的地方不会机械引入接口. 有多实现, 运行时扩展或跨边界隔离需求时才会抽象, 例如累计变量, 函数调用, 表达式求值和 Repository. 反过来, 后台 Service, 复制策略用例和事件接收流程更偏直接编排.

- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/components/cumulative/CumulativelyVariable.java:14 ~43`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/components/cumulative/CumulativelyVariableTemplate.java:275 ~300`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/service/StrategyCopyWorkerService.java:42 ~304`

这说明抽象是为了隔离变化和降低调用方认知负担, 不是为了把代码变得 `更像框架`.

### 5. 不是格式, import 和语法统一驱动的风格

仓库里同时存在通配符 import 和逐项 import, 中文日志和英文日志, `@Accessors(chain = true)` 和少量 `fluent = true`, 早期 `assert`/`System.out` 测试和近期 Mockito/AssertJ/JUnit 5 风格测试.

这些不统一不是一个独立目标, 但也不是当前风格的核心关注点. 代码治理更优先处理分层依赖, 运行行为, 性能和故障边界, 而不是优先追求全仓库表面一致.

- `cz-risk-discern-server/checkstyle/import-control.xml:6 ~25`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/components/constant/impl/ConstantValueImpl.java:60 ~61`
- `cz-risk-discern-server/src/test/java/com/changzhi/platform/risk/discern/components/cumulative/impl/ContinuousSetVariableTest.java:17 ~80`
- `cz-risk-discern-server/src/test/java/com/changzhi/platform/risk/discern/service/StrategyCopyWorkerServiceTest.java:45 ~135`

因此, 不应把这套风格理解成 formatter, import sorter 或单一测试模板驱动的代码风格.

### 6. 不是全局追新或全模块同构风格

Server 模块积极使用 Java 21 特性, SDK 模块却保留 Java 8 兼容. 同一仓库内, 语法选择服从模块运行边界和发布约束, 而不是服从 `新语法更好` 或 `所有模块必须一致`.

- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/model/TimeSlice.java:17 ~235`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/utils/ExecutorUtil.java:18 ~27`
- `cz-risk-discern-sdk/pom.xml:15 ~30`
- `cz-risk-discern-sdk/src/main/java/com/changzhi/platform/risk/discern/api/RiskDiscernApiBuilder.java:20 ~139`

更准确地说, 新能力会在能带来表达力, 性能或并发收益时使用, 但不会突破兼容性边界.

### 7. 不是只写 happy path 的演示型代码

虽然历史测试里有探索性代码, 但生产代码本身明显关心失败分类, 降级, 超时, 线程池上限, trace, 回调隔离和异步边界. 这不是只把主流程跑通的样例式写法.

典型代码会在业务入口处理参数错误, 在策略和回调边界吞掉局部失败, 在 SDK 里区分参数错误, 网络错误, 服务端错误和未知异常, 并提供不同降级策略.

- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/service/EventReceiveService.java:52 ~167`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/components/strategy/StrategyTemplate.java:179 ~218`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/integration/executors/ThreadPoolConfig.java:19 ~145`
- `cz-risk-discern-sdk/src/main/java/com/changzhi/platform/risk/discern/api/impl/ProtectedRiskDiscernApi.java:72 ~218`

这套风格的 `实用` 不是简陋, 而是把线上可运行, 可定位和可降级放在形式整洁之前.

## 高置信度特征

### 1. 职责分层明确, 但不追求洁净架构教条

Controller 极薄, 主要负责 HTTP 协议接入, 参数校验和委托. Service 负责用例编排. Components 承担策略执行, 累计变量和函数调用等核心算法. Repository 隔离数据库访问. Integration 封装外部系统和基础设施.

代表证据:

- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/controller/backend/BackendStrategyController.java:12 ~69`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/service/EventReceiveService.java:31 ~279`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/components/strategy/StrategyTemplate.java:41 ~646`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/repository/StrategyRepository.java:8 ~68`

这种分层后来被 Checkstyle 和 ArchUnit 固化, 但门禁只覆盖关键依赖方向, 并明确保留历史例外. 例如暂不禁止 `repository -> components`, `components.signal` 也被排除在部分规则之外.

这体现的是渐进治理, 不是为了理论纯度一次性重构现有系统.

- `cz-risk-discern-server/checkstyle/import-control.xml:6 ~25`
- `cz-risk-discern-server/src/test/java/com/changzhi/platform/risk/discern/architecture/LayerArchitectureTest.java:35 ~135`

### 2. 只在存在真实多态或稳定边界时抽象

Repository 有接口, Service 通常直接使用具体类. 累计变量, 函数调用和表达式求值等存在多个实现或运行时扩展需求时, 才引入接口.

累计变量通过 Spring 集合注入所有实现, 再按时间切片类型和变量类型构建字典. 这是典型的 `稳定模板编排 + 小接口扩展`.

- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/components/cumulative/CumulativelyVariable.java:14 ~43`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/components/cumulative/CumulativelyVariableTemplate.java:36 ~52`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/components/cumulative/CumulativelyVariableTemplate.java:275 ~300`

反过来, 策略执行没有被机械拆成大量流水线对象. `StrategyTemplate` 集中处理批次执行, 条件求值, 结果归并和回调.

这说明抽象服务于真实变化点, 而不是服务于类长度或模式数量.

### 3. 控制流偏好线性叙事和 guard clause

常见方法结构是:

1. 校验输入和状态
2. 不满足条件时提前返回
3. 准备上下文或中间数据
4. 执行核心操作
5. 汇总结果或记录 trace

简单失败分支经常写成单行 `if (...) return`. 复杂方法则通过若干有业务名称的私有方法维持主流程可读性.

- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/service/EventReceiveService.java:52 ~167`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/service/StrategyMutationService.java:47 ~126`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/components/cumulative/CumulativelyVariableTemplate.java:232 ~270`

Stream 主要用于映射, 分组和汇总. 有状态逻辑, 热路径, 索引操作或需要提前退出时使用普通循环.

因此整体不是纯函数式风格, 而是根据控制流语义选择 stream 或循环.

### 4. 使用可变 DTO 和不可变值对象的双轨数据模型

请求, 响应和运行配置大量使用 `@Data + @Accessors(chain = true)`. 这类对象强调低样板代码, 链式构造和业务编排效率.

- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/model/StrategyAddParameters.java:13 ~74`

明确的值对象, 内部 key, 计算结果和局部数据载体则倾向使用 `record`.

- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/model/OperationResult.java:14 ~74`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/service/StrategyCopyWorkerService.java:301 ~304`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/components/strategy/StrategyTemplate.java:641 ~652`

一次请求的运行状态被集中放入可变 `EventReceiveContext`. 它同时承载输入, 输出, 请求内缓存和埋点记录, 并使用并发集合保护并行写入.

- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/model/EventReceiveContext.java:24 ~118`

这说明作者接受边界明确的可变状态, 不追求全面不可变.

### 5. 积极使用现代 Java, 但由模块和场景驱动

Server 使用 Java 21 能力, 包括:

- `record`
- sealed interface
- switch expression
- 模式匹配
- `var`
- 虚拟线程
- 新集合预分配 API

- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/model/TimeSlice.java:17 ~235`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/components/strategy/StrategyTemplate.java:136 ~172`

这些特性通常用于减少样板, 表达封闭类型, 简化局部类型或优化关键路径.

SDK 则长期保持 Java 8 兼容, 因此仍使用传统 switch, 显式类型和 Java 8 集合方式.

- `cz-risk-discern-sdk/pom.xml:15 ~30`

所以现代语法是兼容边界内的工具选择, 不能外推为所有模块必须统一使用.

### 6. 性能和并发属于设计内容

核心代码显式区分:

- CPU 密集型和 IO 密集型任务
- 串行和并行执行
- 平台线程池和虚拟线程
- 同步完成和脱离响应边界的异步操作
- 超时, 并发上限, 拒绝策略和优雅关闭

- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/integration/executors/ThreadPoolConfig.java:19 ~145`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/components/cumulative/CumulativelyVariableTemplate.java:91 ~220`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/components/strategy/StrategyTemplate.java:83 ~172`

热路径中可以看到预分配集合, 惰性条件计算, 单次结果缓存, 有界 Caffeine 缓存, MD5 长键和 MethodHandle 快路径.

- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/components/strategy/StrategyTemplate.java:226 ~348`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/utils/spel/MethodResolverFastPaths.java:18 ~260`

同时存在 benchmark, JFR 和线程栈驱动的性能判断. 性能结论倾向建立证据链, 而不是仅靠直觉.

- `benchmark/cat-benchmark-report-20260527.md:1 ~120`
- `docs/debug_report/20260714-大量实体清单写操作引发卡死故障分析/根因分析报告.md:1 ~180`

### 7. 失败处理强调分类和隔离

输入错误通常在 Service 边界转成结构化 `OperationResult`. 单策略, 单批次项和回调异常往往被限制在各自边界内, 避免无关任务一起失败.

- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/model/OperationResult.java:24 ~74`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/service/BackendStrategyService.java:54 ~85`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/components/strategy/StrategyTemplate.java:179 ~218`

SDK 将参数错误, 网络错误, 服务端错误和未知异常分类, 并通过具名策略表达可用性优先, 安全性优先和保守降级.

- `cz-risk-discern-sdk/src/main/java/com/changzhi/platform/risk/discern/api/model/FallbackPolicy.java:68 ~141`
- `cz-risk-discern-sdk/src/main/java/com/changzhi/platform/risk/discern/api/impl/ProtectedRiskDiscernApi.java:72 ~218`

高频业务异常还会关闭堆栈生成, 以异常信息换取性能和更低分配成本.

- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/exception/NotWritableStackTraceException.java:10 ~35`

失败边界并非全局一致. 批量事件会先校验全部输入, 任一失败时整批拒绝. 部分异步累计变量写入则脱离响应完成边界. 这说明失败策略会按业务语义选择, 而不是套用单一规则.

### 8. API 偏好便利入口和业务化默认值

常见 API 设计手段包括:

- 默认方法委托到完整重载
- fluent Builder
- 链式 DTO
- 静态策略工厂
- 单次配置覆盖客户端默认配置
- 明确的业务默认值

- `cz-risk-discern-sdk/src/main/java/com/changzhi/platform/risk/discern/api/RiskDiscernApi.java:8 ~30`
- `cz-risk-discern-sdk/src/main/java/com/changzhi/platform/risk/discern/api/RiskDiscernApiBuilder.java:20 ~139`
- `cz-risk-discern-sdk/src/main/java/com/changzhi/platform/risk/discern/api/model/FallbackPolicy.java:112 ~141`

API 更重视调用方能否直接表达业务意图, 而不是追求最少的方法或配置项.

### 9. 命名重业务语义, 接受较长名称

典型名称包括:

- `CumulativelyVariableReadWriteConfig`
- `StrategyConditionalExpressionEvaluator`
- `LocalProcessCumulativelyVariableUpdateSignal`
- `RecentUserBlacklistCardGameAccountSyncScript`

DTO 后缀存在较稳定的角色区分:

- 输入使用 `*Parameters`
- 输出使用 `*Result`
- 内部转换参数使用 `*Params`
- 运行配置使用 `*Config`
- 实现类使用 `*Impl`

这种风格优先保证领域角色可辨识, 即使名称较长.

部分英文存在不自然或历史拼写, 如 `CumulativelyVariable`, `margeOutput`, `ThrowableWarp`. 这些名称长期保留, 说明作者不会仅为英文形式统一而大范围改名.

### 10. 注释主要解释业务意图, 执行顺序和取舍

生产代码中中文 Javadoc 和行内注释密度较高. 复杂方法常使用步骤编号, 或解释为什么选择串行/并行, 为什么忽略某类引用, 某个状态在业务上代表什么.

- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/components/periodic/PeriodicScriptTaskScheduler.java:33 ~365`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/service/StrategyCopyWorkerService.java:100 ~208`

注释更偏向意图和上下文, 但历史代码中也存在复述操作步骤的注释. 近期代码对边界和取舍的解释明显增加.

### 11. 可观测性与业务执行上下文紧密结合

TraceId, 执行耗时, 条件结果, 访问过的变量, 策略命中和回调信息都被纳入请求上下文.

并行任务会显式传播或派生 TraceId, 执行记录使用 `start()/end()` 维护耗时和异常信息.

- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/model/EventReceiveContext.java:92 ~180`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/components/strategy/StrategyTemplate.java:174 ~222`

这反映出较强的生产排障导向. 可观测性不是外围设施, 而是业务执行模型的一部分.

## 测试风格演化

测试风格不能概括为单一模式, 它存在明显的年代变化.

### 早期阶段: 集成和探索优先

早期 Server 测试通常继承完整 Spring 测试上下文, 使用 `dev` profile, 并直接访问 Redis, MySQL, HTTP 或 Groovy 运行环境.

常见特点包括:

- Java `assert`
- 日志或 `System.out` 观察结果
- 实验性并发和缓存测试
- 测试, 示例和环境烟测混合
- 部分断言宽松或缺失

- `cz-risk-discern-server/src/test/java/com/changzhi/platform/risk/discern/AbstractTestCase.java:15 ~29`
- `cz-risk-discern-server/src/test/java/com/changzhi/platform/risk/discern/components/cumulative/impl/ContinuousSetVariableTest.java:17 ~80`

### 近期阶段: 行为和边界逐渐明确

近期测试更多采用:

- `condition_shouldBehavior` 方法命名
- Mockito 或手写 fake
- 参数化测试
- `@Nested` 和 `@DisplayName`
- `assertAll`
- 异常, 边界, 批量和并发行为覆盖

- `cz-risk-discern-server/src/test/java/com/changzhi/platform/risk/discern/service/StrategyCopyWorkerServiceTest.java:45 ~316`
- `cz-risk-discern-sdk/src/test/java/com/changzhi/platform/risk/discern/api/interfaces/FallbackPolicyTest.java:52 ~399`

但这种演化尚未彻底完成. `StrategyCopyWorkerServiceTest` 虽手工创建 mock 和被测对象, 仍继承 `AbstractTestCase`, 因而仍会加载 Spring 测试上下文.

更准确的结论是:

> 断言和依赖隔离正在向单元测试靠近, 但测试运行环境尚未完全脱离早期集成测试基类.

## Groovy 脚本风格演化

`src/test/groovy` 实际同时保存生产脚本, 实验代码和测试 fixture, 因此目录位置不能代表代码性质.

较新的复杂脚本逐渐形成以下结构:

- 入口方法负责调度和总异常处理
- IOC 服务在入口集中加载和校验
- 数据按页读取
- 按批写入
- 并发度和超时由配置控制
- 单行失败不阻断整页
- 运行统计持续写入任务上下文
- 返回明确的下一次执行时间和执行结果

- `cz-risk-discern-server/src/test/groovy/PeriodicScript/AccountRiskScoreScript.groovy:38 ~272`

历史脚本则更容易出现大段嵌套 `try/catch`, 直接回退默认值和混合式日志. 因此脚本风格也处于从任务脚本向工程化批处理程序演化的阶段.

## 近期收敛但尚非历史事实的特点

### 日志规范

当前 `AGENTS.md` 要求:

- 日志消息使用英文
- 变量放在消息末尾
- 名值使用 `=`
- 变量之间使用反引号分隔
- 异常对象放在参数末尾

但历史生产代码仍大量使用中文日志和多种占位符格式.

- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/service/BackendStrategyService.java:64 ~75`
- `cz-risk-discern-server/src/main/java/com/changzhi/platform/risk/discern/service/EventReceiveService.java:153 ~161`

因此英文结构化日志应被理解为近期明确的收敛方向, 不能描述成整个仓库一直稳定存在的风格.

### 分层门禁

Controller/Service/Components/Repository 的依赖方向长期存在于代码结构中, 但自动门禁直到提交 `de9def5` 才引入.

这说明分层是稳定个人选择, 自动化检查则是后期工程化增强.

### `chain = true`

DTO 使用 `@Accessors(chain = true)` 是长期主流. Git 历史还显示 2025-05 曾主动从 `fluent = true` 向 `chain = true` 收敛.

但仍有 `IgnoredOptions` 等 fluent 例外. 因此这是强倾向, 不是完全无例外的语法规则.

## 不应过度概括的现象

### 空值处理没有唯一风格

直接 `== null`/`!= null`, `Objects`, `ObjectUtils`, `CollectionUtils` 和 `StringUtils` 都被广泛使用.

不能将其中任一种描述为稳定的唯一偏好. 更接近事实的描述是按对象类型和局部上下文选择已有工具.

### import 没有严格统一

代码中存在大量通配符 import, 也存在逐项 import. Checkstyle 只检查分层依赖, 不检查 import 排序或通配符.

因此不能把某一种 import 形式提升为个人硬规则.

### 大类和长方法是被容忍的结果

核心模板, Repository 实现和复杂脚本中存在大类和长方法. 这些代码通常仍按业务步骤分段, 但不会为了形式上的短小继续拆出大量类型.

这更像优先级和抽象成本的取舍, 不等于刻意追求长方法.

### 局部重复并不总会立即抽象

SDK 降级结果构造, 数据中心查询重载和部分策略转换存在重复. 作者通常在重复形成稳定概念或产生维护压力后才提取公共方法.

这体现谨慎抽象, 不能简单归纳为偏好重复.

### 工具约束不等于个人风格

以下内容需要单独看待:

- `@RestController`, `@Service`, `@Repository` 具有 Spring 运行语义
- MyBatis Mapper 和实体大多由生成器产生
- Lombok 只提供生成能力, 并不自动要求使用 `@Data` 或链式 setter
- Checkstyle 当前只强制 import 层次
- ArchUnit 只覆盖已明确纳入治理的包方向

个人风格体现在如何选择和组合这些工具, 而不是注解本身.

## 风格演化轨迹

### 2025-04 至 2025-07

主要完成领域模型, 累计变量, 策略执行和基础集成. 测试偏真实环境和实验验证. 架构边界主要依靠包结构和开发者自觉.

### 2025-07 至 2026-01

并发, 缓存, trace, 表达式解析和 SDK 容错成为持续调校主题. 多次提交针对策略执行, ThreadLocal, 超时和缓存一致性进行修正.

代表提交:

- `2767e87`, 移除旧 ThreadLocal 执行上下文
- `dc810a3`, 根据实际阻塞调整并行取消策略
- `0912d78`, `6be48b9`, `3f387df`, 连续修补缓存更新
- `c617428`, 引入统一回调和虚拟线程处理

### 2026-04 至 2026-07

分层门禁, Mockito 行为测试, 工程化批处理脚本, benchmark 和 JFR 故障分析增加. 风格从能运行和快速验证, 继续向边界自动化, 行为可验证和运行证据化演化.

## 最终提炼

最稳定的个人风格不是某种格式或语法, 而是以下组合:

1. 用分层保持业务入口, 编排, 核心算法, 持久化和外部系统的职责可辨识
2. 只在真实变化点建立接口, 接受大型稳定模板集中编排复杂流程
3. 使用 guard clause 和线性流程表达业务步骤
4. DTO 追求构造便利, 值对象和内部载体追求明确不可变语义
5. 在模块兼容范围内积极使用现代 Java
6. 把并发, 缓存, trace, 超时和故障隔离视为核心设计的一部分
7. 优先表达业务语义, 即使名称较长或英文不够自然
8. 根据实际故障和性能数据持续调校代码, 不盲目追求预先完美
9. 对格式, import, 空值写法, 方法长度和局部重复保持务实容忍
10. 测试与日志规范正在从探索式实践向结构化行为和统一可观测性演化

这是一种偏生产实践, 业务驱动, 渐进治理的代码风格.
