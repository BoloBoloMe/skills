# milestone-07 作者检查记录

目标源文件提交: `c77f6af446d294c3d498c570feb88bd41fe79bb6`, 父提交 `6717c5e3f966821aa3fedcf0b8459e4fa2537b3a`. 日期为容器 UTC 2026-10-31, 命令时间见 `CHECKS.log` 与 `PYTEST.log`. 本文件只记作者实际检查, 不能代替独立复核或人工验收.

| 检查 | 命令与入口 | 实际结果 | 原始材料 |
| --- | --- | --- | --- |
| 七个改动技能的格式 | `uv run python general/writing-for-llm/check_skill.py <SKILL.md>`; 目标为 benchmark-checklist, code-review, drive-execution, navigate, software-engineering-consensus, to-execution, verification-contract | 全部 OK, 退出 0 | `CHECKS.log` |
| 测试写法文件迁移保真 | `git rev-parse c77f6af^:workflow/tdd/tests.md` 对照 `git hash-object workflow/verification-contract/reference/tests.md` | blob 相同, 原样迁移, 无需链接修正 | `CHECKS.log` |
| 差异空白检查 | `git diff --check c77f6af^ c77f6af` | 退出 0, 无输出 | `CHECKS.log` |
| navigate 现有测试 | `uv run python -m pytest workflow/navigate/tests` | 收集并通过 30 条, 退出 0, 8.08s | `NAVIGATE-TESTS.log` |
| 全部非 e2e 测试 | `uv run python -m pytest -m "not e2e"` | 会话启动时缺少 podman, 退出 3; 尚未运行用例, 未验证 | `PYTEST.log` |
| 实施前同命令预跑 | `uv run python -m pytest -m "not e2e"` | 同样在 `tests/conftest.py:236` 缺 podman, 退出 3; 不把它编造成测试红态或变更后回归 | `PYTEST-BEFORE.log` |

全量阻塞已通过出生宿主具体会话请求补跑, 原请求 `84feeb9f210a42209453c40fcf5c5a6f`, 目标版本补充信 `7bc09afa354941bb9358b753e856efae`. 宿主已在目标提交的独立副本实际运行: 778 passed, 7 failed, 4 skipped, 103 deselected, 46 subtests passed, 退出 1. 原始日志与基线限制见 `HOST-TESTS.md`, `HOST-PYTEST.log` 和 `HOST-BASELINE.log`; 不把旧版本同类失败当成目标通过, 已请求进一步核实. 容器自身缺 podman 的记录仍成立. 不伪造依赖, 不修改 pytest.ini/testpaths 或测试来绕过启动错误.

本轮未改 roadmap.py 或网页程序, navigate 测试是额外的实际回归记录, 不能用其 30 条通过充抵 AC-07-06 所要求的全量非 e2e 结果. 独立文本复核及补核已有 `REVIEW.md` / `REVIEW-CHECKS.log` (0dc2855, f26f36b, e83cac0), 源文件未发现实现问题. 指代解释与作者工具记录核查已补正; 协调方另以明确编辑标记校正请求方称谓, 不将代理的复核判断冒写为新的用户确认. 全量测试失败仍未闭环. 安装效果和实际 LLM 遵从率均未验证, milestone-07 保持进行中, milestone-08 未开始.
