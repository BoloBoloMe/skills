# 移除验证配方生成与维护 skills

## 范围

我先要求删除 `create-verification-skill`, 随后确认 `maintain-verification-skill` 也一起删除. 基线为 `829a1ad`.
删除两项 skill 的目录, 含正文, codex 元数据与漂移分类参考; README 技能表同步移除两行. 两者规则不迁移, 其余 skill 保持原样. 旧需求, 评审与实跑记录保留为历史, 不作为现行调用入口. 另用 [ADR 0027](../../adr/0027-remove-project-verification-skill-tools.md) 记录两项工作流退役, 仅取代 ADR 0021 对两项职责的分配, 不改旧 ADR 原文.

## 实际检查

- README 技能表与顶层 skills 双向对照: 38 项一致. 不把依赖环境 `.venv` 中自带的示例当成本仓库 skill.
- 现行仓库源码/入口/测试无两项旧名引用; 两个目录均已不存在. 历史 docs 不参与旧名清零检查.
- 调用真实 `sync-to-pi.py` 的 `_query_top_dir` 构建 workflow 同步计划, 只预设交互选择, 不执行计划: 返回 24 项, 不含被删两项, 仍含 verification-contract 与 verify-change.
- `uv run python -m unittest discover -s tests -p test_sync_to_pi.py -v`: 28 项通过.
- `uv run python -m unittest discover -s tests -p test_skills_codex_metadata.py -v`: 1 项通过.
- `git diff HEAD --check` 通过. 检查辅助命令先修正了正则写法和依赖目录误计问题, 以下是修正后完整输出, 不把检查器报错当作产品结果.

