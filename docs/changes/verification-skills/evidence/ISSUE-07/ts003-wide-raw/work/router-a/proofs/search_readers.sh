#!/usr/bin/env bash
# 仅搜索指定的两个仓库, 包含隐藏/被忽略的源文件, 明列排除目录.
set -uo pipefail
roots=(/tmp/orchestra-07/drill-ts003-wide /tmp/orchestra-07/orders-consumer)
filters=(--hidden --no-ignore -g '!**/.git/**' -g '!**/.agents/**' -g '!**/.venv/**' -g '!**/node_modules/**' -g '!**/__pycache__/**' -g '!**/var/**')
run() {
  printf '$'; printf ' %q' "$@"; printf '\n'
  "$@"
  local rc=$?
  printf 'exit_code=%s\n\n' "$rc"
  if (( rc > 1 )); then exit "$rc"; fi
  return 0
}
for root in "${roots[@]}"; do
  printf '\n=== repository=%s ===\n' "$root"
  cd "$root" || exit 2
  run rg --files "${filters[@]}" .
  run rg -n "${filters[@]}" -e '\bamount\b' .
  run rg -n "${filters[@]}" -e 'read_orders|resolve_amount|parse_amount|register_legacy_formatter|amount_str' .
  run rg -n "${filters[@]}" -e 'orders[.]export[.]json|dump_orders|JSON[.]parse|json[.]loads|readFileSync|\brows\b|stdout|jq|stdin|process[.]argv|ARCHIVE|orders_archive' .
  run rg -n "${filters[@]}" -e 'schema|orders-export|amount_value' .
done
printf '\n=== exact bounded absence assertions: consumer schema/new fields ===\n'
cd /tmp/orchestra-07/orders-consumer || exit 2
printf '$'; printf ' %q' rg -n "${filters[@]}" -e 'schema|orders-export|amount_value' .; printf '\n'
rg -n "${filters[@]}" -e 'schema|orders-export|amount_value' .
rc=$?
printf 'exit_code=%s\n' "$rc"
[[ "$rc" == 1 ]] || { printf 'FAIL: expected no consumer schema/new-field dispatch\n'; exit 1; }
printf 'PASS: bounded search had no schema/new-field hits; this says nothing about production or other repositories.\n'
