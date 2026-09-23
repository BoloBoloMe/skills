## 父级
- `../EXECUTION.md`

## 执行
- [ ] 已实现

## 要构建什么
拉窗加固 + 文档批: (1) pull-window 指令集动态绑定放宽: `container` 字段为投信方 session id **或其容器名**皆可命中, 限频键统一到容器标识; (2) 拉窗指令形状扩展为可带 `url` 参数, 设备侧按信里 url 拉起, 不猜端口; (3) reference/pull-window.md: chromium 模板强制 `--user-data-dir`, 音频 `-R` 标可选并给退化写法; (4) reference/mailbox.md: 反向隧道标准配方 (含远端标记文件, sshd ClientAliveInterval 提醒), 跨机换址联动清单 (防火墙白名单与邻居地址同时改); (5) 记录已验证 waypipe 版本组合 (0.8.4 / 自编译 minimal / 0.11.0 混用实测出窗). 适合 AFK: 绑定规则与文档清单已定.

## 覆盖依据
- Product: `../PRODUCT.md`, AC-029, AC-030
- Technical: `../TECHNICAL.md`, 模块接口/安全策略 (指令集)
- 审计: BR-008

## 相关决策
- `../DECISIONS.md`: D011 (B5/E1/E2/E4/E5)

## 允许范围
- `workflow/mailbox/scripts/mailbox.py` (`_pull_window_hit`, `pull_window_container`/取信门禁段)
- `workflow/mailbox/reference/pull-window.md`, `reference/mailbox.md`
- `tests/test_mailbox_whitelist.py`, `test_mailbox_pullwindow.py`

## 禁止范围
- 指令集白名单机制本身 (不新增成员)
- 拉起后校验回告 (E3 缓)
- 防多窗自动合并 (只写文档配方)

## 代码定位提示
- mailbox.py: `_pull_window_hit` (恰含 tool/container 两键校验), `pull_window_container`/`gate_pull_window` (取信侧门禁), `PULL_WINDOW_TOOL`
- 容器名来源: session id 形态 `<容器名>-<8hex>`, 容器名 = 前缀
- 测试: test_mailbox_whitelist.py 的门禁测试 (ADR-0011 要求成员变动必过)

## TDD 切片
- TS-001:
  接缝: 指令集校验函数.
  测试用例: TC-047.
  先写的失败测试: `test_pull_window_hit_by_container_name` — container 填容器名也命中直批; 现只认 session id, 失败.
  最小绿色实现范围: 绑定判定放宽 + 限频键统一.
  不得测试: 白名单其他成员.
  覆盖: AC-029 (容器名行).
- TS-002:
  接缝: 同上.
  测试用例: TC-048.
  先写的失败测试: `test_pull_window_other_session_downgrades` — 填他人 session/容器名降级 request; 回归锚.
  最小绿色实现范围: 保持.
  覆盖: AC-029 (降级行).
- TS-003:
  接缝: 拉窗信解析.
  测试用例: TC-049.
  先写的失败测试: `test_pull_window_url_param` — 带 url 的拉窗信设备侧取信输出含该 url; 现无 url 概念, 失败.
  最小绿色实现范围: 指令形状扩展 (url 可选) + 取信呈现.
  覆盖: AC-030.
- TS-004:
  接缝: 文档 grep.
  测试用例: TC-050 (BR-008).
  先写的失败测试: `test_docs_contain_recipes` — pull-window.md 含 --user-data-dir 与音频退化; mailbox.md 含反向隧道配方与联动清单与版本组合; 未写, 失败.
  最小绿色实现范围: 文档落笔.
  覆盖: BR-008 (审计).

## 验证入口
`uv run pytest tests/ -k "pullwindow or whitelist" -q` 全绿 (门禁测试必过, ADR-0011).

## 风险提示
绑定放宽扩大直批面: 容器名 = session id 前缀的推导必须精确, 误放宽 = 他人容器可拉窗; 限频键统一后注意新旧键衔接.

## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.

## 适合 AFK 的原因
绑定规则/文档清单/版本组合全部已定.

## 验收标准
- [ ] 容器名或 session id 均可命中拉窗指令, 他人降级
- [ ] 拉窗信带 url 设备侧按 url 拉起
- [ ] 四份文档内容落笔且 grep 测试过
- [ ] 门禁测试全绿

## 被阻塞于
- ISSUE-01