```text
README 与实际顶层 skills 双向一致: 38 项
现行入口/源码/测试无两项旧名引用; 排除历史 docs 和依赖目录
真实同步计划构建函数返回 24 个 workflow 项, 已排除两项, 未执行同步
test_copy_failure_keeps_old_destination (test_sync_to_pi.AtomicDirSyncTests.test_copy_failure_keeps_old_destination) ... ok
test_file_copy_failure_keeps_old_file (test_sync_to_pi.AtomicDirSyncTests.test_file_copy_failure_keeps_old_file) ... ok
test_half_copied_directory_is_rejected (test_sync_to_pi.AtomicDirSyncTests.test_half_copied_directory_is_rejected)
拷贝中途停下没抛异常 (半成品) 也能被完整性校验拦住. ... ok
test_normal_path_replaces_whole_directory (test_sync_to_pi.AtomicDirSyncTests.test_normal_path_replaces_whole_directory) ... ok
test_symlinked_destination_is_refused (test_sync_to_pi.AtomicDirSyncTests.test_symlinked_destination_is_refused) ... ok
test_clear_failure_stops_sync (test_sync_to_pi.ClearSkillsTests.test_clear_failure_stops_sync) ... ok
test_clear_only_runs_after_final_confirmation (test_sync_to_pi.ClearSkillsTests.test_clear_only_runs_after_final_confirmation) ... ok
test_clear_removes_all_children_and_preserves_root (test_sync_to_pi.ClearSkillsTests.test_clear_removes_all_children_and_preserves_root) ... ok
test_execute_clears_before_syncing (test_sync_to_pi.ClearSkillsTests.test_execute_clears_before_syncing) ... ok
test_final_rejection_keeps_old_skills (test_sync_to_pi.ClearSkillsTests.test_final_rejection_keeps_old_skills) ... ok
test_drop_empty_sources_removes_item_from_plan (test_sync_to_pi.EmptySourceDirTests.test_drop_empty_sources_removes_item_from_plan) ... ok
test_execute_skips_empty_source_and_keeps_destination (test_sync_to_pi.EmptySourceDirTests.test_execute_skips_empty_source_and_keeps_destination) ... ok
test_complete_skill_is_registered (test_sync_to_pi.ExtensionIntegrityGateTests.test_complete_skill_is_registered) ... ok
test_hidden_staging_dir_is_not_registered (test_sync_to_pi.ExtensionIntegrityGateTests.test_hidden_staging_dir_is_not_registered)
中断残留的隐藏暂存目录即使含 pi-extension 也不当作 skill. ... ok
test_missing_index_ts_blocks_and_keeps_state (test_sync_to_pi.ExtensionIntegrityGateTests.test_missing_index_ts_blocks_and_keeps_state) ... ok
test_missing_skill_md_blocks_and_keeps_state (test_sync_to_pi.ExtensionIntegrityGateTests.test_missing_skill_md_blocks_and_keeps_state) ... ok
test_partial_deployment_does_not_register_any_path (test_sync_to_pi.ExtensionIntegrityGateTests.test_partial_deployment_does_not_register_any_path)
半成品存在时连正常 skill 也暂不登记, 整体状态不变. ... ok
test_skill_without_pi_extension_is_not_a_candidate (test_sync_to_pi.ExtensionIntegrityGateTests.test_skill_without_pi_extension_is_not_a_candidate)
无 pi-extension 的普通 skill 不成为候选, 若曾被登记则视为残缺报错. ... ok
test_unreadable_index_ts_blocks (test_sync_to_pi.ExtensionIntegrityGateTests.test_unreadable_index_ts_blocks) ... ok
test_extension_registration_reconcile (test_sync_to_pi.ExtensionRegistrationReconcileTests.test_extension_registration_reconcile) ... ok
test_removed_skill_is_still_reclaimed (test_sync_to_pi.ManagedExtensionMissingTests.test_removed_skill_is_still_reclaimed) ... ok
test_skill_dir_without_extension_keeps_registration (test_sync_to_pi.ManagedExtensionMissingTests.test_skill_dir_without_extension_keeps_registration) ... ok
test_merge_preserves_environment_reference_without_expanding_or_saving_key (test_sync_to_pi.ModelEnvironmentTests.test_merge_preserves_environment_reference_without_expanding_or_saving_key) ... ok
test_distinct_destinations_pass (test_sync_to_pi.PlanConflictTests.test_distinct_destinations_pass) ... ok
test_incident_shape_aborts_before_empty_source_filter (test_sync_to_pi.PlanConflictTests.test_incident_shape_aborts_before_empty_source_filter)
迁移遗留的空壳目录与真目录同落一个 dst 也先报冲突, 不靠兜底掩盖. ... ok
test_same_destination_from_two_sources_is_rejected (test_sync_to_pi.PlanConflictTests.test_same_destination_from_two_sources_is_rejected) ... ok
test_textually_different_paths_to_same_target_conflict (test_sync_to_pi.PlanConflictTests.test_textually_different_paths_to_same_target_conflict) ... ok
test_sync_no_old_extensions (test_sync_to_pi.RetireOldExtensionsTests.test_sync_no_old_extensions) ... ok

----------------------------------------------------------------------
Ran 28 tests in 0.018s

OK
test_all_skill_md_files_have_codex_metadata_contract (test_skills_codex_metadata.SkillsCodexMetadataTests.test_all_skill_md_files_have_codex_metadata_contract) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.004s

OK
```

## 非作者复核

新建 Herdr agent `remove-verification-tools`, tab `w1:t2T`, pi 会话 `01a1a5ea-dc00-744d-bb9f-0339cbd5bb74`, 未继承实现会话, 仓库只读. 模型为 `cli/deepseek-flash`, thinking `high`, kind `pi`, 按 review 画像选择, 本任务不依赖外部专业知识; 稳定性评分依据偏弱, 结果仍由本会话核对.
实际派工输入:

```text
任务标识=remove-verification-tools; 回信地址=01a1a596-e731-7649-8ece-1288678991f3. 你是新开的非作者复核者. 先调用 mailbox skill, 确认独立信箱和取信守护, 按投信规则通知接手及你的地址, 完成时通知结果和证据路径. 信箱不可用则在会话说明, 不强投或等待回信.
只读仓库 /home/bolo/Workspace/refactor-skill-around-verification, 不提交/同步/修改仓库或真实 agent 配置, 不开子会话. 允许仅写 /tmp/remove-verification-tools-review.md 保存你的完整结论.
用户先要求从工作流 skills 删除 create-verification-skill, 随后明确 maintain-verification-skill 也一起删. 不要求迁移两者规则, 不删除历史 docs 记录, 不同步安装版.
读取相对 829a1ad 的完整差异(含暂存和未暂存), README 目录约定及必要当前文件, 独立核对删除范围, 是否还留现行入口/引用/执行调用, 同步计划是否还能发现两项, 是否损伤其他 skills. 按 README 的调用关系口径人工核对技能表与实际执行调用语句; 普通引用不算调用边. 现行源码只看仓库管理的文件, 不把 .venv 内依赖自带示例 skills 当成仓库技能; 历史 docs 中的旧名不是本次应清除的现行引用. 不运行真实部署同步或外部资源测试.
给出完整发现, 文件/位置/依据, 区分已证实问题和待核实疑点. 无问题也写实际核对范围, 调用关系变化及未覆盖范围. 你的复核不替用户作最终人工接受.
请在普通最终输出给完整报告, 同时把同一正文保存到 /tmp/remove-verification-tools-review.md 作为归档证据, 不只回复路径.
```

