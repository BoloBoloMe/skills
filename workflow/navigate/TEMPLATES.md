# 产物结构: ROADMAP.json

路线图全部信息存于单个 ROADMAP.json. 本文件说明其 schema, path 语法, CLI 调用与目录约定.

## 文件位置

`docs/changes/<feature-slug>/roadmap/ROADMAP.json`

## 顶层字段 (D005)

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `schema_version` | string | 自动 | `"0.0.1"` | 脚本初始化时写入, 调用者不改 |
| `title` | string | 否 | `""` | 路线图标题 |
| `destination` | string | 否 | `""` | 目的地: 到达时的样子, 1-2 句话 |
| `notes` | 数组 | 否 | `[]` | 领域, 应查阅的 skill, 固定偏好, 方向侦查结论; 下标即自然笔记编号 |
| `milestones` | 对象 | 否 | `{}` | 以里程碑 id 为键, 成员见下表 |
| `unknown_seas` | 字符串数组 | 否 | `[]` | 未知海域: 范围内但尚无法精确表述为 Milestone 的模糊视图 |
| `off_course` | 对象数组 | 否 | `[]` | 歧路: 目的地之外主动排除的工作, 每项 `{what, reason}` |

## milestones 成员字段 (D005/D006)

里程碑 id 形如 `milestone-01`, 非纯数字, 不被当作数组下标.

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `title` | string | 是 | 无 | 简述 |
| `status` | string 枚举 | 否 | `待处理` | `待处理` / `进行中` / `已关闭` |
| `type` | string 枚举 | 是 | 无 | `research` / `deliberate` / `prototype` / `task` |
| `blocked_by` | 里程碑 id 字符串数组 | 否 | `[]` | 引用的 id 必须已存在, 不允许环 (含自环) |
| `question` | string | 是 | 无 | 本 Milestone 要解决的决策或调查 (详述) |
| `artifacts` | 字符串数组 | 否 | `[]` | 产物链接 |
| `close_summary` | string 或 null | 否 | `null` | 关闭摘要 |

新增里程碑必须整体创建: `save <file> milestones.<new-id> <JSON对象>`, 对象含必填 `title`/`type`/`question`; 脚本补齐默认 `status`/`blocked_by`/`artifacts`/`close_summary`. 不可分字段逐个创建 (会缺字段而被整文档校验拒绝).

## 不落盘的派生量 (D005)

JSON 只存路线图与里程碑逻辑数据, 零展示信息 (不存坐标/颜色等). 以下均由数据推导, 不写文件:

- 前沿: 未关闭 (`status != 已关闭`) 且 `blocked_by` 全部已关闭的里程碑.
- 已关闭决策: 各里程碑的 `close_summary` + `artifacts`.
- 阻塞关系: 各里程碑 `blocked_by` 的并集 (网页端据此画 DAG).

## path 语法 (D004)

- 点分隔, 如 `milestones.milestone-01.status`, `destination`, `notes.2`.
- 数字段定位数组元素: `notes.2` = 第三条笔记.
- 下标 == 数组当前长度 = 追加; 下标 > 长度 = 越界报错.
- 对数组字段整体 save (如 `save <file> notes <JSON数组>`) 全量替换同样合法.
- 中间节点不存在时由脚本自动创建.

## CLI 调用 (D003)

`<file>` 即上面的 ROADMAP.json 路径. stdout 单行 UTF-8 JSON, 退出码 0 成功 / 1 失败.

```bash
# 读: 目的地, 笔记数组, 全部里程碑
uv run python workflow/navigate/scripts/roadmap.py query docs/changes/<feature-slug>/roadmap/ROADMAP.json destination
uv run python workflow/navigate/scripts/roadmap.py query docs/changes/<feature-slug>/roadmap/ROADMAP.json notes
uv run python workflow/navigate/scripts/roadmap.py query docs/changes/<feature-slug>/roadmap/ROADMAP.json milestones

# 写: 目的地, 追加一条笔记 (下标 == 当前长度), 新建里程碑, 改状态, 记产物, 写关闭摘要
uv run python workflow/navigate/scripts/roadmap.py save <file> destination '"到达时: ..."'
uv run python workflow/navigate/scripts/roadmap.py save <file> notes.0 '"方向 A 结论: ...; 排除方向 B 的理由: ..."'
uv run python workflow/navigate/scripts/roadmap.py save <file> milestones.milestone-01 '{"title": "选定存储方案", "type": "deliberate", "question": "..."}'
uv run python workflow/navigate/scripts/roadmap.py save <file> milestones.milestone-02.blocked_by '["milestone-01"]'
uv run python workflow/navigate/scripts/roadmap.py save <file> milestones.milestone-01.status '"进行中"'
uv run python workflow/navigate/scripts/roadmap.py save <file> milestones.milestone-01.artifacts '["docs/changes/<feature-slug>/milestone-01/findings.md"]'
uv run python workflow/navigate/scripts/roadmap.py save <file> milestones.milestone-01.close_summary '"已选定方案 X: ..."'

# 删: 整个文件
uv run python workflow/navigate/scripts/roadmap.py delete <file>
```

`content` 先按 JSON 解析, 解析失败按裸字符串存. 文本含引号/数字/括号等易歧义内容时, 用 JSON 字符串形式 (外层再套单引号) 传.

## 禁令与旧格式

- llm 禁用 read/write/edit 工具直接触碰 ROADMAP.json; 一切读写经上述脚本 (D002).
- 现场出现旧版 `ROADMAP.md` / `MILESTONE-NN.md` 时, 用 read 读旧文件后经脚本重建为 ROADMAP.json; 不提供迁移命令 (D014).

## 目录约定

- 路线图文件: `docs/changes/<feature-slug>/roadmap/ROADMAP.json`.
- 里程碑产物 (findings/原型/决策文档等) 仍是独立文件, 放 `docs/changes/<feature-slug>/<milestone-NN>/`, 链接记入该里程碑 `artifacts`.
- 会话中调用 `to-execution` skill 时, 产物根目录指定为 AFK 编码任务所属里程碑的子目录 `docs/changes/<feature-slug>/<milestone-NN>/`.
