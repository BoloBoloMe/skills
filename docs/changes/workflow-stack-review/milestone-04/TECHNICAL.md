# demo 改名与 PoC 类型落地 Technical Spec

## 模块划分

- `workflow/demo/` (由 `workflow/prototype/` 改名): 制作演示材料的方法与规则. 藏了"逻辑演示还是外观演示"的分支判据, 三子形态 (贴现有页面 / 新页面 / 无前端项目) 的落位规则, 以及"验证止于能演示"的边界. 删除测试: 删掉它, 这些判据会散回 navigate 的类型条目和现场口述. 本次除改名外, 正文按演示语义重写: 适用范围句写明拿已交付成品或线上系统演示时不调用本 skill, 正文不提 PoC; 通用规则 1 改为不进产品/不承诺交付/材料可保留回看, 规则 5 的捕获改为记录演示了什么, 想让我据此判断什么, 材料位置与 issue 指针, 规则 6 改为验证止于能演示. `LOGIC.md` 第 5 步的清理句改为与点名删除一致.
- `workflow/navigate/SKILL.md` 的类型语汇: 描述各里程碑类型何时创建, 完成标准, 收口产物, 及其处置. 本次只改文本, 不新增模块. 其中 `poc` 条目新增拆分判据 (按结论边界拆, 单结论跨会话不拆, 会话规模只作经验), 产品代码归 `task` 的指派, 以及终止处置 (亲裁终止才记关闭, 摘要写未证实即终止, 移除终点验收依赖, 不记歧路); `research` 条目补"工作目录内的事实就地查, 不单立里程碑"及查影响面/查领域的指派.
- `workflow/navigate/TEMPLATES.md`: ROADMAP.json 的字段说明, 含 `type` 的合法值一行. 本次只改枚举行与原型一词.
- `workflow/navigate/scripts/roadmap.py`: 守门脚本. 本次只改 `TYPE_VALUES` 常量, 校验错误文案由该常量拼出, 不新增分支.
- `workflow/navigate/web/index.html`: 地图展示页. 本次改类型元数据表, 图例, 星球外观分派, 配色表.
- `workflow/navigate/tests/visual/render_checks.py`: 星球渲染检查. 本次改类型清单与其夹具里的类型值, 并给新类型留下渲染用例.
- `README.md`: 工作流技能表一行.
- `docs/adr/0024-demo-poc-milestone-types.md`: 新增 ADR, 记录命名与枚举约定及旧名处置边界.

模块/目录边界: 可改 `workflow/demo/`, `workflow/navigate/`, `docs/adr/`, `README.md`; 其余文件不动.

## 模块接口

- `roadmap.py` 命令行: 保持现有 `query` / `save` / `delete` 三个操作与现有参数, 不新增命令. `type` 合法值集合变为 `research`, `deliberate`, `demo`, `poc`, `task`, `acceptance`; 非法值仍以退出码 1, stdout 单行 JSON 的 `error` 字段报错, 消息里列出完整合法值.
  - 不变量: 不含 `demo`/`poc` 的既有 ROADMAP.json 照常读取与校验通过; `query` 不写文件; 写入路径仍只认 `milestones.<id>.<field>` 形式. 不含 `prototype` 的兼容别名.
- 展示页 `?roadmap=<绝对路径>`: 页面按 `type` 取元数据, 元数据表必须覆盖上述 6 个值; 未知类型仍回退到 `task` 元数据, 不抛错. 图例每类一项, 顺序与元数据表一致.
- `workflow/demo/SKILL.md` 的 frontmatter: `name: demo`, description 重写为演示用途; 保留 `disable-model-invocation: true`, 不改变调用方式 (仍由 navigate 的 demo 类型条目点名).
  - 不变量: 正文只谈怎么造演示材料; 演示已交付成品是直接跑成品, 不调用本 skill; 正文出现 PoC 字样即偏离 (证据在 poc 里程碑自己产物里).
- `docs/adr/0024-demo-poc-milestone-types.md`: 记录 demo 取代 prototype, poc 为新增类型, 以及旧分支/旧目录只作历史存在. 遵循 `docs/adr` 既有格式.

## 接缝与依赖

- 无新增跨模块接缝. 本次改动的两处既有接缝均在模块内部: `roadmap.py` 的 `TYPE_VALUES` 与校验函数之间 (内部); 展示页 `TYPE_META` 与渲染分派之间 (内部).
- 依赖类别无变化: 测试与展示页只用仓库内文件与进程内依赖, 不引入远程或真正外部依赖.

## 安全策略

不适用: 改动是仓库内文档, 静态前端资源与常量枚举, 不涉及认证, 授权, 隐私, 密钥或脱敏数据. 唯一安全底线是写入范围限制在仓库内文件, 不触碰已安装 skills 与全局配置.

## 非功能要求

- 回归检查: `uv run python -m pytest workflow/navigate/tests` 全部通过 (含 ROADMAP 校验, CLI, 网页服务与视觉渲染检查), 通过标准为退出码 0 且无 failed.
- 文档机检: 本次改动的每个 `SKILL.md` 运行 `uv run python general/writing-for-llm/check_skill.py <path>`, 通过标准为输出 OK 且退出码 0.
- 不宣称安装效果: 不运行 `sync-to-pi.py`, 不以仓库内改动推断已安装 skill 的行为, 不测量模型触发率或 token 变化.

## 决策引用

- `docs/changes/workflow-stack-review/milestone-01/DECISIONS.md`: D004, D005, D006, D007, D013
- `docs/changes/workflow-stack-review/milestone-03/DECISIONS.md`: D001, D002, D004, D005, D011, D012, D013, D014, D015, D016, D017, D018, D019
