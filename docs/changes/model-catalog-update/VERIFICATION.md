# 验证记录

日期: 2026-11-18. 环境: Linux 宿主机, `uv run python --version` = Python 3.14.7.
比较基线: `194c5754749a53b2e4cd040f2d2cda701ca9b191`.
目标: 基于该提交的未提交工作区, 本次源码/数据/测试逐文件 SHA256 见 [source-sha256.txt](source-sha256.txt). 本记录不代表用户验收或已同步发布.

要求与范围见 [REQUEST.md](REQUEST.md).

## 来源核对

使用 access-web 的只读 scrape 入口:

```text
cd /home/bolo/.agents/skills/access-web
uv run python scrape/scripts/scrape.py browse https://developers.openai.com/api/docs/models/gpt-6.2-astra.md --max-chars 16000
uv run python scrape/scripts/scrape.py browse https://developers.openai.com/api/docs/models/gpt-6.2-sol.md --max-chars 16000
uv run python scrape/scripts/scrape.py download https://raw.githubusercontent.com/openai/codex/main/codex-rs/models-manager/models.json /tmp/llm-model-update-codex.json
```

两份官方 Markdown 均返回 HTTP 200, `mode=extract`, `method=raw_text`, `confidence=high`, `warnings=[]`. 首次抓取 HTML 页面因导航噪声置信度低且截断, 未用作事实依据, 随后改读官方提供的 Markdown.

| 官方 Standard 短上下文价格, USD/1M tokens | input | output | cacheRead | cacheWrite (30 分钟) |
| --- | --- | --- | --- | --- |
| GPT-6.2 Astra | 8 | 40 | 0.4 | 10 |
| GPT-6.2 Sol | 2 | 10 | 0.1 | 2.5 |

两份模型卡均明确 `none` 推理请求会被拒绝, text/image 输入, 总窗口 1050000, 最大输入 922000, 最大输出 128000. 本次保留客户端目录 872000 的配置上限, 不宣称已实测该长度. 超 272K 输入价格变化等边界见模型目录 `sources`/`pricingNote`.

上游 Codex JSON HTTP 200, 667893 字节, SHA256 `d50b6749506d97e5f334dbabcb666eb1689f423cf3e88cfabdcf3c536b873068`. 核对新型号 low/medium/high/xhigh/max 及 max_context_window=872000. 上游另有 ultra 自动委派档与 >=0.166.0 的客户端要求, 本次未将其新工具模式/实验工具带入固定 0.162.1 的目录. 新增条目的基础指令是原有官方 GPT-6 首段, 非最新上游完整提示词. 兼容性实测缺口见下文.

## 实际入口与结果

所有下列仓库命令从本仓库根执行, 未运行全量 pytest, 未连接付费生成 API, 未创建容器或写真实 agent 目录.

1. `uv run python workflow/use-sandbox-worktree/scripts/agent-template.py validate cliproxyapi`
   - 预期: 模板可校验, 版本已更新.
   - 实际: `valid=true`, 模板与模型版本均为 `2026-11-18.1`, digest `dc23ccfa17431aa4dff71b848de5a265504007d2618b8eceaa439fe96ddb87a7`.
   - 真实渲染入口另由 DataTests 检查: Pi 6 个模型, Codex 4 个 Responses 模型, Kimi 6 个模型, 均含新型号; 默认模型未变.
2. 改前用旧脚本和设备数据执行 `uv run python general/llm-select/score.py --scores /home/bolo/.agents/llm-select/llm-scores.json --catalog /home/bolo/.agents/llm-select/model-catalog.json`, 改后执行 `uv run python general/llm-select/score.py`.
   - 预期/实际: 旧候选默认输出逐字节一致, 两份输出 SHA256 均为 `46907442eecd294efbc87eef9bfcd2f510ca38221948fa8c585bd45a6f18751b`.
   - 评分卡迁移前后逐字节一致, SHA256 均为 `7ddb16917ffaeb63bd7a7e2b67414b64986c1a42f292a67a7d0c058e19eebd0a`. 没有重评旧结论.
3. `uv run python general/llm-select/score.py --scope 'cli/glm-5.3-flash cli/gpt-6.2-astra cli/gpt-6.2-sol'`
   - 预期/实际: 两个新型号显示 `[未评分]`, 六项能力 N/A, thinking `low/medium/high/xhigh/max`. 价格分分别显示 Astra `0.00742`, Sol `0.0297`. 未用旧型号评分冒充新型号.
4. 默认数据路径和分发:
   - SmokeTests 在临时 cwd/HOME 下故意放无效旧数据, 从真实 CLI 仍成功读取随 skill 的数据.
   - ModelDataDistributionTests 调用真实 `execute_plan` 同步到临时 skill 目录, 再从其 `score.py` 启动 CLI, 正确输出基准和两个未评分新型号及价格分.
   - 没有执行面向真实 agent 目录的同步, 没有改动真实 skills. 沙箱真实挂载未运行; 旧数据挂载的既有隔离测试 16 个通过.
