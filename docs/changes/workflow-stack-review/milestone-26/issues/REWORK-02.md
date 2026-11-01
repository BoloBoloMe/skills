# REWORK-02 返工复审发现项

## 父级
- `../../milestone-26/REVIEW-rework.md` (P-1, P-2, P-4, P-5, P-6, P-7)
- `issues/REWORK-01.md`

## 执行
- [ ] 已完成
- [ ] 派工前复核: HEAD; `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest --collect-only -q` 条数.

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

## 停止条件
需要改 spec 或产品行为; 需要真实 podman/出网. 遇到停手并 mailbox request 上报.
