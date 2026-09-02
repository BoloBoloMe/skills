# 产品验收标准 Gherkin 化与机检脚本 Product Spec

> 改名注解 (2026-09-02): 文中 `to-product-spec` 与 `to-technical-spec` 即现行 `to-spec` (`workflow/to-spec/`), `to-execution-spec` 即现行 `to-execution` (`workflow/to-execution/`); 决策见 `docs/changes/spec-skills-merge/DECISIONS.md`.

## 背景

旧格式 PRODUCT.md 的验收标准 (AC) 是自由散文的给定/当/则句式, 且 关键场景 (SC) 节与 AC 双载体重叠; 解析/标签/覆盖等形态规则没有机械校验面, 只能靠 LLM 目检, 而 LLM 目检不可靠. 受益者: spec 编写方 (落盘即合法, 不返工), workflow 维护者 (规则由脚本统一强制, 不随会话漂移), 变更的四方读者 (业务/开发/测试/人, 场景自包含可读). 需求来源: 用户经 deliberate 盘问确认, 结论固化于本变更决策账本 D001-D022. 现在处理的理由: 模板改动无实例是盲改 (D017), 本 spec 自身即新模板与机检脚本的首个试金石.

## 目标

- G-001: 新变更 PRODUCT.md 的验收标准以官方 zh-CN Gherkin 内嵌于 markdown, 场景为唯一场景载体, 可被 parser 解析.
- G-002: 机检脚本 check-ac.py 对产物形态做机械校验: 合法产物退出码 0, 非法产物按规则类报错且退出码非 0, 校验一律以脚本结果为准.
- G-003: 审计式断言有独立稳定落点 (非行为验收小节), 与行为验收不共用载体.

## 非目标

- 不上可执行层: 不写 step definitions, 触发条件与迁移路径见 D015.
- 不回填历史产物: docs/changes/present-web-server/PRODUCT.md 等既有产物维持旧格式 (D016).
- 不改 workflow/deliberate/SKILL.md: 盘问全程保持自然语言 (D013).
- 技术层不做 Gherkin 化: workflow/to-technical-spec 不动, TC 保持散文 GWT 句式 (D014).
- 不覆盖 workflow 元词汇表的内容盘点与定义质量: 元词汇表按 D018 并入本变更实施, 其产物属 domain-awareness 职责, 不在本 spec 验收范围.

## 用户故事

- US-001: 作为 spec 编写方, 我想要模板与书写纪律明确的新格式 Gherkin 形态, 以便落盘即合法可机检, 不靠事后目检返工.
- US-002: 作为 workflow 维护者, 我想要机检脚本统一强制形态规则, 以免规则执行随 LLM 会话漂移.
- US-003: 作为变更的四方读者 (业务/开发/测试/人), 我想要自包含的 Gherkin 场景与独立编号的非行为断言, 以便不经叙述视角也能核对每条验收与每项审计结论.

## 业务规则

- BR-001: 标签集封闭: 只允许 @AC-NNN / @G-NNN / @US-NNN / @BR-NNN / @normal / @failure / @edge; 每场景恰好一个 @AC-NNN, 至少一个覆盖标签; 标签只允许出现在 场景:/场景大纲: 行 (D003/D007).
- BR-002: 关键字白名单: zh-CN 官方子集唯一写法 (功能/背景/场景/场景大纲/例子/假定/当/那么/而且/但是); 禁 给定/则/英文关键字/官方同义变体/规则: (Rule) (D005/D008).
- BR-003: 验收标准节形态: 单个 gherkin 代码块, 首行 # language: zh-CN, 次行 功能: <变更标题>, 不产独立 .feature 文件 (D001/D002).
- BR-004: 机检唯一触发点 = to-product-spec 完成标准; LLM (含子代理) 只允许调用脚本并汇报结果, 禁止目检替代脚本 (D012).
- BR-005: 审计式断言不进场景, 落 非行为验收 小节并编 NB-NNN; 转得了行为的断言必须写成场景 (D010).

## 验收标准

场景规则与标签/关键字约定见 workflow/to-product-spec/GHERKIN.md; 本节按模板为单个 gherkin 块.

