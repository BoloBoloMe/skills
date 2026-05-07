# HILE v2.24 一页速查

- HILE 只消费已批准、已关闭的 HILP handoff，不补规划、不扩大范围。
- 没有 approved HILP handoff 的 controlled execution 请求必须回到 HILP，不进入 partial HILE intake。
- 执行前检查 planned files；执行后检查 actual changed files。
- allowlist 外默认 out-of-scope；`prohibited_files` 可为空但字段必须存在。
- `source_handoff_ref` 必须指向 `phase-05/execution-handoff@vN`，并能在 HILP manifest 中找到。
- completion 需要新鲜验证证据和 completion review。
- 发现范围、验证或事实漂移时，停止并回到 HILP。
