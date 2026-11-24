# 验证记录 (2026-11-24)

## 测试

- `uv run --no-project python -m unittest tests.test_llm_select tests.test_pi_models_config tests.test_sync_to_pi`: 67 通过.
- `uv run --no-project python -m unittest tests.test_swt_llm_select_mount tests.test_env_docs tests.test_swt_stage_env tests.test_sync_to_pi`: 63 通过.
- `uv run --no-project python -m unittest discover -s tests -p 'test_agent_templates*.py'`: 50 个, 3 失败, 3 跳过. 失败为 `LifecycleTests.test_verified_birth_reentry_uses_frozen_snapshot_not_latest_template` 与 `ResumeTests.test_new_and_old_ready_resume_are_separate` (legacy=False/True), 与 2026-11-18 变更的改前基线完全一致, 属既有生命周期行为, 本次未引入新失败. 新增 `DataTests.test_cost_optional_but_complete_when_present` 通过.
- 真实模板校验: `uv run python scripts/agent-template.py validate cliproxyapi` -> `valid: true`, models-version `2026-11-24.1`.

## 选型表

`score.py --scope 'cli/glm-5.3-flash cli/gpt-6.2-sol cli/gpt-6.2-astra cli/gpt-6-luna cli/deepseek-flash cli/glm-5.4'` 输出符合预期:

- glm-5.4 `[未评分]`, 价格 N/A, thinking low/high/max.
- gpt-6.2-astra/sol 按 AA v5.0.1 评分入表; deepseek-flash knowledge N/A; 价格分与手算一致 (astra 0.0148 / sol 0.0594 / deepseek 0.452 / luna 1.19).

## 数据口径与边界

- 网关清单来自 GET /v1/models (20 条, 客户端 Key, 2026-11-24); 三处数据只保留文本/推理模型, 图像模型与 codex-auto-review 不列入.
- AA 数据为 Intelligence Index v5.0.1, Max 档, 2026-11-24 抓取; glm-5.4 未被 AA 收录, 无第三方基准, 不伪造评分.
- glm-5.4 单价未公布: z.ai Model API 未上线 (安全评估中), bigmodel 定价页未列; 目录不填 cost, score.py 价格维 N/A.
- 未验证: glm-5.4/gpt-6.2 真实网关生成调用, 沙箱三客户端端到端兼容, 长上下文/大输出实测.
