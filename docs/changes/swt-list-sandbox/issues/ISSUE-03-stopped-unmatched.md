## 父级

- `../EXECUTION.md`

## 执行

- [x] 已实现

## 要构建什么

非 running 与记录缺失分支的条目呈现: 非 running 容器 `access-entries` 不含任何可达入口, 只含状态行与 resume 命令提示行; lifecycle=retired 条目附 仅可终结 标注; record-state=missing 条目附 本记录根无记录 标注 + 缺项 reason 行 + `podman rm <名>` 清理指引行且无 terminate 指引; record-state=corrupt 条目附 记录不可解析 标注, 同 reason 纪律. 适合 AFK: 分支行为全部在 AC-004/AC-005 场景中固定.

## 覆盖依据

- Product: `docs/changes/swt-list-sandbox/PRODUCT.md`, AC-004, AC-005
- Technical: `docs/changes/swt-list-sandbox/TECHNICAL.md`, 模块接口 (M1 不变量: 非 running 无可达入口 / podman rm 指引 / 无 terminate 指引), 测试接缝

## 相关决策

- `docs/changes/swt-list-sandbox/DECISIONS.md`: D003, D011

## 允许范围

- `swt.py` 内 list 实现的分支呈现部分 (状态行/resume 提示/标注/指引行拼装).
- 扩展 `tests/test_swt_list.py`.

## 禁止范围

- running+matched 的入口组装 (归 ISSUE-02, 本切片不得触碰其行集).
- 修改 terminate/resume 子命令本体.
- 改动 LIST schema 已定字段.

## 代码定位提示

- resume 命令提示的命令形态参考 SKILL.md 恢复节: `uv run python scripts/swt.py resume --name <容器名>`.
- retired 判定: runtime 容器记录 `retired` 字素 (参考 `podman_container_state` 的 lookup 用法, 约 705 行).
- record-state 判定已在 ISSUE-01 落地, 本切片只消费其结果拼行.

## TDD 切片

- TS-031:
  接缝: 接缝 B (podman fake-run), `tests/test_swt_list.py`.
  测试用例: TC-031.
  先写的失败测试: `test_stopped_no_reachable_entries_with_resume_hint` — fake exited+matched 容器, 断言 access-entries 不含 ssh/URL/herdr/直飞任何可达行, 含状态行与 resume 提示行; retired 容器条目含 仅可终结.
  最小绿色实现范围: 非 running 分支与 retired 标注.
  不得测试: 行序.
  覆盖: AC-004.
- TS-032:
  接缝: 同上.
  测试用例: TC-032.
  先写的失败测试: `test_unmatched_reason_and_podman_rm_guidance` — fake label 在而记录缺失容器, 断言 本记录根无记录 标注 + reason 行 + `podman rm` 指引行, 全条目无 terminate 字样; 记录损坏容器断言 记录不可解析 标注同纪律.
  最小绿色实现范围: missing/corrupt 分支行.
  不得测试: 未确认文案细节 (只断言关键词在场/缺席).
  覆盖: AC-005.

## 验证入口

- `uv run --with pytest pytest -m "not e2e" -q tests/test_swt_list.py` 全绿 (含前序用例不回归).

## 风险提示

- "无可达入口" 断言要覆盖全部入口类型 (ssh/三种 URL/herdr/直飞), 漏一类即假绿.
- missing 与 "在别的 records-root" 不可区分是既定事实 (D006), 文案只能写 本记录根无记录, 禁止写 孤儿/全局无记录.

## 停止条件

- 需要改变任一 Spec/决策/issue 边界时停止.

## 适合 AFK 的原因

分支输入输出全部由 fake fixtures 与场景固定, 无自由决策.

## 验收标准

- [ ] 停止容器无可达入口 + resume 提示 + retired 标注 (TC-031).
- [ ] missing/corrupt 标注 + reason + podman rm 指引 + 无 terminate (TC-032).
- [ ] 前序用例不回归.

## 被阻塞于

- ISSUE-01 (`issues/ISSUE-01-list-skeleton.md`)
