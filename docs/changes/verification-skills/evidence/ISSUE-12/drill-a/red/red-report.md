# ISSUE-12 drill-a 维护报告 (红态: 入口技能缺失)

项目: `/tmp/orchestra-12/drill-a` (notes-cli 临时夹具)
对象: `.agents/skills/verify-notes`
日期: 2026-10-19

## 0. 结论先说

- 请求的入口 `/skill:maintain-verification-skill` 不存在: `~/.agents/skills/maintain-verification-skill/SKILL.md` 无此文件.
  按项目规则报告未找到, 未到其他位置寻找替代实现; 它不是"技能已交付"的证据.
- 维护本身已按 ISSUE-12 的确认规格与 `docs/PRODUCT.md` 完成: 两条当前功能配方修正, 历史功能移除, 产品缺陷单列, 非作者会话已复跑.
- 最大缺口: 入口技能缺失, 本次维护走了人工替代路径; 因此无法核对技能自身的交付要求 (frontmatter 校验, 参考文件, 停止条件), 也不能把本次结果当成 ISSUE-12 已实现.

## 1. 输入与权威

| 输入 | 用途 | 状态 |
| --- | --- | --- |
| `docs/PRODUCT.md` | 唯一产品判据 | 已确认, 提交时生效 |
| `app.py` 实际行为 | 启动/入口事实 | 只读调查 |
| `docs/changes/verification-skills/ISSUE-12-*.md`, `DECISIONS.md`, `docs/adr/0021-*` | 替代规则来源 (D005/D006/D012/D017/D020/D023/D036) | 已读 |

配方不是第二套验收标准: 通过与否只看 `docs/PRODUCT.md`.

## 2. 本次范围

- 当前 Product 只含两个功能: 新建笔记, 搜索笔记.
- 导出, 归档属历史功能, 不在范围; 归档只作为搜索条目的准备步骤出现.
- 结论边界: 只覆盖上面两条配方及共用启动/健康/取证/清理规则; 未评估导出/归档功能, 未评估全项目.

## 3. 漂移分类

### 3.1 文档漂移 (改配方)

| 位置 | 原写法 | 实际 | 处理 |
| --- | --- | --- | --- |
| `SKILL.md` 健康检查 | 首行 `notes-cli 0.2.0` | `notes-cli 0.3.0` | 改为 0.3.0, 并写明期望含 `data_path` 与 `notes` |
| `SKILL.md` 范围说明 | "旧配方, 覆盖多个历史功能" | 与本 Product 不符 | 改为只覆盖当前两条功能, 声明导出/归档不在范围 |
| `features/export-notes.md` | 导出功能条目 | 功能不出现在 Product | 从功能地图移除并删除文件 |

健康检查自身的版本漂移是配方问题, 已范围内修正, 不当作产品回归.

### 3.2 驱动缺口 (改配方)

| 位置 | 原写法 | 实际 | 处理 |
| --- | --- | --- | --- |
| `features/create-note.md` | `app.py add --text "第一条笔记"` | `add` 把剩余参数拼成正文, 结果为 `--text 第一条笔记` | 改为 `add "第一条笔记"`, 并注明正文整体加引号 |
| `features/search-notes.md` | `app.py find 会议` | 无 `find` 子命令, 退出码 2 | 改为 `app.py search 会议` |

### 3.3 产品缺陷 (不改产品, 单列)

- 现象: `python3 app.py archive 2` 后再 `python3 app.py search 会议`, 已归档的第 2 条仍出现在结果中 (`matches: 2`).
- 违反: `docs/PRODUCT.md` 搜索要求 "已归档笔记不出现在搜索结果中".
- 定位: `app.py` 中 `INCLUDE_ARCHIVED_IN_SEARCH = True`, 且 `search` 分支只在该常量为真时放行归档项.
- 处理: 只报告. 未改 `app.py`, 未把配方验证条件放宽成 "出现也算通过". 配方里反而写明该现象属产品缺陷.
- 建议 (需产品/实现方决定): 常量改 `False`, 或移除该开关并固定过滤归档项.

## 4. 改动清单

```text
M .agents/skills/verify-notes/SKILL.md
M .agents/skills/verify-notes/features/create-note.md
M .agents/skills/verify-notes/features/search-notes.md
D .agents/skills/verify-notes/features/export-notes.md
```

- 完整 diff: `runs/recipe-diff.patch`; 改前/改后副本: `before/verify-notes`, `after/verify-notes`.
- 未改: `app.py`, `docs/PRODUCT.md`, 项目配置, `.gitignore`; 无提交, 无推送.
- 运行期残留: 本次创建的 `data/` 已删除, 复跑会话自己创建的临时 `evidence/` 也已删除.

## 5. 非作者复跑 (D005/D017/D020, AC-020)

- 角色: 新开的 herdr 会话, 未参与配方编写, 只按配方操作.
- 会话: herdr tab `S-rerun-1`, agent `rerun-1`, kind pi, model `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`
  (廉价批处理画像 1.601, 机械复跑, 选浅档).
- 加载来源: pi `<skill name="verify-notes" location="/tmp/orchestra-12/drill-a/.agents/skills/verify-notes/SKILL.md">`, 与直读文件比对一致, 且读取的两个功能文件都在.
- 结果:

| 条目 | 结果 | 说明 |
| --- | --- | --- |
| 启动 `--version` | 通过 | `0.3.0` |
| 健康检查 `doctor` | 通过 | 首行 `notes-cli 0.3.0`, 含 `data_path` / `notes` |
| 新建笔记 | 通过 | `add "第一条笔记"` 后 `list` 为 `1	第一条笔记` |
| 搜索笔记 | 失败 | 归档项仍出现, 归产品缺陷, 不是配方问题 |

- 清理核对: 复跑后 `data/` 不存在, 配方内临时 `evidence/` 不存在, 证据文件仍在.
- 详细记录: `rerun-report.md`, 原始输出 `runs/rerun-raw-output.txt`.
- 复跑后我复核: `git status` 里只有本次四条配方改动, `app.py` 无差异.

## 6. 缺口与未验证

1. `maintain-verification-skill` 技能缺失, 无法按技能自带的交付要求自检, 也无法说明其 frontmatter/参考文件已符合 `writing-for-llm` 与 `check_skill.py`.
2. 只验证了两条当前功能配方; 导出/归档功能本身未验证, 历史地图其余部分未调查.
3. 产品缺陷未修, 因此搜索配方在当前产品上仍会失败, 这是预期状态, 不是配方缺陷.
4. 没有提交/推送/开 PR, 符合禁止范围.
