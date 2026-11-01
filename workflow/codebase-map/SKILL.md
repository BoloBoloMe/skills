---
name: codebase-map
description: 把代码库结构与依赖分层可视化成可交互页面, 手动用 build/serve/stop 三子命令分析并托管, 不被任何 skill 调用.
disable-model-invocation: true
---

# 代码库结构可视化

纯手动工具: 只由用户手动调用, 任何 skill (含 to-spec) 都不调用它. 职责只有一件事: 出"代码库结构与分层"的可视化页面, 不做架构评审, 不产重构建议, 不参与验收判断.

## 用法 (三子命令)

调用式:

```
python3 <skill 目录>/scripts/codebase-map.py <build|serve|stop> ...
```

宿主有 uv 时 `uv run python <skill 目录>/scripts/codebase-map.py <build|serve|stop> ...` 等价. 三个子命令各管一件事, 三者不合并:

- `build <目标目录> [--exclude <glob>]... [--json]`: 只分析并产出数据, 不起服务. 权威数据落在目标库的 `.codebase-map/cc.json`, 副本复制进服务根供页面读取. `--exclude` 以 glob 语义追加排除规则, 可多次; 默认已排除 `node_modules` `.git` `dist` `build` `target` `vendor` 与 `.codebase-map`. `build --json` 的 `stats.notes` 固定带三句分母说明 (测试与 build 目录默认不扫, 零声明文件不进依赖树, 分析端自带忽略规则单列为工具默认过滤), 人类可读输出逐行打印.
- `serve [--port <N>] [--address <IP>] [--json]`: 起或复用常驻服务并交付局域网 URL 与交付说明. 服务单例, 端口默认沿用上次端口 (首次为 8090).
- `stop [--json]`: 停整个服务, 没有"只停某一个库"的语义; 没有实例时幂等成功. 停机后旧 URL 立即失效, 服务根与缓存里的数据副本保留.

`--port` 只在没有存活实例时生效, 有实例要先 `stop` 再换端口; `--address` 只作用于本次调用, 不落盘.

用法例子 (demo 与 other 是中性占位名):

```
python3 <skill 目录>/scripts/codebase-map.py build /path/to/demo
python3 <skill 目录>/scripts/codebase-map.py build /path/to/demo --exclude "docs/**" --json
python3 <skill 目录>/scripts/codebase-map.py serve
python3 <skill 目录>/scripts/codebase-map.py serve --port 8091
python3 <skill 目录>/scripts/codebase-map.py serve --address <已确认局域网地址>
python3 <skill 目录>/scripts/codebase-map.py stop
```

`build` 只在宿主机使用: 在沙箱容器内执行会被拒绝, 不降级.

## build 持锁窗口

`build` 全程持有运行时文件锁: 取锁后要经过初始化与三步分析, 一直到写完副本与登记 state.json 才释放. 分析一个库期间, 同时执行的 `serve` 与 `stop` 会等锁, 等待超过 30 秒就报 `internal_error` 失败退出. 建议错开时间操作: 等正在跑的 `build` 结束, 再执行 `serve` 或 `stop`.

## 交付纪律

- 交付给用户的是局域网 URL: 基址 `http://<已确认地址>:<端口>/` 加每个数据键的完整 URL `http://<已确认地址>:<端口>/?file=<键>`, 全部取自 `serve` 的输出; 不给 loopback 地址, 不给文件路径, 不让用户自己拼.
- 交付消息原样转述 `serve` 输出摘要里 `delivery_notes` 的四类说明, 不改写其中的数字与判断, 不说分层完全可信:
  1. 层号/环/向上依赖在官方依赖视图里看; 3D 城市图按官方默认指标.
  2. 依赖抽取完整性未量化, 不能当作分层完全可信.
  3. 分母口径: 依赖树里的文件数 (输出里逐键列出); 零声明文件不进依赖树, 测试与 build 目录默认不扫, 分析端自带忽略规则单列为工具默认过滤.
  4. 未解析扩展名 (`unparsed_note`, 第 4 类): 逐库列出没进依赖树的扩展名与数量; 某库没有未解析扩展名时写明"没有未解析扩展名"; 记录里缺统计记录 (老数据) 的库写明缺少统计记录, 重新 build 可补.

## 地址来源与缺值出口

- 已确认局域网地址记录在 `~/.agents/sandbox-worktree/lan-address`, `serve` 只读该文件, 这是唯一自动来源.
- 记录缺值且未传 `--address` 时, `serve` 报阻塞: 输出 `address_missing` (code 为 `no_confirmed_address`) 与候选地址列表; 服务照常起, 退出码仍为 0, 但输出里没有 url.
- 用户确认某个候选地址后, 用 `serve --address <已确认地址>` 重新交付; `--address` 只属于本次调用, 不写进任何文件.
- 不猜地址: 不用回环地址, 主机名或文件路径顶替, 也不回写 `~/.agents/sandbox-worktree/lan-address`.

