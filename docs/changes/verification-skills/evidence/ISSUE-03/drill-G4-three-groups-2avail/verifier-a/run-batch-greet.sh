#!/bin/bash
# AC-001-3: 对 data/greet/names.txt 每一行运行一次 python3 tool.py greet --name <姓名>
# 逐条真跑 (每条一个独立 python3 进程), 逐字节比对 stdout, 记录退出码.
set -u
REPO=/tmp/orchestra-03/heavy/three-groups-2avail
V=$REPO/docs/changes/tool-cli/evidence-c0505de-r1/verifier-a
NAMES=$REPO/data/greet/names.txt
DETAIL=$V/ac001-3.detail.tsv
SUMMARY=$V/ac001-3.summary.txt
TMP=$V/.tmp-greet
rm -rf "$TMP"; mkdir -p "$TMP"

START=$(date -Is)
START_S=$(date +%s.%N)
pass=0; fail=0; total=0

printf 'idx\tname\texpected\texpected_bytes\tactual_text\tactual_bytes\texit\tmatch_raw_with_nl\tmatch_raw_without_nl\n' > "$DETAIL"

while IFS= read -r name || [ -n "$name" ]; do
  total=$((total+1))
  expected="Hello, ${name}!"
  printf '%s\n' "$expected" > "$TMP/exp_nl"
  printf '%s' "$expected" > "$TMP/exp_nonl"

  python3 tool.py greet --name "$name" > "$TMP/out" 2> "$TMP/err"
  rc=$?

  exp_bytes=$(wc -c < "$TMP/exp_nl")
  act_bytes=$(wc -c < "$TMP/out")
  actual_text=$(cat "$TMP/out")

  m_nl=NO; m_nonl=NO
  cmp -s "$TMP/out" "$TMP/exp_nl" && m_nl=YES
  cmp -s "$TMP/out" "$TMP/exp_nonl" && m_nonl=YES

  if [ "$rc" -eq 0 ] && [ "$m_nl" = YES ]; then
    pass=$((pass+1)); verdict=PASS
  else
    fail=$((fail+1)); verdict=FAIL
    {
      echo "### FAIL idx=$total"
      echo "name=<$name>"
      echo "expected=<${expected}> (bytes=$exp_bytes)"
      echo "actual stdout od:"
      od -c "$TMP/out"
      echo "actual bytes=$act_bytes"
      echo "exit=$rc"
      echo "stderr:"; cat "$TMP/err"
      echo
    } >> "$V/ac001-3.failures.txt"
  fi

  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$total" "$name" "$expected" "$exp_bytes" "$actual_text" "$act_bytes" "$rc" "$m_nl" "$m_nonl" "$verdict" >> "$DETAIL"
done < "$NAMES"

END_S=$(date +%s.%N)
END=$(date -Is)
{
  echo "场景: AC-001-3 批量问候 250 个姓名"
  echo "命令: 对 data/greet/names.txt 每行执行 python3 tool.py greet --name <该行姓名>"
  echo "数据文件: data/greet/names.txt (wc -l=$(wc -l < "$NAMES"))"
  echo "开始: $START"
  echo "结束: $END"
  echo "耗时秒: $(awk -v a="$START_S" -v b="$END_S" 'BEGIN{printf "%.3f", b-a}')"
  echo "总条数: $total"
  echo "通过: $pass"
  echo "失败: $fail"
  echo "明细: $DETAIL"
} > "$SUMMARY"
cat "$SUMMARY"