```gherkin
# language: zh-CN
功能: 产品验收标准 Gherkin 化与机检脚本

@AC-001 @normal @G-001 @G-002 @US-001 @BR-003 @BR-004
场景: 合法产物通过机检
假定 spec 编写方按新模板产出一份 PRODUCT.md, 其验收标准块内场景标签与关键字齐全
当 spec 编写方在仓库根执行 uv run workflow/to-product-spec/check-ac.py 并传入该文件路径
那么 脚本退出码为 0
而且 stdout 输出通过摘要, 报告场景数与 AC 数

@AC-001 @edge @G-002 @BR-003
场景: 场景大纲计为一个场景
假定 产物的验收标准块含 2 个普通场景与 1 个配 例子 表的场景大纲
当 spec 编写方执行机检脚本
那么 脚本退出码为 0
而且 通过摘要报告场景数为 3

@AC-002 @failure @G-002 @US-002 @BR-001 @BR-002
场景大纲: 规则类违规按类报错
假定 spec 编写方持有一份存在 <产物缺陷> 的 PRODUCT.md
当 spec 编写方执行机检脚本
那么 脚本退出码非 0
而且 stderr 输出以 [<报错规则类>] 为前缀的违规条目

例子:
| 产物缺陷 | 报错规则类 |
| 场景挂自由标签 @smoke | 标签封闭集 |
| 单场景同时挂 @AC-001 与 @AC-002 | @AC 唯一性 |
| 场景缺 @G-NNN/@US-NNN/@BR-NNN 覆盖标签 | 覆盖完整性 |
| 场景使用 规则: 关键字分组 | 关键字白名单 |
| 功能: 行之前挂 @AC-001 标签行 | tag-position |
| 场景步骤以 给定 或 则 开头 | 关键字白名单 |

@AC-002 @failure @G-002 @US-002 @BR-002
场景: 结构性语法错误解析失败
假定 spec 编写方持有一份 gherkin 块中 背景: 行出现在 场景: 行之后的 PRODUCT.md
当 spec 编写方执行机检脚本
那么 脚本退出码为 1
而且 stderr 输出 [解析] 前缀与 parser 原始错误, 报错行号为 PRODUCT.md 文件行号

@AC-003 @edge @G-002 @US-002 @BR-003
场景大纲: 文档级结构缺陷判为输入错误
假定 spec 编写方持有一份 <结构缺陷> 的 PRODUCT.md
当 spec 编写方执行机检脚本
那么 脚本退出码为 2
而且 stderr 输出以 [输入] 为前缀的报错

例子:
| 结构缺陷 |
| 文档无 验收标准 节 |
| 验收标准 节内无 gherkin 代码块 |
| 验收标准 节内含两个 gherkin 代码块 |
| gherkin 块首行不是 # language: zh-CN |

@AC-004 @normal @G-001 @G-003 @US-003 @BR-005
场景: 新格式产物不含关键场景节
假定 spec 编写方按新模板产出 PRODUCT.md
当 变更读者查阅该文档章节
那么 文档不存在 关键场景 节
而且 场景的正常/失败/边界类型由 @normal/@failure/@edge 标签承载

@AC-004 @normal @G-003 @US-003 @BR-005
场景: 审计式断言落入非行为验收小节
假定 盘问确认的结论含审计式断言 (如 未引入认证)
当 spec 编写方落盘 PRODUCT.md
那么 该断言以 NB-NNN 编号出现在 非行为验收 小节
而且 不出现在任何场景步骤中

@AC-004 @edge @G-003 @US-003 @BR-005
场景: 可转行为的断言强制写成场景
假定 盘问确认的结论含可转为刺激-响应的断言 (如 重启后归零)
当 spec 编写方落盘 PRODUCT.md
那么 该断言以场景步骤形式出现在验收标准块
而且 不落入 非行为验收 小节
```

## 非行为验收

- NB-001: workflow/deliberate/SKILL.md 一字未改, 盘问保持自然语言 (D013).
- NB-002: workflow/to-technical-spec 产物未 Gherkin 化, TC 保持散文 GWT 句式 (D014).
- NB-003: docs/changes/present-web-server/PRODUCT.md 等历史产物未回填新格式 (D016).
- NB-004: 本期未引入 step definitions 与可执行层 (D015).

## 成功指标

不设指标. 已确认理由: 机检退出码 0 已是 to-product-spec 完成标准的硬门槛, 形态质量由脚本闭环保证, 无独立观测渠道 (D012).

## 产品决策引用

- docs/changes/gherkin-ac/DECISIONS.md: D001, D002, D003, D004, D005, D007, D008, D009, D010, D011, D012, D013, D014, D015, D016, D017. 核心取舍: D001 (内嵌 Gherkin), D003 (1 AC = 1..N 场景), D004 (删 SC 节), D010 (NB 小节), D011 (机检脚本形态), D012 (单触发点), D017 (本 spec 自身为试金石).

## 待验证事实

无.
