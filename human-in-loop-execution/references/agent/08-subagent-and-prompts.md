# Subagent 与 Prompt 约束

```yaml
subagent_allowed_when:
  - platform_supports_subagents
  - units_have_disjoint_allowed_files
  - dependencies_are_explicit
  - shared_state_conflicts_absent_or_serialized
  - each_subagent_has_context_packet
subagent_forbidden_when:
  - user_requested_single_session
  - units_share_same_file_without_serialization
  - handoff_scope_unclear
  - verification_requires_global_state_not_available_to_subagent
prompt_must_include:
  - unit_id
  - source_hilp_refs
  - objective
  - allowed_files
  - prohibited_files
  - must_read_context
  - stop_conditions
  - expected_output
prompt_must_not_include:
  - full_unrelated_hilp_assets
  - permission_to_expand_scope
  - vague_instruction_to_fix_anything
```

Use only prompt content generated from the current v2.24 contract.
