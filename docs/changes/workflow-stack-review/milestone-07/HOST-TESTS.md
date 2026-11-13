# milestone-07 宿主补跑记录

## 来源与目标

宿主具体会话 `01a18814-6e80-744f-a09f-346ba7b25522` 来信 `228ebc1d16484c86a407f361c086e9fd` 报告独立实跑. 本会话已实际读取对方放进容器的两份原始日志, 原样存为 `HOST-PYTEST.log` 与 `HOST-BASELINE.log`; 下文区分日志观察, 宿主声明与结论限制.

- 目标: `c77f6af446d294c3d498c570feb88bd41fe79bb6`.
- 宿主报告的环境: rootless podman + uv, pytest 9.2.0, 独立干净 worktree `/tmp/swt-m07-pytest/repo`, 结束后已移除该 worktree.
- 宿主报告的命令: `uv run --no-project --with pytest python -m pytest -m "not e2e" -q`.
- 宿主报告的时间: 2026-10-31T15:44:28Z 至 2026-10-31T15:48:57Z.
- 日志观察: `7 failed, 778 passed, 4 skipped, 103 deselected, 46 subtests passed in 268.91s`, 宿主报告退出码 1. **全量检查失败, 不记为通过.**

## 失败项

| 测试文件 | 目标版本失败项 | 日志观察 |
| --- | --- | --- |
| `general/present/tests/test_browser_session.py` | `TestCLI::test_exit_code_0_on_success`, `TestJSONOutput::test_state_browser_not_running_when_no_metadata`, `TestJSONOutput::test_status_alive_false_when_no_metadata`, `TestJSONOutput::test_success_has_required_fields`, `TestLifecycle::test_recovery_after_close` | 共 5 条, 期望的正常/未运行状态被 `access_web_unavailable` 或失败返回替代. |
| `tests/test_mailbox_admin.py` | `test_neighbor_persisted_across_restart`, `test_pending_budget_exhaustion_semantics` | 共 2 条, Serve 在 15 秒窗口未报告端口, `tests/conftest.py:111`. |

首次来信把两类都归为环境缺口, 后续补核已收窄: 浏览器相关失败由宿主报告为缺少 playwright Python 包; 信箱启动读取超时仅确认间歇发生, 根因未定位. 详情和证据边界见下方真正父提交补核, 不把它们都当成已查明的环境问题.

## 历史无效基线与限制

**本节 b748fd2 对照已确认无效, 只保留历史, 不用于本轮是否引入失败的结论.**

- 对照提交按宿主报告为 `main=b748fd2b70c85afeebec82c5b57562d37b621c59`, 同环境只跑上述两个文件. 宿主未提供完整的基线命令与时间; 原始日志显示 `7 failed, 70 passed in 48.00s`, 报告退出码 1.
- 两边的 5 条 present 失败同名, `test_pending_budget_exhaustion_semantics` 同名. 另一条不同: 目标是 `test_neighbor_persisted_across_restart`, 基线是 `test_neighbor_upsert_by_name`, 均在第二次创建 Serve 时端口报告超时.
- 所以只能观察到旧版本也出现同类失败, **不能声称 7 个具体失败全部一一证明为旧问题**, 更不能将目标日志记成全绿.
- 本容器当时没有 b748fd2 的 Git 对象, 未核实该提交与目标的祖先关系; 它也不是所提供的紧邻父提交 `6717c5e3f966821aa3fedcf0b8459e4fa2537b3a`.
- 本会话实查 `git diff --exit-code c77f6af^ c77f6af -- general/present/scripts general/present/tests general/mailbox/scripts tests pytest.ini`, 退出 0. 这些程序与测试路径在本轮没有改动, 这是代码范围事实, 不是实际测试通过证明.
- 已以请求信 `f65db281c2eb4687b2162276a6fa315c` 请宿主核实基线关系, 在真正父提交对照两个文件, 并只读查明缺依赖与 Serve 超时根因; 明确不改源码/测试/安装目录, 不切母体主仓 HEAD. 结果待实际回信.

## 真正父提交与间歇失败补核

