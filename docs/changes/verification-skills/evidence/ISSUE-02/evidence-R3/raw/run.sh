#!/usr/bin/env bash
# 本轮验收实际执行脚本. 每个场景记录命令, stdout, stderr, 退出码.
set -u
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)" || exit 99
ROOT=$PWD
EVID=$ROOT/docs/changes/tool-cli/verify-r1-bb25738/raw
rec() { # rec <id> <desc> <command...>
  local id=$1 desc=$2; shift 2
  local out=$EVID/$id.out err=$EVID/$id.err code=$EVID/$id.code
  printf '=== %s ===\n描述: %s\n命令:' "$id" "$desc" >> "$EVID/observations.txt"
  printf ' %q' "$@" >> "$EVID/observations.txt"
  printf '\n时间: %s\n' "$(date -Is)" >> "$EVID/observations.txt"
  "$@" > "$out" 2> "$err"; local rc=$?
  echo "$rc" > "$code"
  printf '退出码: %s\n标准输出:\n' "$rc" >> "$EVID/observations.txt"
  sed 's/^/  | /' "$out" >> "$EVID/observations.txt"
  printf '标准错误:\n' >> "$EVID/observations.txt"
  sed 's/^/  | /' "$err" >> "$EVID/observations.txt"
  printf '\n' >> "$EVID/observations.txt"
}

rec AC-001-1 "默认问候" python3 tool.py greet --name Ada
rec AC-001-2 "全大写问候" python3 tool.py greet --name Ada --shout
rec AC-001-3 "自定义分隔符" python3 tool.py greet --name Ada --sep '; '
rec AC-001-4 "缺少姓名时报参数错误" python3 tool.py greet
rec AC-002-1 "统计词数" python3 tool.py count --file notes.txt
rec AC-002-2 "统计字符数" python3 tool.py count --file notes.txt --chars
rec AC-002-3 "空文件词数为零" python3 tool.py count --file empty.txt
rec AC-002-4 "文件不存在时报错退出" python3 tool.py count --file missing.txt

python3 "$EVID/health_stub.py" & STUB=$!
for _ in $(seq 1 50); do
  if python3 -c 'import socket,sys
s=socket.socket()
sys.exit(0 if s.connect_ex(("127.0.0.1",18080))==0 else 1)' 2>/dev/null; then break; fi
  sleep 0.1
done
rec AC-004-1 "远程服务就绪检查 (本地健康服务 stub)" python3 tool.py health --url http://127.0.0.1:18080/health
kill "$STUB" 2>/dev/null; wait "$STUB" 2>/dev/null
echo "health stub 已停止, 端口 18080 已释放" >> "$EVID/observations.txt"

rec AC-003-1 "默认 JSON 导出" python3 tool.py export --name Ada
rec AC-003-2 "缩进导出" python3 tool.py export --name Ada --pretty
rec AC-003-3 "未知格式报错退出" python3 tool.py export --name Ada --format yaml
