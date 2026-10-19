# board d2e680c 独立验收: 派工计划

- 目标提交: `d2e680ce826388a3051dec79d7ff68fc68cc6fc1` (HEAD: t1, 2026-10-19T15:19:48Z)
- 判据来源: `docs/changes/board/PRODUCT.md` (确认标记 `<!-- confirmed-flow: v1 -->`)
- 本轮证据目录: `docs/changes/board/evidence/board-d2e680c-r1/` (新建, 不覆盖 `board-dep-1.2-run`)
- 计划时间: 2026-10-19T15:42Z

## 证据目录影响判断

- 项目无构建脚本, 无自动化测试, `app.py` 只读取自身与 `vendor/`, 不读取 `docs/`.
- `docs/` 进入 git 跟踪范围, 但不参与构建/测试发现/运行输入, 因此证据可放仓库内 `docs/changes/board/evidence/` 下.
- 证据只允许新增本目录文件; 源码, 配置, 测试, Spec 不得改动.

## 必验清单 (4 项, 照 PRODUCT.md 原文)

| 编号 | 原文要点 |
| --- | --- |
| AC-001-1 | 假定实例 board 在 127.0.0.1:18201 运行且 health 返回 `ok instance=board`; 运行 `python3 app.py status --port 18201`; 输出含 `instance=board`, `state=ready`, `version=relay-v2` 且退出码 0 |
| AC-002-1 | 假定实例 board 在 127.0.0.1:18201 运行; 运行 `python3 app.py report --port 18201`; 输出形如 `relay-report instance=board version=relay-v2 dep=<n>` 且退出码 0; dep 与 `deps.txt` 一致 |
| AC-003-1 | 假定 relay 127.0.0.1:18290 监听且实例 board 在 18201 运行; 运行 `python3 app.py sync --port 18201 --relay-port 18290`; 输出含 `sync-ok instance=board` 与 `relay=ok` 且退出码 0 |
| BR-001 (审计) | status 与 report 的 version 字段只取自实例自身, relay 服务不可用时也不改变 |

## 分组, 人数与资源

- 全部 4 项共用同一个实例 (127.0.0.1:18201, instance=board) 与同一条 relay 依赖 (127.0.0.1:18290).
  端口与实例由 PRODUCT.md 原文指定, 不能换端口; 拆成多组会争用同一实例端口, 或每组重复同一份启动准备.
- 结论: 单组, 派 1 名验收者依次做完; 无并行收益, 不派第二人.
- 当轮可用非作者会话: 1 名新开 (本轮新建).
- 共用准备: 实例启动与健康检查由该验收者做一次, 自己复用, 无跨会话共享材料.

## 每项材料来源

| 编号 | 来源 | 理由 |
| --- | --- | --- |
| AC-001-1 | 本轮实跑 (主证据) + 旧观察作佐证 | BR-001 必须在 relay 不可用时运行 status, 同一命令顺带覆盖本场景, 无额外准备成本; 旧 `board-dep-1.2-run` 记录须核对适用条件后引用 |
| AC-002-1 | 本轮实跑 (主证据) + 旧观察作佐证 | 同上; report 的 dep 值还要与当前 `deps.txt`/`vendor/relaylib.py` 比对 |
| AC-003-1 | 本轮尝试实跑 | 旧记录当时 relay 在监听, 现在 18290 无监听; 环境条件已变, 旧观察不适用. 若确实无 relay, 按缺依赖服务记未验证, 禁止自建 relay 桩/替身 |
| BR-001 (审计) | 本轮实跑 (relay 不可用前后 status/report 的 version 对照) + 旧观察 (relay 可用时同代码) | 断言运行过程, 需实际记录; 只读代码只能标推断, 不算通过 |

## 旧材料适用性核对点 (交由验收者执行)

- 旧记录: `docs/changes/board/evidence/board-dep-1.2-run/` (1dbbbe1, 2026-10-19T15:19:48Z, dep 1.2).
- 必查: `git diff --stat 1dbbbe1..HEAD` 是否只动文档; `deps.txt` 与 `vendor/relaylib.py` 版本是否仍为 1.2; 配置/启动方式是否改变; 环境依赖 (relay, 实例) 是否仍在.
- 只改文档时该证据适用范围不变, 直接引用; 条件变化 (尤其 relay 不在) 则不得引用该场景的旧结论.

## 写入与清理

- 实例数据目录用 README 的 `runtime/board` (`.gitignore` 已忽略 `runtime/`).
- 结束时停止验收者自己启动的实例, 记录清理命令与 18201 无残留监听的检查.
- 不提交, 不推送, 不改产品代码/配置/测试/Spec.
