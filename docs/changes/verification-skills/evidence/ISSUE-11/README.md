# ISSUE-11 演练总表

待测技能: `workflow/create-verification-skill/SKILL.md` (分支 `issue/11`, 工作树 `/home/bolo/Workspace/skills/skills-v2.worktrees/ISSUE-11`).

## 宿主与运行时

- pi 1.3.0 (`pi --version`), herdr 0.9.4 client/server (protocol 22).
- 会话模型: `cli/deepseek-v4.1-flash-expires-on-0910`, thinking `high`, 启动参数 `-a` (一次性项目信任).
- 启动命令: `herdr agent start <名> --kind pi --pane <pane> -- --provider cli --model deepseek-v4.1-flash-expires-on-0910 --thinking high -a`.
- 提交渠道: `herdr pane send-text <pane> '<文本>'` + `herdr agent send-keys <名> "alt+\\"` (pi 的提交键, 见 use-herdr/PI.md).

## 待测源版本

技能在演练中迭代过三版, 三版的正文都能在下面的会话转录里核对.

| 版本 | sha256 | 用在哪 |
| --- | --- | --- |
| v1 | 未单独留存, 全文在两个会话转录的 `<skill ...>` 块里: `raw/TS-001-green-session-i11-gen1-pane.txt`, `raw/TS-002-red-transcript-i11-gen2.txt` | 红阶段 (TS-002 red, TS-003 red), TS-001 第一次绿 |
| v2 | `460b9067e058f2f65b8d31a0fc96bb2e78331aa3fcf1a0c61b55fbad4019c35d` (`skill-versions/v2-SKILL.md`) | TS-001 复跑, TS-016-2, AC-017, AC-018-1, AC-018-2 首轮 |
| v3 | `ffa308ac02c957a424a9ebffd0c008d1dffe667e29338e14c63fb0793a6ade47` (`skill-versions/v3-SKILL.md`, 与分支当前文件一致) | 加 frontmatter 规则后的 AC-018-2 复跑 |

v2 与 v3 的差别只有两处: 生成物的 `description` 含冒号时要加引号; 加载失败时先修配方再重跑, 不能把"命令没展开"当成跑过.

## 演练会话清单

| 会话名 | tab | 临时项目 @ 起始提交 | 加载的技能版本 | 干什么 | 原始记录 |
| --- | --- | --- | --- | --- | --- |
| i11-red | w1J:t26 | p1-dual @786baa1 | 无 (未安装) | TS-001 红: 技能不存在时点名加载失败 | `raw/TS-001-red-session-i11-red-pane.txt` |
| i11-gen1 | w1J:t28 | p1-dual @786baa1 | v1 | TS-001 首轮绿 | `raw/TS-001-green-session-i11-gen1-pane.txt` |
| i11-gen2 | w1J:t29 | p2-gaps @add5a22 | v1 | TS-002 红: 生成者自己跑 | `raw/TS-002-red-transcript-i11-gen2.txt` |
| i11-gen3 | w1J:t2D | p3-buildfail @5d1df07 | v1 | TS-003 红: 无构建受阻规则 | `raw/TS-003-red-transcript-i11-gen3.txt` |
| i11-gen3b | w1J:t2F | p3-buildfail @5d1df07 | v1 | TS-003 红: 明说"可以改项目任何文件" | `raw/TS-003-red-transcript-i11-gen3b.txt` |
| i11-gen4 | w1J:t2H | p1-dual @786baa1 | v2 | AC-016-1 正式证据 | `raw/TS-001-green-v2-transcript-i11-gen4.txt` |
| i11-gen5 | w1J:t2J | p2-gaps @4057bb5 | v2 | AC-017 生成 + 派工 + 汇总实跑记录 (两轮) | `raw/TS-002-017-green-transcript-i11-gen5.txt` |
| i11-ver1 | w1J:t2P | p2-gaps @4057bb5 | 生成的 verify-fixture | AC-017-1/2/3: 未参与编写的会话按名加载并实跑 | `raw/TS-002-017-verifier-transcript-i11-ver1.txt`, `raw/ver1-report.md` |
| i11-ver2 | w1J:t2S | p2-gaps @5c0dd32, cwd `web-console/` | 生成的 verify-fixture (同名冲突) | TC-104: 同名冲突与未加载 | `raw/TC-104-ver2-*.txt` |
| i11-gen6 | w1J:t2T | p4-draft @44ba7bc | v2 | AC-016-2: 只有草稿 PRODUCT | `raw/TS-001-draft-product-transcript-i11-gen6.txt` |
| i11-gen7 | w1J:t2V | p3-buildfail @5cd1f47 | v2 | AC-018-2 首轮 (暴露 frontmatter 加载失败) | `raw/TS-003-loadfail-transcript-i11-gen7.txt` |
| i11-ver3 | w1J:t2W | p3-buildfail @5cd1f47 | 首轮生成的 verify-fixture (未被加载) | 加载失败下的实跑, 只报构建受阻 | `raw/TS-003-loadfail-verifier-transcript-i11-ver3.txt` |
| i11-gen7b | w1J:t2X | p3-buildfail @2b41b8f | v3 | AC-018-2 复跑 + 处理子会话报告 (两轮) | `raw/TS-003-green-transcript-i11-gen7b.txt` |
| i11-ver4 | w1J:t2Y | p3-buildfail @2b41b8f | 复跑生成的 verify-fixture | AC-018-2: 子会话报构建受阻, 并给出真实 location | `raw/TS-003-green-verifier-transcript-i11-ver4.txt` |

## 临时项目

全部在 `/tmp/orchestra-11/`, 都是独立 Git 仓库, 起始提交见上表.

- `p1-dual`: 已确认 PRODUCT 只覆盖功能 A (命令行 + 网页), 仓库另有 tags, import-legacy, export_csv, stats 四个未涉及功能; 含 `deploy/global-skills/verify-fixture/SKILL.md` 作为全局部署副本替身 (不被 pi 发现).
- `p2-gaps`: PRODUCT 覆盖功能 A (命令行 + 网页), B (tags 命令行), C (import-legacy 命令行, 需上游导出文件 `seed/legacy-export.json`, 仓库不含), 用于 AC-017 与 AC-018-1.
- `p3-buildfail`: Rust 命令行应用, 构建需要 `cargo`, 本机没有, 用于 AC-018-2.
- `p4-draft`: 与 p1 同应用, 但 `PRODUCT.md` 状态是草稿, 用于 AC-016-2.

## 证据文件

- `generated/`: 各轮生成出来的 `verify-fixture/SKILL.md` 原文 (含红的失败产物).
- `raw/`: 会话转录 (由会话 jsonl 转换, 含工具调用与原命令), 终端快照, 派工回收的报告原文.
- `raw/verifier-evidence/`: 两个实跑会话落在 `/tmp/verify-fixture-evidence/` 的取证文件 (原样拷贝).
- `skill-versions/`: v2 与 v3 的技能源码快照.