来源: 宿主来信 `da2135e9c5e24ae79b6f5c6514eb1ffe`. 本会话已实际读取并原样保存新日志; 以下测试计数和失败清单直接来自日志, 提交关系及运行环境说明来自宿主.

- 宿主核实 b748fd2 与 c77f6af 互不为祖先, 共同祖先为 96b3b5f, 因此撤回首次基线推断. 真正父提交为 `6717c5e3f966821aa3fedcf0b8459e4fa2537b3a`.
- 父提交的两个文件对照: `HOST-PARENT.log` 显示 `6 failed, 71 passed in 33.38s`, 宿主报告退出 1. 失败为同名 5 条 browser_session 与 `test_pending_budget_exhaustion_semantics`. 这 6 项失败在真正父提交也实际出现过, 但仍不记成目标通过.
- 目标提交信箱测试文件三次复跑:
  - `HOST-ADMIN-RUN-1.log`: `1 failed, 14 passed`, 32.95s; 失败 `test_neighbor_persisted_across_restart`.
  - `HOST-ADMIN-RUN-2.log`: `2 failed, 13 passed`, 47.84s; 失败 `test_neighbor_upsert_takes_over_occupied_address` 与 `test_pending_budget_exhaustion_semantics`.
  - `HOST-ADMIN-RUN-3.log`: `1 failed, 14 passed`, 33.28s; 失败 `test_neighbors_get_delete_patch`.
- 三轮均有 `serve 未在超时内报告端口`, 失败用例随轮次变化. 因此只确认间歇失败, 不能把目标比父提交多出的那项判为已证明非本轮引入, 也不选取某个单项偶然通过来充抵整套失败.
- 宿主报告已实际定位浏览器依赖错误: `Cannot import browser_agent: No module named playwright`; Chromium 缓存存在, 缺的是 Python 包. 与仓库 `general/access-web/browse/pyproject.toml` 的声明依赖 `playwright>=1.40` 相符. 该导入探测命令的原始输出未单独附入日志, 本处明确按宿主实测来信记录, 不是本会话另行实跑.
- 宿主手动测 Serve 启动与连续三轮重启约 0.06-0.07s, 未定位测试中 15s 读取超时的原因; 未据此断言服务或测试中的哪一方有 bug. 原始计时记录未随信附入, 不作修复结论.
- 本轮补核按宿主声明均在 `/tmp` 独立 worktree 中完成, 未再次切主仓或动其未提交内容, 未运行同步. 宿主未补装 playwright, 尚未修改程序或测试.
- 下一步建议先在 `/tmp` 的独立验证环境补齐已声明的测试依赖, 不写真实已安装 skill 的环境, 再完整跑一次并保留所有结果; 若仍失败, 另行明确调查/修复工作边界. 用户未确认前不扩大本轮到信箱代码修复, 不自行改关闭标准.

## 安全与副作用声明

以下是宿主声明, 本会话未在宿主现场独立复核: 前后 podman 匿名卷清单同为 5 个, 未同步或改测试/pytest.ini; 补跑期间曾误将母体主仓 HEAD 短暂切到目标提交, 随后恢复 main 并保留原有 5 处未提交改动, 备份在宿主 `/home/bolo/.local/share/swt-rescue/`. 因此不照抄"完全没有动过母体"的宽泛说法, 后续已明确限定仅操作独立副本.

## 当时判定 (已被用户后续范围替代)

后续用户明确只在当前容器验证, Podman 相关代码未改就不用测, 信箱间歇故障不归本轮; 已修改 AC-07-06, 最终直接相关检查见 `CLOSURE.md` / `FINAL-CHECKS.log`. 下述旧范围下的阻塞判定不再作为本节点关闭条件, 本文件仅保留历史实跑事实.

AC-07-06 的全量测试要求尚未满足: 容器自身因缺 podman 未能启动用例, 宿主已运行但有 7 条失败. 文本核对, 格式检查与 navigate 30 条通过均不充抵该条件. milestone-07 保持进行中, 不据此关闭或宣称正式交付. 若需要调整关闭条件或另列修复工作, 须先由用户明确决定并更新权威标准, 不是由代理把既有失败自行豁免.
