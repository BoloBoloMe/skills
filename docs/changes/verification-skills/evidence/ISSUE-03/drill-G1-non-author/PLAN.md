# 验收派工计划 (2028383)

## 输入

- 标准: `docs/changes/tool-cli/PRODUCT.md`, `验收标准` 节带 `<!-- confirmed-flow: v1 -->`, 确认标记位于 gherkin 块之前.
- 目标版本: `2028383100c4d5c65789c3a56b13c44d6eba8da2` (HEAD, `feat: greet 支持全大写输出`).
- 版本前提: `git status --porcelain` 为空; HEAD 与目标提交一致; 无未跟踪产品文件.
- 产物根目录: `docs/changes/tool-cli/`; 本轮证据目录: `docs/changes/tool-cli/verify-2028383-v1/`.

## 必验清单 (条数 = 场景 5 + 审计 BR 1 = 6)

| 编号 | 类型 | 承接方式 |
| --- | --- | --- |
| AC-001-1 默认问候 | 场景 | 运行 CLI 观察 stdout 与退出码 |
| AC-001-2 全大写问候 | 场景 | 运行 CLI 观察 stdout 与退出码 |
| AC-002-1 统计词数 | 场景 | 运行 CLI 观察 stdout 与退出码 |
| AC-002-2 统计字符数 | 场景 | 运行 CLI 观察 stdout 与退出码 |
| AC-003-1 JSON 导出 | 场景 | 运行 CLI 观察 stdout 与退出码 |
| BR-002 依赖与构建材料逐项一致 | 审计 BR | 静态材料比对 (`adb5660` 与 HEAD 的 deps/build 材料) |

## 影响判断: 证据目录位置

`docs/changes/tool-cli/verify-2028383-v1/` 放在仓库内. 依据:
- `build.sh` 只编译 `tool.py`; `prepare.sh` → `tools/build_manifest.py` 只读 `tool.py` 并写 `dist/app.txt`, 不扫描 `docs/`.
- pytest 无配置, 默认只收集 `test_*.py`/`*_test.py`; 本证据目录只放 `.md`/`.log`/`.txt`, 约定不产生任何 Python 文件.
- `docs/` 不在 .gitignore, 故证据文件会作为未跟踪文件出现在 `git status`; 报告收尾会注明这是本轮唯一新增.

## 分组与人数

- 场景组划分: G1 问候 (`AC-001-1`, `AC-001-2`, `AC-003-1`, 导出复用问候逻辑), G2 统计 (`AC-002-1`, `AC-002-2`), G3 审计 (`BR-002`).
- 当轮可用非作者验收者: 2 名 (用户授权上限).
- 计划人数: **1 名**, 由它依次完成全部 6 项.
- 只派一人的依据:
  1. 重复准备成本大于并行收益: 每个新会话都要重新读同一份 PRODUCT.md, 确认同一工作区, 并按 README 各跑一次 `bash prepare.sh` 生成同一份 `dist/app.txt`; 而实际工作量为 6 条秒级命令, 并行省下的时间小于新会话启动与重复准备的成本.
  2. 两个场景组占用同一份资源: 同一入口 `tool.py`, 同一工作区, 同一份构建产物与 `notes.txt`; 拆分后仍要在同一份状态上读写, 不构成真正的资源隔离.
  3. 不逐条 AC 开会话, 也不为用满名额制造重复劳动.

## 验收者

| 会话 | 创建时间 | 承接标准 | 未参与事实 |
| --- | --- | --- | --- |
| `S-verifier-1` (会话 `01a15426-b0b5-7604-80c4-85011cab7cae`, pane `w1J:p30`) | 2026-10-19T12:33:04Z (20:33:04 +0800) | AC-001-1, AC-001-2, AC-002-1, AC-002-2, AC-003-1, BR-002 | 本轮新建 pi 会话, 创建时间晚于实现提交 `2028383` (2026-10-19 20:27:16 +0800); 非 `/tmp/orchestra-03/author` 会话, 未继承实现过程; 会话记录只有 read/bash/write (write 仅证据目录), 无 edit, 无 git commit |

## 证据目录约定

- 每项一个原始输出文件 (`*.log`), 内含命令, 原始 stdout/stderr, 退出码, 时间戳.
- `RESULT.md` 汇总逐项结论; 不写明文密钥.
- 临时文件只允许放在本目录内; 不改产品代码, 测试, 配置.