初稿出现差异计数和调用边误判, 本会话要求按原始语句重核, 没有照单采信. 实际复核反馈:

```text
remove-verification-tools 复核反馈. 完整初稿已读走并保留在 /tmp/remove-verification-tools-review-01.md. 本会话守护报告 running, 但服务把收件方判离线, 本轮改走 Herdr 交互, 不强投或重试通知.
请重核几项事实, 更新 /tmp/remove-verification-tools-review.md 的完整结论, 普通常规输出给完整更正版:
1. 你列出的差异是 1 个 README 修改与 5 个删除, 但摘要写 6 个文件被删, 正文写 7 项. 请用实际 diff 重新核对数字.
2. README 的边口径只算执行调用. 重读基线中 create 的新会话复跑段是否含 use-herdr 执行调用; maintain 写按 create 的某节执行是否只是普通引用. 独立按正文判断, 列准确的删除前出边, 不把正则命中直接当边.
3. 你认为没有本仓库的生成 skill 就意味着新项目配方永远为空. 请核实这个结论能否排除用户手工编写或项目自带配方, 区分已证实事实与推断. 删除这两项不要求删掉 verify-change 对既有配方的可选支持.
4. 你写 pytest 因缺 podman 在 conftest 阶段 INTERNALERROR. 如确实执行过, 请附实际命令与原始退出/错误片段; 如未执行, 改为未验证, 不把环境猜测写成实测.
不要再运行整套 pytest 或任何部署/外部资源检查; 仍只读仓库. 允许更新原报告文件, 不修改仓库. 其余发现也请保留有依据的结论. 此反馈不是要求你接受作者的无问题结论, 只纠正计数/边口径和实测口径.
```

更正版完整输出见 [REVIEW.md](REVIEW.md). 本会话核对并采用的结果:

- 源码差异是 README 修改 1 项, 文件删除 5 项, 共 6 项; 最终另加 ADR, 本记录与复核原稿归档, 不混为源码删除数.
- 删除前的仓库内执行调用边为 create -> verification-contract, create -> use-herdr, maintain -> verification-contract. maintain 对 create 的章节指针是引用, 不另算执行调用. 删除后没有其余 skill 指向两项旧名.
- 38 项现存 skill 与 README 技能表一致, 其余 skill 文件未变. 构建同步计划已排除两项, 但真实安装目录旧副本仍存在, 本轮未清理或同步安装版.
- 关于新项目配方分支永远为空的推断已撤回. 项目可以自带或自行编写配方, verify-change 的可选支持原样保留, 不新增无关改动.
- 复核者实际尝试过单文件 pytest, 被 conftest 调用缺失的 podman 阻断, 退出码 3, 没有用例执行; 其原始片段保留在报告中. 同一元数据用例的 unittest 直跑通过, 本会话另有上文 28+1 项通过记录, 不把环境受阻算通过.
- ADR 0027 由本会话在源码复核后补充并核对, 用于承接退役决策; 非作者报告关于尚无取代记录的观察只适用于它检查时的现场. 其余建议不构成本次未决事项: 可选配方支持保持不动, 实际安装清理由部署方单独处理.

首次接手通知已到达; 完成信因服务判断收件方离线被拒, 本会话守护当时仍称 running. 后续按反馈转用 Herdr 取回完整报告, 未强投, 未把投信状态当作业务结果. 结果已归档, 所建 tab 已关闭.

## 未覆盖与适用性

没有运行真实部署同步或删除安装版 skills, 没有运行完整产品开发/验收流程. 同步测试在隔离临时目录操作, 不等于真实 agent 环境已同步.
本轮没有测试代码, 手动验证程序或测试运行配置的变更, 测试代码验收记为 "无相关变更", 比较范围为本次基线到目标提交; 不虚构人工选样或接受记录.
