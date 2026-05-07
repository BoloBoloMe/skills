# Tiny HILE flow example

Tiny flow still requires a valid HILP handoff. It does not mean ordinary unapproved coding.

```yaml
intake:
  source_handoff_ref: phase-05/execution-handoff@v1
  status: pass
tier:
  selected: tiny
  confirmation_required: false
  confirmation_required_when_triggered: []
inline_plan:
  steps:
    - update one allowed file
    - run targeted test
verification:
  commands:
    - pytest tests/test_example.py
```

If `handoff_says_wait_for_confirmation`, `user_requested_review_before_execution`, production behavior risk, or uncertainty is present, save a plan and wait for `确认执行：确认执行 Plan <path>`.
