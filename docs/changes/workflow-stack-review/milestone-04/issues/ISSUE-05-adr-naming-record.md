## 父级
- `../EXECUTION.md`
## 执行
- [ ] 已完成
## 要交付什么
新增 `docs/adr/0024-demo-poc-milestone-types.md`, 按 `docs/adr` 既有体例 (标题一行加 1 到 3 句正文) 记下三条: `demo` 取代 `prototype` 作为演示类工作的名称; `poc` 是新增的里程碑类型; 旧名处置边界是旧 `prototype/` 开头分支与 `docs/changes` 下的 `prototypes/` 产物目录按历史证据原样保留, 不做读取兼容.

具体:
1. 文件为 `docs/adr/0024-demo-poc-milestone-types.md`, 编号接在现有最大号 0023 之后.
2. 标题用一句概括改名与新增类型; 正文 1 到 3 句, 写清替代关系, 新增类型, 以及旧分支/旧目录只作历史存在且不提供兼容读取.
3. 体例对齐 `docs/adr/0023-verification-only-workflow.md`: 无多余章节, 不加 frontmatter Status 除非该文件用了.
## 覆盖依据
- Product: `../PRODUCT.md`, AC-014, G-006, NG-001, NG-002.
- Technical: `../TECHNICAL.md`, 模块划分 (docs/adr 条目), 模块接口 (ADR 记录范围与既有格式).
## 相关决策
- `../../milestone-03/DECISIONS.md`: D013 (记一条 ADR 记命名与枚举约定), D001 (不留别名的取舍与历史文件原样保留).
## 允许范围
- 新增 `docs/adr/0024-demo-poc-milestone-types.md`.
## 禁止范围
- 不改任何既有 ADR, 不改编号, 不在 ADR 里重记 PoC 词义 (词义归 `workflow/software-engineering-consensus/`).
- 不写实施状态, 不写验证结论, 不复制 PRODUCT/TECHNICAL 正文.
## 代码定位提示
- 体例样板: `docs/adr/0023-verification-only-workflow.md` (标题加一段正文), `docs/adr/0017-navigate-roadmap-json-gatekeeper-script.md`.
- 事实来源: `../../milestone-03/DECISIONS.md` 的 D001 与 D013; `../PRODUCT.md` 的 NG-001 与 NG-002.
- 编号核对: `ls docs/adr/` 现有最大号为 0023.
## 验证契约
- 变更类型: 非行为改动.
- 对应范围: 新增一篇决策记录文档, 不影响任何脚本, 页面或 skill 行为.
- 验证要求/证据: 文件存在且编号连续; 正文覆盖 AC-014 的可观察断言 (demo 取代 prototype, poc 新增, 旧分支与旧目录保留且不兼容); 体例与相邻 ADR 一致 (无多余章节); `git status` 显示只有这一个新文件属于本 issue.
## 验证入口
```bash
ls docs/adr/ | tail -3        # 通过标准: 最大编号是 0024-demo-poc-milestone-types.md, 0023 仍在
sed -n '1,12p' docs/adr/0024-demo-poc-milestone-types.md
#    通过标准: 首行是标题; 正文 1 到 3 句; 含 demo 取代 prototype, poc 为新增类型,
#    旧分支与 docs/changes 下 prototypes/ 目录按历史保留, 不做读取兼容
grep -n 'prototype\|PoC\|poc' docs/adr/0024-demo-poc-milestone-types.md
#    通过标准: prototype 只以被取代的旧名出现; poc 以新增类型出现; 没有复制 PoC 词条定义
git status --short docs/adr/   # 通过标准: 只有一个新增文件, 无既有 ADR 改动
```
## 交付证据
执行后填写: 文件路径与正文摘录, 编号核对输出, `git status` 结果.
## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.
## 验收标准
- [ ] `docs/adr/0024-demo-poc-milestone-types.md` 存在, 编号连续, 体例与相邻 ADR 一致.
- [ ] 正文写明 demo 取代 prototype, poc 为新增类型, 旧分支与旧目录按历史证据保留且不做读取兼容.
## 被阻塞于
- 无