5. `git diff --check`: 通过.

原始模板校验/评分/版本/hash 输出见 [cli-results.txt](cli-results.txt).

## 自动化结果与复跑

```text
uv run python -m unittest discover -s tests -p test_llm_select.py -q
uv run python -m unittest discover -s tests -p test_pi_models_config.py -q
uv run python -m unittest discover -s tests -p test_agent_templates.py -q
uv run python -m unittest discover -s tests -p test_swt_llm_select_mount.py -q
uv run python -m unittest discover -s tests -p test_sync_to_pi.py -q
uv run python -m unittest discover -s tests -p test_agent_templates_safety.py -q
```

| 套件 | 结果 |
| --- | --- |
| test_llm_select.py | 35 通过 |
| test_pi_models_config.py | 3 通过 |
| test_agent_templates.py | 6 通过 |
| test_swt_llm_select_mount.py | 16 通过 |
| test_sync_to_pi.py | 29 通过 |
| test_agent_templates_safety.py | 37 个测试方法, 33 通过, 2 失败, 2 跳过; 失败记录共 3 条, 其中 2 条属于同一测试方法的子用例 |

前五套件共 89 个通过, 输出见 [test-results.txt](test-results.txt). 最后追加的一次 35 个测试是修正文档字符串后的单套件复跑, 不重复计数.

安全套件改前/改后同样失败:
- `LifecycleTests.test_verified_birth_reentry_uses_frozen_snapshot_not_latest_template`: configure_repo 门控断言.
- `ResumeTests.test_new_and_old_ready_resume_are_separate`: legacy=False/True 两个子用例预期 0 实际 1.

改前已实际运行并观察上述失败, 记录在 REQUEST.md. 改后原始输出见 [template-safety-results.txt](template-safety-results.txt). 未掩盖, 跳过或修复这些无关失败. 开发中发现的固定版本断言和告警文案断言不匹配已修正, 最终没有新增失败记录. 2 个未运行的真实客户端解析测试保持未验证.

## 测试代码抽查

比较范围为基线到本次工作区的全部差异, 包括测试/夹具/手动验证代码/运行配置. 新增或修改的功能测试完整清单如下, 没有新增持久层替身或独立手动验证程序, 没有删除测试.

| 路径与方法 | 用途/对应要求 | 真实依赖与替换点 | 结果 |
| --- | --- | --- | --- |
| `tests/test_llm_select.py`: `SmokeTests.test_default_data_works_outside_repo_without_device_tables` | 默认读取随 skill 数据, 不依赖 cwd 或旧设备目录, 新型号未评分 | 真实子进程 CLI/JSON/临时 HOME/cwd, 无 mock | 通过 |
| `tests/test_sync_to_pi.py`: `ModelDataDistributionTests.test_synced_llm_select_runs_with_its_own_data` | 数据随 skill 同步后可直接算分 | 真实 execute_plan/文件系统/子进程 CLI, 同步目标仅临时目录, 无 mock | 通过 |
| `tests/test_pi_models_config.py`: `PiModelsConfigTests.test_gpt_62_specs_match_sandbox_and_selection_catalog` | 三处目录的新型号规格/价格/推理档一致且符合来源 | 真实仓库 JSON, 预期是官方数据与明确配置上限的字面量, 无 mock | 通过 |
| `tests/test_agent_templates_safety.py`: `DataTests.test_deterministic_and_native_catalog_consumed` | 扩展现有 Pi/Codex/Kimi 模型集合断言 | 真实模板校验/快照/渲染与 JSON/TOML 解析, 复用已有临时文件/假 Key, 本方法不发网关请求 | 通过 |
| `tests/test_agent_templates_safety.py`: `DataTests.test_new_birth_same_name_gets_new_snapshot_not_old_one` | 原快照不随后续新版本改变 | 真实 creation/文件系统/read_snapshot, 使用独立字面版本 test-v1/next 替代依赖仓库历史版本号的断言 | 通过 |

作者已自检上述全部改动: 经真实入口, 预期来自独立字面量或官方资料, 新增测试未替换内部协作者, 文件使用真实临时存储. 各测试可用上方所属文件的 unittest 命令复跑. 该清单绑定 source-sha256.txt 中的工作区版本.

用户选样与明确接受: **待确认**. 本次未提交, 尚无目标提交号, 以文件 SHA256 固定待审内容; 不能称正式验收通过或自动关闭. 技能执行调用关系没有变化, README 仅更新数据维护位置说明.

## 未验证范围

- 未调用新型号的真实生成/工具流/长上下文请求, 未确认现场网关已开放新型号或按官方价格计费.
- 上游 GPT-6.2 对 Codex >=0.166.0 的要求与固定 0.162.1 的差异已显式记录, 未验证旧客户端端到端兼容.
- 未同步到真实 agent 目录, 未验证真实容器挂载/初始化, 未升级或构建镜像. 实施结果目前仅在仓库工作区.
- 历史评分/速度依据/价格目录中的旧条目原样保留, 没有重新调研或纠正弱依据.
