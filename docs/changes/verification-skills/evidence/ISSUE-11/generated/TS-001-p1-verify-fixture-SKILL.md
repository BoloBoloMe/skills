---
name: verify-fixture
description: 在本项目真实跑一遍笔记记录功能 A: 命令行 add/list 与网页列表/提交, 含启动, 检查, 取证, 清理.
disable-model-invocation: true
---

# 验证 fixture 笔记应用

依据: `PRODUCT.md` 状态"已确认", 确认来源"用户 2026-10-18 逐条确认", 本轮范围"功能 A 笔记记录".

本配方只覆盖 AC-A1 与 AC-A2. 不把单元测试当验收证据, 必须走真实入口.

## 1. 覆盖范围

- AC-A1: 命令行 `add` 之后 `list` 输出包含刚提交的文字.
- AC-A2: 网页根路径 HTML 列表包含已有笔记; 向网页提交新笔记后, 列表出现该文字.

范围外, 本配方不验证:
- 导出 CSV (`tools/export_csv.py`), 统计 (`tools/stats.py`), 标签 (`notes.cli tag`), 历史导入 (`notes.cli import-legacy`). 原因: `PRODUCT.md` 非目标.
- `GET /notes` JSON 接口. 原因: 不属于 AC-A2 的根路径 HTML 列表.
- 浏览器内表单提交. 原因: 页面没有表单, 见第 7 节.

## 2. 已观察到的运行事实

- 项目根: `/tmp/orchestra-11/p1-dual`. 所有命令都在此目录执行, 否则 `import notes` 失败.
- 应用: Python 包 `notes`. 入口 `notes.cli` 与 `notes.web`, 无第三方依赖.
- Python: 3.14.x. 现场观察到 `/usr/bin/python3` 为 3.14.4, 经 `uv run python` 包装时为 3.14.7, 两者都跑通. 按 `PRODUCT.md` 用 `python3`, 不要改成 `python`.
- 数据目录: 环境变量 `NOTES_DATA_DIR`, 默认 `./.notes-data` (相对当前目录). 数据文件是其中的 `notes.json`, 首次读写时自动创建.
- 网页: `python3 -m notes.web --port <端口>`. 默认端口 8791, 只监听 `127.0.0.1`. 启动后打印 `listening on http://127.0.0.1:<端口>/`.
- 根路径 `GET /` 返回 HTML 列表, 每条形如 `<li>文字</li>`. 页面没有输入框或表单.
- 提交新笔记: `POST /`, 字段名 `text`. 表单编码与 JSON 两种都已观察可用, 返回 201 和该条 JSON.
- 既有测试: `./check.sh`, 实际 2 个测试通过. 只测 `notes.store` 的 add/load, 不覆盖 CLI 与网页, 不能替代本配方.
- 前置数据: 无需种子数据. 全新临时数据目录从空列表开始.

## 3. 共用准备

始终使用临时数据目录, 避免污染项目默认的 `.notes-data`. 证据放 `/tmp`, 不写进仓库.

```sh
cd /tmp/orchestra-11/p1-dual
export EVIDENCE="$(mktemp -d /tmp/verify-fixture.XXXXXX)"
export NOTES_DATA_DIR="$(mktemp -d /tmp/verify-fixture-data.XXXXXX)"
export PORT=18791
echo "EVIDENCE=$EVIDENCE"
echo "NOTES_DATA_DIR=$NOTES_DATA_DIR"
```

检查端口是否空闲. 有输出且退出码 0 表示已被占用, 换一个端口再试.

```sh
if curl -sS -m 1 -o /dev/null "http://127.0.0.1:$PORT/"; then
  echo "端口 $PORT 已被占用, 换端口"
else
  echo "端口 $PORT 可用"
fi
```

## 4. 共用启动与实例检查

命令行入口是短进程, 无需 start/stop. 网页入口按下面的方式启动, 检查, 停止.

启动, 等待就绪:

