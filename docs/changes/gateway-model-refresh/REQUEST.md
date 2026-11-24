# 网关模型列表对齐 (2026-11-24)

## 已确认要求

用户要求:
1. 同步本仓库三处模型数据与 CLIProxyAPI 网关现状 (GET /v1/models 实测 20 条).
2. 更新 `general/llm-select/` 的模型目录与评分卡.
3. 更新 `workflow/use-sandbox-worktree/` 的 cliproxyapi 模板模型清单.
4. 会话中确认口径: OpenAI 模型只用 luna/sol/astra 三系且各自最新代; `gpt-6.1-terra`/`gpt-6-chat-thinking` 与旧代 GPT 不使用.

## 实施范围

- 新增 `glm-5.4` (1M 窗口/128K 输出/图像输入, thinking low/high/max), 移除网关已下线的 `glm-5.3`/`glm-5.3-flashx` 与口径外旧代 GPT (`gpt-6-astra`/`gpt-6.1-sol`/`gpt-6-sol`/`gpt-5.6-*`).
- `glm-5.3-flash` 价格 0.075/0.25 -> 0.15/0.50 (z.ai 现价), thinking 档 [high,xhigh,max] -> [low,high,max] (网关声明); `deepseek-flash` 0.14/0.28 -> 0.30/1.20 (DeepSeek 官方 peak 价, off-peak 半价).
- 评分卡全表按 Artificial Analysis Intelligence Index v5.0.1 重锚 (基准不变): gpt-6.2-astra/sol 首次评分, gpt-6.1-sol 条目随口径移除; glm-5.4 无公开基准数据, 保持未评分.
- 沙箱模板校验放宽: cost 可选 (价格未公布的模型可省略, 出现时必须完整且非负有限); 模板版本 2026-11-18.1 -> 2026-11-24.1.

## 验证方式

- `score.py` 默认与 `--scope` 运行, 检查未评分/价格 N/A 行为.
- 相关 unittest 全量: llm-select/pi-models/sync/agent_templates*.
- 数据一致性: `pi/models.json`, 沙箱模板 `models.json`, `model-catalog.json` 三处型号集合一致.

## 改前基线

提交 `5bdaa8e`, 远端已拉取, 工作区除用户未跟踪的 pi-session html 外干净.
