# Skill 汉化 SOP

目标: 把外部或英文 skill 汉化为本仓库可维护版本, 同时保持行为语义, invocation 可靠性和低 context load.

## 适用范围

适用于把一个已有 skill 复制, 翻译, 本地化, 或适配到本仓库. 不适用于从零设计新 skill, 从零设计时先读 `general/write-a-skill/SKILL.md`.

完成标准:

- 已确认源 skill 路径和目标 skill 路径.
- 已确认目标运行时, 例如 `pi`, Claude Code, Codex CLI.
- 已确认目标 skill 是 `model-invoked` 还是 `user-invoked`.

## 1. 固定输入

先读源版 `SKILL.md`, 再读目标版 `SKILL.md`. 若正文明确引用 sibling reference, 按引用读取. 不要在完成对照前改文件.

完成标准:

- 已读取源版和目标版.
- 已读取适用的 `AGENTS.md`.
- 已读取 `general/write-a-skill/SKILL.md`.
- 若目标运行时有差异, 已查目标运行时文档或源码.

## 2. 区分三类内容

把 skill 拆成三层处理:

- **运行时字段**: frontmatter 中目标运行时真正消费的字段.
- **触发语义**: `name`, `description`, slash command, 关闭短语, 切换短语.
- **执行语义**: 正文里的步骤, 规则, 例外, 完成标准, 示例.

完成标准:

- 已标出有效 frontmatter 字段.
- 无效字段已计划删除, 除非明确要兼容另一个运行时.
- `description` 只保留触发器和必要摘要, 不重复正文身份设定.

## 3. 先比语义, 再比文字

不要直接逐句翻译. 先列行为差异:

- 缺失规则.
- 范围被误缩或误扩的规则.
- 示例技术栈替换后引入的偏向.
- 持续条件, 关闭条件, 强度级别等状态语义.
- 测试/check 规则和例外条件.
- 原版的最后约束, maxim, 或边界说明.

完成标准:

- 每个差异都有源版位置, 目标版位置, 影响, 处理决定.
- 本地化措辞差异没有被误判为行为差异.
- 行为差异没有被藏在普通翻译里.

## 4. 处理 frontmatter

按目标运行时保留字段. 以 `pi` 为例, 常用字段是 `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`, `disable-model-invocation`. 未知字段会被忽略, 应删除以降低噪音.

`description` 写法:

- `model-invoked`: 保留触发词, 每个 branch 只留一个触发器.
- `user-invoked`: 设置 `disable-model-invocation: true`, `description` 只写一行人类摘要.
- 不扩写触发词清单, 除非 invocation 证据不足.

完成标准:

- frontmatter 只含目标运行时有效字段或明确兼容字段.
- `description` 没有重复正文内容.
- skill name 保持稳定, 除非迁移计划明确要求改名.

## 5. 翻译正文

正文以中文为主体. 英文只保留以下类型:

- frontmatter key 和 metadata value.
- 命令, slash command, 参数, 关闭/切换触发短语.
- code, API, library, file path, protocol, hardware 型号.
- 强 leading word, 例如 `YAGNI`, 或已经成为 skill 共享语言的词.
- skill 名, 例如 `Ponytail`, `Caveman`.

翻译原则:

- 保留执行强度, 不把硬规则译软.
- 保留例外条件, 不把窄例外扩成通用许可.
- 保留数量词, 例如 `one`, `only`, `at most`, `never`.
- 技术术语能自然翻译就翻译, 代码字面量不翻译.
- 示例可本地化, 但不得无意改成特定技术栈专用.

完成标准:

- 每个残留英文都有保留理由.
- 所有普通 prose 已中文化.
- 原版的 must/never/only/at most 等约束强度仍可见.

## 6. 优化中文

逐句检查中文是否像规则, 不是散文. 优先短句, 硬边界, 可执行表达.

检查点:

- 贬义人格词改成行为词, 例如 `懒惰` 可改为 `会偷懒`.
- 直译腔改成工程语境, 例如 `boring` 可译为 `朴素`.
- 模糊动词改成动作, 例如 `处理` 改成 `删除`, `保留`, `质疑`.
- 弱约束补强, 例如 `一个` 改成 `一个且只有一个`.
- 口语化只在它能增强记忆时保留.

完成标准:

- 读者不看源版也能执行.
- 中文没有降低规则强度.
- 没有为了顺口删掉边界条件.

## 7. 保持信息层级

不要因为汉化就把所有 reference 内联. 按 `write-a-skill` 的信息层级放置内容:

- 每次运行都需要的步骤和规则留在 `SKILL.md`.
- 只有部分 branch 需要的材料放到 sibling reference.
- 一个概念的定义, 规则, 注意事项放在同一处.

完成标准:

- `SKILL.md` 没有被翻译细节撑大.
- reference 链接仍然有效.
- branch 专属材料没有污染所有路径.

## 8. 校验

汉化后至少做这些检查:

```bash
rg -n "[\x{ff0c}\x{3002}\x{ff1b}\x{ff1a}\x{ff01}\x{ff1f}\x{3001}\x{ff08}\x{ff09}\x{3010}\x{3011}]" <SKILL.md>
rg -n "[A-Za-z][A-Za-z0-9_./:@|*\-]*" <SKILL.md>
rg -n "^(---|name:|description:|license:|compatibility:|metadata:|allowed-tools:|disable-model-invocation:|# |## )" <SKILL.md>
```

检查说明:

- 第一条应无命中, 本仓库中文文档使用 ASCII 标点.
- 第二条用于人工审查残留英文, 不是要求清零.
- 第三条确认 frontmatter 和标题结构.

完成标准:

- 无中文全角标点.
- 残留英文均属于保留类型.
- frontmatter 可被目标运行时识别.
- 标题层级没有因翻译改变结构.

## 9. 交付说明

交付时只说明行为相关变化, 不复述全文.

交付格式:

- 修改了哪些文件.
- 删除或保留了哪些运行时字段.
- 哪些英文被保留, 原因是什么.
- 哪些关键规则被恢复或收紧.
- 做过哪些校验.

完成标准:

- 交付说明能让维护者快速 review.
- 不粘贴整份 skill.
- 不用长篇解释为翻译选择辩护.

## 反模式

- 只做逐句翻译, 不检查行为语义.
- 把 `description` 当正文摘要扩写.
- 为了中文化翻译命令, API, code snippet.
- 把原版通用示例改成单一技术栈, 却没有说明这是刻意本地化.
- 把 `one`, `only`, `never`, `at most` 译丢.
- 把无效 frontmatter 留着, 只因为原版有.
- 翻译后不扫残留英文和全角标点.