```sh
cd /tmp/orchestra-11/p1-dual
setsid python3 -m notes.web --port "$PORT" > "$EVIDENCE/web.log" 2>&1 &
SERVER_PID=$!
for i in $(seq 1 25); do
  grep -q "listening on http://127.0.0.1:$PORT/" "$EVIDENCE/web.log" 2>/dev/null && break
  sleep 0.2
done
cat "$EVIDENCE/web.log"
```

期望第一行为 `listening on http://127.0.0.1:18791/`. 再确认根路径可访问:

```sh
curl -fsS -m 2 "http://127.0.0.1:$PORT/" -o "$EVIDENCE/web-root-initial.html"
echo "rc=$?"
cat "$EVIDENCE/web-root-initial.html"
```

期望退出码 0, HTML 含 `<ul></ul>` (全新数据目录).

停止. 用进程组结束, 不要只 kill 包装进程:

```sh
kill -- -"$SERVER_PID" 2>/dev/null || kill "$SERVER_PID" 2>/dev/null
sleep 0.5
if curl -sS -m 1 -o /dev/null "http://127.0.0.1:$PORT/"; then
  echo "仍在运行, 按端口查残留: pgrep -af 'notes[.]web --port $PORT'"
else
  echo "已停止"
fi
```

注意: 本机 `python3` 可能被 shell 包装成 `uv run python`, 只 kill `$!` 会留下真正的 Python 子进程, 所以用 `setsid` 加 `kill -- -PID`. 也不要在自身命令行含有 `notes.web` 字样的 shell 里 `pkill -f "notes.web"`, 已观察到会误杀自己.

## 5. 功能 A: 笔记记录

### A1 命令行 add / list

完整可粘贴脚本. 每条命令都能单独重跑, 但重跑前请确认 `$NOTES_DATA_DIR` 已导出.

```sh
cd /tmp/orchestra-11/p1-dual
export NOTES_DATA_DIR="$(mktemp -d /tmp/verify-fixture-data.XXXXXX)"
export EVIDENCE="$(mktemp -d /tmp/verify-fixture.XXXXXX)"
TEXT="AC-A1-$(date +%s)"

python3 -m notes.cli add "$TEXT" | tee "$EVIDENCE/cli-add.txt"
python3 -m notes.cli list | tee "$EVIDENCE/cli-list.txt"

grep -F -- "$TEXT" "$EVIDENCE/cli-list.txt" && echo "AC-A1 PASS" || echo "AC-A1 FAIL"
```

期望:
- `add` 输出 `added 1: <TEXT>`. 全新目录第一条 id 为 1.
- `list` 输出一行 `<TEXT>`, 格式是 `id<TAB>文字`, 如 `1	AC-A1-...`.
- `grep` 命中, 打印 `AC-A1 PASS`.
- `$NOTES_DATA_DIR/notes.json` 存在, 内容含该文字.

可补充检查数据落盘:

```sh
cat "$NOTES_DATA_DIR/notes.json"
```

### A2 网页根路径列表与提交

先经命令行造一条"已存在"的笔记, 再启网页, 验证列表, 再 POST 新笔记, 再验证列表. 提交用 `--data-urlencode` 编码中文.

```sh
cd /tmp/orchestra-11/p1-dual
export NOTES_DATA_DIR="$(mktemp -d /tmp/verify-fixture-data.XXXXXX)"
export EVIDENCE="$(mktemp -d /tmp/verify-fixture.XXXXXX)"
export PORT=18791
SEED="AC-A2-既有-$(date +%s)"
NEW="AC-A2-新增-$(date +%s)"

python3 -m notes.cli add "$SEED" | tee "$EVIDENCE/cli-seed.txt"

setsid python3 -m notes.web --port "$PORT" > "$EVIDENCE/web.log" 2>&1 &
SERVER_PID=$!
for i in $(seq 1 25); do
  grep -q "listening on http://127.0.0.1:$PORT/" "$EVIDENCE/web.log" 2>/dev/null && break
  sleep 0.2
done

curl -fsS -m 2 "http://127.0.0.1:$PORT/" -o "$EVIDENCE/web-root-before.html"
curl -sS -i -m 2 -X POST --data-urlencode "text=$NEW" "http://127.0.0.1:$PORT/" > "$EVIDENCE/web-post.txt"
curl -fsS -m 2 "http://127.0.0.1:$PORT/" -o "$EVIDENCE/web-root-after.html"
python3 -m notes.cli list > "$EVIDENCE/cli-list-after.txt"

kill -- -"$SERVER_PID" 2>/dev/null || kill "$SERVER_PID" 2>/dev/null

echo "--- before ---"; cat "$EVIDENCE/web-root-before.html"
echo "--- post ---";   head -20 "$EVIDENCE/web-post.txt"
echo "--- after ---";  cat "$EVIDENCE/web-root-after.html"
echo "--- cli ---";    cat "$EVIDENCE/cli-list-after.txt"
```

