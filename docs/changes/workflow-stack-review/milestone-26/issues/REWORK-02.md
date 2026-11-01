# REWORK-02 返工复审发现项

## 父级
- `../../milestone-26/REVIEW-rework.md` (P-1, P-2, P-4, P-5, P-6, P-7)
- `issues/REWORK-01.md`

## 执行
- [x] 已完成
- [x] 派工前复核: HEAD = d6e72e60d0924e79344813fd9b830ee8f76ce6ae; `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest --collect-only -q` 条数 = 943.
- [x] 完成后 collect 条数 = 944 (增量 +1 = P-7 新用例); 套件 79 passed (基线 78).

## 要交付什么

只修复审确认的可移植性与覆盖范围问题, 不动产品行为, 不放宽断言.

1. **P-1 (必须)**: `tests/test_cli_output_shape.py` 的 `test_podman_missing_message_names_no_podman` 现在用 `PATH=/usr/bin:/bin` 表达"没有 podman". 宿主 `/usr/bin/podman` 常见, 会让该用例在宿主上红或真跑 build. 改为构造临时目录作 PATH: 只软链真实存在的 `sh` 与 `mount` (以及解释器需要的其它必要二进制, 按实测最小集), 不含 podman; 若临时 PATH 里缺必要二进制导致无法起子进程, 用例应显式失败并说明原因, 不静默通过.
2. **P-2/P-3 (文档)**: 同一用例的 docstring 写明前置条件 (需要 `unshare`, 需要允许非特权 user namespace, 用于在容器里藏 `/run/.containerenv` 以到达宿主前置链), 并写明不满足前置时的表现 (失败而不是假通过); 在 `tests/README.md` 的映射行或 `tests/run` 注释里注明该套件含此环境构造 (分层偏移备案).
3. **P-4 (措辞)**: `codemap_service.py` `_apply_delivery` docstring 末句改为"裸地址字段与 `--address` 的值不落盘 (按已确认记录来源组装的 `last_url` 是交付 URL, 属记录重算结果)".
4. **P-5 (映射)**: `tests/README.md` 与 `tests/run` 的 codebase-map 映射补上 `workflow/codebase-map/SKILL.md` 与 `workflow/codebase-map/README.md` -> `workflow/codebase-map/tests` (文本契约用例约束它们).
5. **P-6 (明确范围)**: `tests/test_skill_docs.py` 的 D-1 守卫: 保留当前"失败出口表格首列"口径, 但把范围写进断言失败信息与函数 docstring, 说明它只查表格首列而非全文 token; 并让 collector 同时收 `no_confirmed_address` 这类非 `error_result` 产生的码 (从 `codemap_common.py` 的常量或引用处以静态解析取到), 避免将来写进表格会假红.
6. **P-7 (覆盖)**: 补一条人类可读形态的换端口断言: 用非 `--json` 形态跑一次换端口, 断言输出含"旧地址已失效"与端口信息.

## 允许范围
`workflow/codebase-map/tests/test_cli_output_shape.py`, `tests/test_skill_docs.py`, `workflow/codebase-map/scripts/codemap_service.py` (仅 docstring), 仓库根 `tests/README.md` 与 `tests/run`.

## 禁止范围
不改任何产品行为与 `--json` 字段; 不加 skip/xfail; 不放宽断言; 不处理 E-1..E-4 与 Q-1..Q-5 (待发起方裁决); 不改 m21 的 tools 与 i18n.

## 验证契约
- 变更类型: 非行为改动 (测试与文档) 加 1 条测试覆盖补充 (P-7).
- 验证要求/证据: `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest workflow/codebase-map/tests` 全绿; 收集条数增量 = 新增用例数; 用一个"PATH 里塞假 podman"的负向自测证明 P-1 的新构造不再依赖系统 PATH 内容; 映射双向一致核对.

## 交付证据

原始记录: `/tmp/m26-rw02/` (pytest-full.log, collect-count.txt, p1_probe.py, p1-negative-selftest.log, p1-pytest-polluted-path.log, p6-collector-diff.txt, p5-mapping-check.txt, tests-run-fast.log, p7-single.log).

- **P-1**: `test_cli_output_shape.py` 新增 `_no_podman_path()`: 临时目录只软链 unshare/sh/mount 三个真实存在的二进制 (shutil.which 找源, 缺任一即断言失败并说明前置缺失), 子进程 env PATH 指向该目录; 并断言目录内容恰为这三个名字 (不含 podman). 不再用 `PATH=/usr/bin:/bin`, 构造与系统 PATH 目录内容无关. 子进程无 --json 输出时显式 AssertionError 说明 unshare/userns 前置原因, 不静默通过.
  负向自测 (假 podman = `/tmp/m26-rw02/fakebin/podman`, --version 应答正常): (1) 探针: 外层 PATH 前插假 podman 目录后, 新构造 (env PATH=临时目录) 仍报 `podman_missing`; 同污染下旧构造 `PATH=$FAKEBIN:/usr/bin:/bin` 报 `image_unavailable` (假 podman 被当真, 对照有效, 复现评审实验). (2) 污染 PATH 下跑整个 test_cli_output_shape.py = 5 passed.
- **P-2/P-3**: 该用例 docstring 写明前置 (unshare/sh/mount 在场; 非特权 user namespace; seccomp 不拦 mount) 与不满足时的表现 (显式失败, 不是假通过); `tests/README.md` 映射行与 `tests/run` 注释均注明该套件含 unshare mount ns 环境构造用例, 快层偏移备案.
- **P-4**: `codemap_service.py` `_apply_delivery` docstring 末句逐字改为 "裸地址字段与 --address 的值不落盘 (按已确认记录来源组装的 last_url 是交付 URL, 属记录重算结果)."
- **P-5**: `tests/README.md` 映射行与 `tests/run` RULES 补 `workflow/codebase-map/SKILL.md` 与 `workflow/codebase-map/README.md` -> `workflow/codebase-map/tests`. select_suites 实验: 两文件各自命中该套件; 原有 scripts/tests/swt/present/GLOBAL 命中不变; 近名 (workflow/navigate/SKILL.md, scriptsX) 不误伤; `./tests/run --fast` 端到端选中该套件并 79 passed.
- **P-6**: `collect_code_error_codes()` 增加 dict 字面量 key 为 "code" 的字符串值收集分支 (收 `no_confirmed_address`; 值为变量的回放位如 error_result/_write_startup_error 的 payload 不收); `doc_error_codes` docstring 与主用例 docstring/断言失败信息均写明"只查失败出口表格首列, 不扫全文 token". 实测: collector 全集 15 码 (原 14 + no_confirmed_address), doc 表格 14, 差集空; 编造码负向自测仍被抓; 把 no_confirmed_address 写进表格不假红.
- **P-7**: `test_cli_output_shape.py` 新增 `test_port_change_human_output_reports_stale_address_and_port`: record 来源 --json 首启 -> stop -> 非 --json `serve --port` 换端口, 断言 stdout 含 "旧地址已失效", "port: <新端口>", 旧交付 URL (previous_url 铺开), rc=0. 单条 1 passed.

验证汇总: `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest workflow/codebase-map/tests` = 79 passed (基线 78, +1 = P-7); 全仓 collect 944 (基线 943, 增量 +1). 未加 skip/xfail, 未放宽任何既有断言, 未改产品行为与 --json 字段.

## 停止条件
需要改 spec 或产品行为; 需要真实 podman/出网. 遇到停手并 mailbox request 上报.
