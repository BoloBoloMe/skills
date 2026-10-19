#!/bin/bash
# R 阶段: 逐字执行 .agents/skills/verify-board/SKILL.md 的命令
cd /tmp/orchestra-05/red-stalerecipe || exit 1
RAW=docs/changes/board/evidence/accept-d1f656e-recipe-r1/acceptor/raw
step() { echo "[step] $*"; echo "[time] $(date -Is)"; }

{ step "recipe: mkdir -p runtime/board"; mkdir -p runtime/board; echo "[exit] $?"; } > $RAW/R0-mkdir.log 2>&1

{ step "recipe: python3 app.py serve --port 18001 --data-root runtime/board &"
  bash -c 'python3 app.py serve --port 18001 --data-root runtime/board & pid=$!; wait $pid; echo "[serve-exit] $?"'
  echo "[wrapper-exit] $?"; } > $RAW/R1-serve.stdout 2> $RAW/R1-serve.stderr
echo "[time] $(date -Is)" > $RAW/R1-serve.meta
echo "[cmd] python3 app.py serve --port 18001 --data-root runtime/board &  (backgrounded 按配方, 等待子进程取真实退出码)" >> $RAW/R1-serve.meta

for c in health status report; do
  { step "recipe: python3 app.py $c --port 18001"
    bash -c "python3 app.py $c --port 18001"
    echo "[exit] $?"; } > $RAW/R1-$c.stdout 2> $RAW/R1-$c.stderr
  echo "[time] $(date -Is)" > $RAW/R1-$c.meta
  echo "[cmd] python3 app.py $c --port 18001" >> $RAW/R1-$c.meta
done

{ step "ps/ss on 18001"
  echo "[cmd] ss -ltnp | grep :18001"; ss -ltnp 2>/dev/null | grep ':18001' || echo "NOT LISTENING"
  echo "[cmd] ps -ef | grep 'app.py serve' | grep -v grep"; ps -ef | grep 'app.py serve' | grep -v grep || echo "NO SERVE PROCESS"
  echo "[exit] recorded"; } > $RAW/R2-listen-check.log 2>&1
