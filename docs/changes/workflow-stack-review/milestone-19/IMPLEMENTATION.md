# milestone-19 IMPLEMENTATION: 给 skill 补 codex 的 agents/openai.yaml 元数据

状态: 已实现, 待独立核验 (验收归 milestone-08).

## 做了什么

1. 为 frontmatter 带 `disable-model-invocation: true` 的 *用户调用* skill 新建
   `agents/openai.yaml`, 内容仅两行:

   ```yaml
   policy:
     allow_implicit_invocation: false
   ```

   布尔值不加引号, 键不加引号, 不写 interface/icon/brand_color/dependencies.
2. *模型调用* skill 不建文件, 走 codex 默认的允许隐式调用.
3. 新增守卫测试 `tests/test_skills_codex_metadata.py`: 遍历 `workflow/` 与
   `general/` 下全部 `SKILL.md`, 按行用标准库解析 (不引 pyyaml):
   - 带 `disable-model-invocation: true` 的必须有 `agents/openai.yaml`,
     且 `policy.allow_implicit_invocation` 为不带引号的 `false`,
     文件内容与最小配置逐字一致;
   - 反之若建了该文件, `allow_implicit_invocation` 不得为 `false`.
4. `general/writing-for-llm/SKILL-MECHANICS.md` 新增 "codex 元数据" 一节:
   维护 `agents/openai.yaml` 是维护 skill 的必选项, *用户调用* skill 建文件并
   设 `false`, *模型调用* skill 不建文件, 漏维护由守卫测试抓住.
5. 未改任何 `SKILL.md` frontmatter, 未动 `sync-to-pi.py`, 未运行同步,
   未改 `~/.agents/skills` 下真实安装的 skills.

## 实际处理文件清单与计数

现场核实: `workflow/` + `general/` 共 39 个 `SKILL.md`. 注意: 路线图
milestone-19 文本写 "43 个用户调用 + 9 个模型可见 = 52", 与现场不符;
本实现按 frontmatter 条件判断, 不依赖计数, 以现场 39 个为准. 计数差异
已在收尾信中上报, 待 milestone-08/路线图维护方核对.

新建 33 个 `agents/openai.yaml` (全部 *用户调用*):

- general/ (10): handoff, llm-select, opposing-viewpoint, present,
  receive-handoff, retro, teach, translate-a-skill, writing-for-llm, wtf
- workflow/ (23): benchmark-checklist, blast-radius, code-review,
  codebase-design, create-verification-skill, decision-ledger, deliberate,
  demo, domain-awareness, domain-modeling, drive-execution, explain-diff,
  fix-bugs, follow-the-money, improve-codebase-architecture, lazy-dev,
  maintain-verification-skill, navigate, to-execution, to-spec,
  use-sandbox-worktree, use-worktree, verify-change

未建文件的 6 个 *模型调用* skill: general/access-web, general/grilling,
general/mailbox, general/use-herdr, workflow/software-engineering-consensus,
workflow/verification-contract.

其他改动文件:

- tests/test_skills_codex_metadata.py (新增)
- general/writing-for-llm/SKILL-MECHANICS.md (新增一节)
- docs/changes/workflow-stack-review/milestone-19/IMPLEMENTATION.md (本文件)

## 抽查证据

- *用户调用* (模型不可见) `workflow/drive-execution`:
  - frontmatter 含 `disable-model-invocation: true` (SKILL.md 第 4 行);
  - `workflow/drive-execution/agents/openai.yaml` 内容为
    `policy:\n  allow_implicit_invocation: false\n` (cat 实读确认).
- *模型调用* (模型可见) `workflow/verification-contract`:
  - frontmatter 无 `disable-model-invocation`;
  - `workflow/verification-contract/agents/` 目录不存在 (find 无结果).

## 已实测通过

- `uv run python -m pytest tests/test_skills_codex_metadata.py` — 1 passed.
- 守卫红测: 临时删除 `workflow/fix-bugs/agents/openai.yaml` 并把
  `general/retro/agents/openai.yaml` 的值改成带引号 `"false"` 后, 测试失败并
  指出缺文件; 还原后恢复 1 passed (两种漏配都能抓住).
- 相关子集 `uv run python -m pytest tests/test_skills_codex_metadata.py
  general/present/tests/test_skill_contract.py
  general/writing-for-llm/tests/test_check_skill.py
  tests/test_old_mechanism_retired.py tests/test_sync_to_pi.py
  tests/test_sync_to_pi_compose.py` — 48 passed.
- 测试环境说明: 容器无 podman, `tests/conftest.py` 的 sessionstart/finish
  钩子无条件调 `podman volume ls` 会 INTERNALERROR; 用 PATH 上的空实现
  stub (`/tmp/m19-stub/podman`) 绕过, 只影响钩子, 不影响断言. 同时按纪律设
  `NAVIGATE_WEB_RUNTIME_DIR=/tmp/navigate-milestone-19`, 只跑相关子集,
  不跑抢默认端口的 navigate 全量测试.

## 未验证

- 未在真实 codex-cli 0.162.1 中加载本仓库 skill 验证 "skill 不注入模型
  上下文, 只能 dollar-skill-name 显式调用" 的端到端行为; 该结论引自
  路线图记录的 codex-cli 自带 skill-creator 文档, 本里程碑只保证元数据
  文件本身正确.

## 证据缺口

- 路线图 43/9 计数与现场 39 个 SKILL.md (33 用户调用 + 6 模型调用) 的差异
  未找到出处, 待路线图维护方核对.
- 容器缺 podman 的根因未查 (镜像播种范围问题), 已用 stub 绕过, 缺包清单
  可交宿主重建镜像时补.