## 失败出口清单

错误码与下一步动作 (与 `scripts/` 下代码一致):

| 错误码 | 下一步动作 |
| --- | --- |
| `container_not_supported` | 改在宿主机执行; 不降级, 没有容器内调用宿主服务的接口. |
| `target_missing` | 确认目标库路径后重试. |
| `podman_missing` | 先装 podman, 确认 `podman --version` 可用后重试. |
| `image_unavailable` | 补网络或确认能访问镜像 registry 后重试; 不用其它镜像顶替. |
| `image_digest_mismatch` | 用 `podman pull` 更新到官方 2.3.0 镜像后重试; 不采信镜像内自报版本号. |
| `frontend_unavailable` | 确认宿主能访问 GitHub release 后重试; 不用本机其它前端顶替. |
| `frontend_hash_mismatch` | 删掉 `cache/frontend/` 目录后重跑 build 重新下载. |
| `gate_failed` | 在目标库补出依赖边与分层后重跑 build; 分母与零声明清单看 build 输出的 stats. |
| `no_data_keys` | 先 build 生成数据副本, 再 serve (两类文案区分"还没 build"与"副本已删", 处理都是重新 build). |
| `port_in_use` | 处理端口占用: 确认占用者后二选一, `serve --port <N>` 换端口, 或先处理占用者再重试. |
| `instance_running` | 已有存活实例: 先 stop, 再用 `serve --port <N>` 换端口; 或不带 `--port` 直接复用. |
| `state_mismatch` | 状态不一致交用户裁决: 先核实 pid/端口归属, 确认后按"状态复原步骤"处理. |
| `stop_failed` | 稍后再次执行 stop; 持续失败按日志排查该进程为何不退出. |
| `internal_error` | 保留 stderr 全文并报告. |

`address_missing` 不是失败: `serve` 成功但缺已确认地址时的阻塞出口, 处理见上一节.

## 状态复原步骤

删掉 `~/.agents/codebase-map/` 等于放弃当前实例 (状态记录与运行时产物一起消失). 复原方式二选一:

- 数据副本还在 (服务根里仍有 `.cc.json`): 重新执行 `serve`, 副本原地复用.
- 数据副本也没了: 重新执行 `build` 重建.

`state_mismatch` 一类状态不一致的收尾都是: 核实 pid/端口归属, 交用户裁决后按本节复原.

## 数据副本清理

- 清理入口全在服务根 `~/.agents/codebase-map/serve-root/`: 手动删掉某个库对应的 `.cc.json` 文件, 或删掉整个目录按需重建.
- `build`, `serve`, `stop` 都不会自动删除任何库的副本, 也没有"只留最近一个"的清理; 删掉副本不会自动恢复, 需要重新 build.

## 版本口径

- 分析端: 官方镜像 `codecharta/codecharta-analysis:2.3.0`; 版本以镜像的单架构清单 digest 核对 (多架构清单 digest 只记录), 不采信镜像内自报的版本号.
- 前端: 官方 `vis-2.9.1` 英文原版 (`web.zip`, sha256 校验); 三子命令不做汉化.
- 首次初始化 (build 发现缺镜像或缺前端时) 会把服务根的前端整体换成官方英文 vis-2.9.1; 若要用汉化界面, 在初始化之后用 `tools/stage.py frontend` 重新铺设; 这两件事不要同时进行. 这是既有事实, 不是新能力.

## 使用纪律

- 服务无认证无 TLS, 绑定 `0.0.0.0`, 局域网内任何主体都能读服务根的全部内容; 只分析愿意公开的库, 不把仓库根或敏感目录当分析目标.
- 只在宿主机使用, 不在沙箱容器内运行.

## 汉化构建链

本 skill 另含一套汉化构建资产, 与三子命令并存:

- `tools/build-zh.sh`: 前端汉化构建流水线 (克隆钉死的上游 tag -> 三通道替换 -> npm build -> 渲染冒烟), 产物在 `~/.agents/codebase-map/cache/`.
- `tools/stage.py`: 把前端产物与数据副本铺进服务根 (`frontend`/`data` 两个子入口).
- `i18n/`: 三通道词表 (模板 / .ts 白名单 / 绑定内字面量; 同一术语只用一个译法).
- `README.md`: 该链的操作手册 (分析端与前端命令, 数据交付, 升级流程, 已知坑).

这条链做汉化构建与 serve-root 铺设, 细节见 `README.md`; 常驻服务与交付走上面的三子命令.
