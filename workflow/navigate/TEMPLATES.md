# 产物结构: ROADMAP.json

路线图全部信息存于单个 ROADMAP.json. 本文件说明其 schema, path 语法, CLI 调用与目录约定.

## 文件位置

`docs/changes/<feature-slug>/roadmap/ROADMAP.json`

## 顶层字段

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `schema_version` | string | 自动 | `"0.0.1"` | 脚本初始化时写入, 调用者不改 |
| `title` | string | 否 | `""` | 路线图标题 |
| `destination` | string | 否 | `""` | 目的地: 到达时的样子, 1-2 句话 |
| `notes` | 数组 | 否 | `[]` | 领域, 应查阅的 skill, 固定偏好, 方向侦查结论; 下标即自然笔记编号 |
| `milestones` | 对象 | 否 | `{}` | 以里程碑 id 为键, 成员见下表 |
| `unknown_seas` | 字符串数组 | 否 | `[]` | 未知海域: 范围内但尚无法精确表述为 Milestone 的模糊视图 |
| `off_course` | 对象数组 | 否 | `[]` | 歧路: 目的地之外主动排除的工作, 每项 `{what, reason}` |

写入约束: 未列出的顶层字段会被脚本拒绝写入. 每次 save 在内存完成写入后对整文档跑完整 schema 校验 (含 `blocked_by` 环检测), 任一校验失败则不落盘并返回错误 (整文档校验是兜底闸门).

## milestones 成员字段

里程碑 id 形如 `milestone-01`, 非纯数字, 不被当作数组下标.

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `title` | string | 是 | 无 | 简述 |
| `status` | string 枚举 | 否 | `待处理` | `待处理` / `进行中` / `已关闭` |
| `type` | string 枚举 | 是 | 无 | `research` / `deliberate` / `demo` / `poc` / `spec` / `verification-plan` / `execution-plan` / `implementation` / `verification` / `task` / `acceptance` |
| `blocked_by` | 里程碑 id 字符串数组 | 否 | `[]` | 引用的 id 必须已存在, 不允许环 (含自环) |
| `question` | string | 是 | 无 | 本 Milestone 要解决的问题或完成的工作 (详述) |
| `inputs` | 对象数组 | 新建必填 | 无 | 每项含非空 `content`, 可选非空 `source`; 无输入显式写 `[]` |
| `output_dir` | string 或 null | 新建必填 | 无 | 传给下游 skill 的产物根目录; 无独立产物目录显式写 `null` |
| `artifacts` | 字符串数组 | 否 | `[]` | 产物链接 |
| `close_summary` | string 或 null | 否 | `null` | 关闭摘要 |

新增里程碑必须整体创建: `save <file> milestones.<new-id> <JSON对象>`, 对象含必填 `title`/`type`/`question`/`inputs`/`output_dir`; 脚本补齐默认 `status`/`blocked_by`/`artifacts`/`close_summary`. 不可分字段逐个创建 (会缺字段而被整文档校验拒绝).

`inputs` 每项的 `content` 说明需要什么内容及用途, 不复制来源正文; `source` 指文件/章节/URL/完整提交号等可追溯来源, 无落盘材料时省略, 不将其冒充权威输入. 例如 `{"content": "产品判据", "source": "docs/changes/foo/PRODUCT.md#验收标准"}`. 输入对象只允许这两个字段. 制图时允许预期来源, 领取时核实存在, 确认状态和适用版本; 验证里程碑还须明确目标提交与方案修订号. `blocked_by` 只管等待关系, `inputs` 管实际输入, `artifacts` 只记实际产物.
`output_dir` 是非空目录路径或 `null`, 需要落盘的下游 skill 不得带 `null` 开始. 项目内的 `inputs.source`, `output_dir` 和产物链接从目标项目根目录解析, 不是从 `roadmap/` 解析; 项目外材料使用明确路径或 URL. 产物内部相对引用仍按共识从产物根目录解析.
旧图缺 `inputs`/`output_dir` 时仍可 query/save, 脚本不自动补默认值或猜目录. 领取前按实际材料补齐, 无法核实时报告缺口; 新建节点无论单独还是随整个 `milestones` 写入都必须显式提供这两个字段.

