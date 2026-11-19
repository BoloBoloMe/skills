# 模型目录更新与评分数据入库

## 已确认要求

用户要求:
1. 在 `pi/models.json` 和 `workflow/use-sandbox-worktree/` 模型列表中加入 `gpt-6.2-astra` / `gpt-6.2-sol`.
2. `general/llm-select/` 的模型评分卡和价格表在本仓库维护.

## 实施范围

- 新增模型, 保留原有型号与默认模型. Pi/Codex/Kimi 的沙箱生成配置包含新型号.
- 本机旧评分和价格目录复制进 `general/llm-select/`, 评分数据原样保留. 新型号只入价格目录, 不伪造能力评分.
- `score.py` 默认从脚本同目录读取数据, 保留显式路径参数. 数据随 skill 同步与只读挂载进入沙箱. 不修改真实 agent skills 或同步到真实 agent 目录.
- 价格采用官方 Standard 短上下文单价. 上下文沿用当前网关目录的 872000 配置上限, 最大输出 128000. 不声明已验证真实网关请求/长上下文.
- 不升级固定 Codex 客户端. 新型号复用现有 GPT-6 基础指令首段并适配 0.162.1 字段, 仅加入必要模型元数据, 保持禁用 WebSocket/Responses Lite/自动升级/实验工具.

## 验证方式

- 配置检查: 加载版本化模板, 从真实渲染入口检查 Pi/Codex/Kimi 新型号和默认值.
- 评分入口: 从其他工作目录运行默认命令; 新旧数据对同一组旧候选的输出一致; 新型号显式候选显示未评分及正确价格/档位.
- 隔离同步: 使用现有同步函数复制 skill 到临时目录, 从复制后的 CLI 验证默认数据可读, 不写真实 agent 目录.
- 运行相关现有 unittest. 更新已存在的固定模型集合断言, 补充默认数据 CLI 回归检查.
- 留下命令/输出/边界与测试变更清单, 正式验收由用户决定.

## 改前基线

提交: `194c5754749a53b2e4cd040f2d2cda701ca9b191`, 初始工作区干净.

- `test_llm_select.py`: 34 通过.
- `test_agent_templates.py`: 6 通过.
- `test_pi_models_config.py`: 2 通过.
- `test_agent_templates_safety.py`: 37 个, 3 个失败, 2 个跳过. 失败为 `LifecycleTests.test_verified_birth_reentry_uses_frozen_snapshot_not_latest_template` 的 configure_repo 门控断言, 以及 `ResumeTests.test_new_and_old_ready_resume_are_separate` 的 legacy=False/True 两个子用例. 均在本次修改前出现, 本次不修复这些无关生命周期行为.