期望:
1. 启动日志含 `listening on http://127.0.0.1:18791/`.
2. `web-root-before.html` 含 `<li>$SEED</li>`, 即根路径列出了已有笔记.
3. `web-post.txt` 首行 `HTTP/1.0 201 Created`, 正文 `{"id": 2, "text": "$NEW"}`.
4. `web-root-after.html` 同时含 `<li>$SEED</li>` 与 `<li>$NEW</li>`.
5. `cli-list-after.txt` 也出现 `$NEW`, 证明网页提交写入了同一数据目录.
6. `web.log` 有对应的 `GET /` 200 与 `POST /` 201 记录.

逐条核对:

```sh
grep -F -- "<li>$SEED</li>" "$EVIDENCE/web-root-before.html" && echo "A2-list PASS" || echo "A2-list FAIL"
grep -F -- "201 Created" "$EVIDENCE/web-post.txt" && grep -F -- "$NEW" "$EVIDENCE/web-post.txt" && echo "A2-post PASS" || echo "A2-post FAIL"
grep -F -- "<li>$NEW</li>" "$EVIDENCE/web-root-after.html" && echo "A2-after PASS" || echo "A2-after FAIL"
grep -F -- "$NEW" "$EVIDENCE/cli-list-after.txt" && echo "A2-shared-store PASS" || echo "A2-shared-store FAIL"
```

## 6. 取证

每次验证保留一个临时证据目录 `$EVIDENCE`, 关键文件:
- `cli-add.txt`, `cli-list.txt`, `cli-seed.txt`, `cli-list-after.txt`: 命令行原始输出.
- `web.log`: 启动行与请求日志.
- `web-root-initial.html`, `web-root-before.html`, `web-root-after.html`: 根路径 HTML 快照.
- `web-post.txt`: POST 响应头与正文.
- `$NOTES_DATA_DIR/notes.json`: 数据落盘原文.

报告时直接引用这些文件里的行, 不要只写"已通过".

## 7. 未确认与边界

- 浏览器内提交未确认: 根路径 HTML 只有 `<ul>`, 没有 form/input, 无法在页面上点出提交. 本配方用 `POST /` 验证 AC-A2 的"向网页提交". 若验收要求页面表单, 当前实现不满足, 需产品与实现确认.
- 默认端口 8791 已观察可用, 但可能被占用. 配方固定显式传 `--port 18791`, 冲突时换端口.
- 多实例并发写同一数据目录未验证, 不在本轮 AC.
- 删除, 修改, 分页, 排序均无入口, 不在本轮 AC.
- 未提供 `TECHNICAL.md` 与 `EXECUTION.md`; 本配方依据 `PRODUCT.md`, `README.md`, `check.sh` 与现场观察.

## 8. 清理

```sh
# 先停网页, 再删临时目录
kill -- -"$SERVER_PID" 2>/dev/null || kill "$SERVER_PID" 2>/dev/null
pgrep -af "notes[.]web --port $PORT" || echo "无残留"
rm -rf "$NOTES_DATA_DIR" "$EVIDENCE"
```

不要删除项目里可能存在的真实 `.notes-data`; 本配方始终用 `/tmp` 下的临时数据目录.