## 不落盘的派生量

JSON 只存路线图与里程碑逻辑数据, 零展示信息 (不存坐标/颜色等). 以下均由数据推导, 不写文件:

- 前沿: 未关闭 (`status != 已关闭`) 且 `blocked_by` 全部已关闭的里程碑.
- 已关闭决策: 各里程碑的 `close_summary` + `artifacts`.
- 阻塞关系: 各里程碑 `blocked_by` 的并集 (网页端据此画 DAG).

## path 语法

- 点分隔, 如 `milestones.milestone-01.status`, `destination`, `notes.2`.
- 数字段定位数组元素: `notes.2` = 第三条笔记.
- 下标 == 数组当前长度 = 追加; 下标 > 长度 = 越界报错.
- 对数组字段整体 save (如 `save <file> notes <JSON数组>`) 全量替换同样合法.
- 中间节点不存在时由脚本自动创建.

## CLI 调用

`<file>` 即上面的 ROADMAP.json 路径. stdout 单行 UTF-8 JSON, 退出码 0 成功 / 1 失败.

```bash
# 读: 目的地, 笔记数组, 全部里程碑
uv run python <skill 目录>/scripts/roadmap.py query docs/changes/<feature-slug>/roadmap/ROADMAP.json destination
uv run python <skill 目录>/scripts/roadmap.py query docs/changes/<feature-slug>/roadmap/ROADMAP.json notes
uv run python <skill 目录>/scripts/roadmap.py query docs/changes/<feature-slug>/roadmap/ROADMAP.json milestones

# 写: 目的地, 追加一条笔记 (下标 == 当前长度), 新建里程碑, 改状态, 记产物, 写关闭摘要
uv run python <skill 目录>/scripts/roadmap.py save <file> destination '"到达时: ..."'
uv run python <skill 目录>/scripts/roadmap.py save <file> notes.0 '"方向 A 结论: ...; 排除方向 B 的理由: ..."'
uv run python <skill 目录>/scripts/roadmap.py save <file> milestones.milestone-01 '{"title": "选定存储方案", "type": "deliberate", "question": "...", "inputs": [], "output_dir": "docs/changes/<feature-slug>/"}'
uv run python <skill 目录>/scripts/roadmap.py save <file> milestones.milestone-02.blocked_by '["milestone-01"]'
uv run python <skill 目录>/scripts/roadmap.py save <file> milestones.milestone-01.status '"进行中"'
uv run python <skill 目录>/scripts/roadmap.py save <file> milestones.milestone-01.artifacts '["docs/changes/<feature-slug>/DECISIONS.md"]'
uv run python <skill 目录>/scripts/roadmap.py save <file> milestones.milestone-01.close_summary '"已选定方案 X: ..."'

# 删: 整个文件
uv run python <skill 目录>/scripts/roadmap.py delete <file>
```

`content` 先按 JSON 解析, 解析失败按裸字符串存. 文本含引号/数字/括号等易歧义内容时, 用 JSON 字符串形式 (外层再套单引号) 传.

## 目录约定

- 路线图文件: `docs/changes/<feature-slug>/roadmap/ROADMAP.json`.
- 同一交付单元的多个里程碑在 `output_dir` 填相同的产物根目录, 默认 `docs/changes/<feature-slug>/`; 多个交付单元可各用子目录, 不按里程碑编号强制分目录.
- 调用下游 skill 时传入该里程碑的 `inputs` 与 `output_dir`, 直接复用实际来源. 独立验证的证据按验证规则放绑定目标提交的子目录, 环境要求放项目外时记录实际位置. 代码改动仍在目标仓库完成, `output_dir` 不代替代码工作目录.
- `artifacts` 记录实际文件, 报告或提交链接; 无独立产物目录时 `output_dir` 写 `null`, 关闭摘要说明原因, 不为填字段强造文件.
