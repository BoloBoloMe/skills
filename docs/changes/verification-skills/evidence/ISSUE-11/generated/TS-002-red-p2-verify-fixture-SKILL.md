---
name: verify-fixture
description: 按 PRODUCT.md 验收 fixture 笔记应用: 命令行新增/列出, 网页列表与提交, 标签, 历史导入.
disable-model-invocation: true
---

# fixture 笔记应用验证配方

## 0. 本次覆盖范围

- 判据来源: 仓库根目录 `PRODUCT.md`, 状态"已确认", 确认来源为用户 2026-10-18 逐条确认.
- 覆盖功能:
  - 功能 A 笔记记录: 命令行 `add`/`list`, 网页根路径列表, 网页提交后列表更新.
  - 功能 B 标签: 命令行 `tag`.
  - 功能 C 历史数据导入: 命令行 `import-legacy`.
- 共用规则: 启动, 实例检查, 取证, 清理.
- 明确排除: `tools/export_csv.py`, `tools/stats.py`, 以及 PRODUCT.md 非目标里的导出与统计. 不为它们编写步骤.
- 网页内部端点 `/notes` 只是诊断用, 不是本轮判据, 不计入功能地图.

## 1. 前置与硬约束

- 必须在仓库根目录执行, 也就是同时含 `PRODUCT.md`, `notes/`, `check.sh` 的目录. 本机当前为 `/tmp/orchestra-11/p2-gaps`.
  - 在其他目录执行 `python3 -m notes.cli` 会报 `ModuleNotFoundError: No module named 'notes'`, 实测退出码 1.
- 需要 `python3`, 实测 3.14.4 与 3.14.7 都能通过 (不同 shell 可能解析到不同解释器).
  - 若本机规则要求用 uv, 可把 `python3` 换成 `uv run python`. 实测 `uv run python -m notes.cli list` 能正常启动, 其余子命令未逐一用 uv 重跑. PRODUCT.md 原文入口仍按 `python3` 记录.
- 下面的命令默认在同一个 shell 里执行, 因为依赖已导出的 `NOTES_DATA_DIR`.
- 用 `NOTES_DATA_DIR` 把数据放到隔离目录, 不写仓库默认的 `.notes-data`.
- 不要改动 `deploy/global-skills/verify-fixture/SKILL.md`. 它是全局部署副本替身, 与本验证无关.
  - 实测基线 sha256: `63e832cd18e6e0c802e8176a39d4b576dac6e4a28ffce0a7d1ffe211a63c5775`.

初始化, 每个新验证会话先跑:

```sh
cd /tmp/orchestra-11/p2-gaps
export NOTES_DATA_DIR="$PWD/.verify-data"
export EVIDENCE="$PWD/.verify-evidence"
rm -rf "$NOTES_DATA_DIR"
mkdir -p "$NOTES_DATA_DIR" "$EVIDENCE"
```

注意: 不要省略 `mkdir -p "$NOTES_DATA_DIR"`. 数据目录不存在时直接跑 `tag` 会抛 `FileNotFoundError`, 退出码 1, 已实测. 先跑 `add` 或 `list` 也会顺带建目录.

## 2. 既有测试入口

不是本轮判据, 只做环境自检:

```sh
./check.sh
```

期望: 输出 `Ran 2 tests`, 最后 `OK`, 退出码 0. 实测通过. 它不证明 A/B/C 的产品判据.

## 3. 功能地图

| 功能 | 用户入口 | 通过判据 | 小节 |
| --- | --- | --- | --- |
| A 笔记记录 | `python3 -m notes.cli add <文字>`, `python3 -m notes.cli list` | AC-A1 | 4.1 |
| A 笔记记录 | `python3 -m notes.web --port <端口>`, 浏览器打开 `http://127.0.0.1:<端口>/` | AC-A2 | 4.2 |
| B 标签 | `python3 -m notes.cli tag <名称>` | AC-B1 | 5 |
| C 历史导入 | `python3 -m notes.cli import-legacy`, 前置 `seed/legacy-export.json` | AC-C1 | 6 |

## 4. 功能 A: 笔记记录

### 4.1 命令行 add/list, AC-A1

在已跑过初始化的小节 1 环境里执行:

```sh
python3 -m notes.cli add "验证笔记A1" > "$EVIDENCE/a1-add.txt" 2>&1
echo "add_exit=$?" >> "$EVIDENCE/a1-add.txt"
cat "$EVIDENCE/a1-add.txt"
```

期望:
- 退出码 0.
- 输出 `added 1: 验证笔记A1`. 若数据目录里已有笔记, 编号会顺延, 不是 1.

然后:

```sh
python3 -m notes.cli list > "$EVIDENCE/a1-list.txt" 2>&1
echo "list_exit=$?" >> "$EVIDENCE/a1-list.txt"
cat "$EVIDENCE/a1-list.txt"
grep -F "验证笔记A1" "$EVIDENCE/a1-list.txt"
```

期望:
- 退出码 0.
- 列表含一行 `1<TAB>验证笔记A1`, 实际是制表符分隔的 id 与文字.
- `grep` 退出码 0, 找到这行.

证据: `$EVIDENCE/a1-add.txt`, `$EVIDENCE/a1-list.txt`.

### 4.2 网页列表与提交, AC-A2

启动服务, 用独立端口避免冲突. 下面以 8876 为例:

```sh
PORT=8876
python3 -m notes.web --port "$PORT" > "$EVIDENCE/web.log" 2>&1 &
echo $! > "$EVIDENCE/web.pid"
for i in $(seq 1 50); do
  curl -sf -o /dev/null "http://127.0.0.1:$PORT/" && break
  sleep 0.1
done
cat "$EVIDENCE/web.log"
```

期望:
- `$EVIDENCE/web.log` 出现 `listening on http://127.0.0.1:8876/`.
- 就绪循环在 5 秒内退出, `curl` 返回 0.

实例检查与失败识别:
- 若端口被占用, 进程会退出码 1, 日志含 `OSError: [Errno 98] Address already in use`, 已实测. 换一个 `PORT` 重跑.
- 若日志没有 `listening on` 且 `curl` 一直失败, 先看 `$EVIDENCE/web.log` 的报错, 不要继续提交.

读取根路径列表:

```sh
curl -sS -D "$EVIDENCE/web-get.headers" "http://127.0.0.1:$PORT/" -o "$EVIDENCE/web-before.html"
cat "$EVIDENCE/web-get.headers"
grep -F "验证笔记A1" "$EVIDENCE/web-before.html"
```

期望:
- 响应头含 `HTTP/1.0 200 OK` 与 `Content-Type: text/html; charset=utf-8`.
- HTML 里有 `<li>验证笔记A1</li>`, `grep` 退出码 0.

向网页提交一条新笔记:

```sh
curl -sS -i -X POST --data-urlencode "text=网页提交A2" "http://127.0.0.1:$PORT/" | tee "$EVIDENCE/web-post.txt"
```

期望:
- 状态行 `HTTP/1.0 201 Created`.
- 响应体是 JSON, 形如 `{"id": 2, "text": "网页提交A2"}`. id 取决于当前条数.

重新读取根路径, 确认列表更新:

```sh
curl -sS "http://127.0.0.1:$PORT/" -o "$EVIDENCE/web-after.html"
grep -F "网页提交A2" "$EVIDENCE/web-after.html"
```

期望: HTML 里出现 `<li>网页提交A2</li>`, `grep` 退出码 0. 这满足 AC-A2 的"提交后列表出现这条文字".

浏览器渲染检查, 可选但推荐, 本机已装 google-chrome:

```sh
google-chrome --headless=new --disable-gpu --no-sandbox \
  --user-data-dir=/tmp/verify-fixture-chrome \
  --dump-dom "http://127.0.0.1:$PORT/" > "$EVIDENCE/web-dom.html"
grep -o '<li>[^<]*</li>' "$EVIDENCE/web-dom.html"
```

期望: 退出码 0, 输出页面里的 `<li>` 条目, 含 `验证笔记A1` 和 `网页提交A2`. 实测通过.

人工浏览器入口: 打开 `http://127.0.0.1:8876/`, 应看到标题 `笔记` 和列表.
当前实现的页面 HTML 里没有任何 `<form>` 或 `<input>`, 已实测, 所以没有可点的输入框或提交按钮. "向网页提交"目前只能走上面的 HTTP POST, 再刷新页面看列表. 这是观察到的实现现状, 是否有意如此标为未确认, 见第 9 节.

诊断端点, 不是判据:

```sh
curl -sS "http://127.0.0.1:$PORT/notes"
```

期望: 返回 JSON 数组, 含已保存的笔记. 只用来快速核对存储内容.

结束服务:

```sh
kill "$(cat "$EVIDENCE/web.pid")" 2>/dev/null || true
sleep 0.3
curl -sS --max-time 2 "http://127.0.0.1:$PORT/" >/dev/null 2>&1 || echo "server stopped"
```

期望: 输出 `server stopped`, 端口不再响应.

## 5. 功能 B: 标签, AC-B1

先确保数据目录存在, 避免已实测的 `FileNotFoundError`:

```sh
mkdir -p "$NOTES_DATA_DIR"
python3 -m notes.cli tag "工作" > "$EVIDENCE/b1-tag.txt" 2>&1
echo "tag_exit=$?" >> "$EVIDENCE/b1-tag.txt"
cat "$EVIDENCE/b1-tag.txt"
```

期望:
- 输出 `tagged: 工作`.
- `tag_exit=0`.
- 进程无报错.

核对落盘:

```sh
cat "$NOTES_DATA_DIR/tags.txt" | tee "$EVIDENCE/b1-tags.txt"
```

期望: 内容含 `工作`. 重复执行 `tag` 会继续追加, 文件里出现多行, 已实测.

证据: `$EVIDENCE/b1-tag.txt`, `$EVIDENCE/b1-tags.txt`.

## 6. 功能 C: 历史数据导入, AC-C1

### 6.1 缺前置时的预期失败

仓库不包含 `seed/legacy-export.json`. 先确认这条负向行为:

```sh
python3 -m notes.cli import-legacy > "$EVIDENCE/c1-missing.txt" 2>&1
echo "missing_exit=$?" >> "$EVIDENCE/c1-missing.txt"
cat "$EVIDENCE/c1-missing.txt"
```

期望:
- 标准错误含 `missing prerequisite: seed/legacy-export.json`.
- `missing_exit=2`.
- 这是预期的前置缺失, 不是 AC-C1 通过.

### 6.2 用等价的临时历史数据文件跑 AC-C1

重置同一个隔离数据目录, 保证导入条数清楚, 不影响已经取到的 A/B 证据:

```sh
export NOTES_DATA_DIR="$PWD/.verify-data"
rm -rf "$NOTES_DATA_DIR"
mkdir -p "$NOTES_DATA_DIR"
mkdir -p seed
printf '["历史笔记一", "历史笔记二"]\n' > seed/legacy-export.json
python3 -m notes.cli import-legacy > "$EVIDENCE/c1-import.txt" 2>&1
echo "import_exit=$?" >> "$EVIDENCE/c1-import.txt"
cat "$EVIDENCE/c1-import.txt"
```

期望:
- 输出 `imported 2`, `import_exit=0`.
- 条数等于 JSON 数组长度.

列出导入结果:

```sh
python3 -m notes.cli list > "$EVIDENCE/c1-list.txt" 2>&1
echo "list_exit=$?" >> "$EVIDENCE/c1-list.txt"
cat "$EVIDENCE/c1-list.txt"
grep -F "历史笔记一" "$EVIDENCE/c1-list.txt"
grep -F "历史笔记二" "$EVIDENCE/c1-list.txt"
```

期望:
- 退出码 0.
- 列表含 `1<TAB>历史笔记一` 与 `2<TAB>历史笔记二`.
- 两个 `grep` 都退出码 0.

若要避免在仓库里建 `seed/`, 也可改用环境变量指定文件, 已实测等价:

```sh
printf '["历史笔记一", "历史笔记二"]\n' > "$EVIDENCE/legacy-export.json"
NOTES_LEGACY_EXPORT="$EVIDENCE/legacy-export.json" python3 -m notes.cli import-legacy
```

注意:
- 不要在同一个数据目录重复跑 `import-legacy`, 会重复追加. 实测第二次仍输出 `imported 2`, id 变成 3 和 4, 列表出现重复文字. 要重来就清空数据目录.
- 空数组 `[]` 会输出 `imported 0` 且退出码 0, 已实测, 不能当作成功导入.

证据: `$EVIDENCE/c1-missing.txt`, `$EVIDENCE/c1-import.txt`, `$EVIDENCE/c1-list.txt`.

## 7. 取证清单

建议保留在 `$EVIDENCE`:

| 文件 | 证明 |
| --- | --- |
| `a1-add.txt`, `a1-list.txt` | AC-A1 的提交文字与列表输出, 含退出码 |
| `web-get.headers`, `web-before.html` | 网页根路径 200 且含已有笔记 |
| `web-post.txt` | 网页提交返回 201 与新条目 JSON |
| `web-after.html` | 提交后列表出现新文字 |
| `web-dom.html` | 真实浏览器渲染出的列表, 可选 |
| `b1-tag.txt`, `b1-tags.txt` | AC-B1 输出, 退出码, 标签落盘 |
| `c1-missing.txt` | 缺前置时的预期报错与退出码 2 |
| `c1-import.txt`, `c1-list.txt` | AC-C1 的 `imported 2` 与导入后列表 |
| `web.log`, `web.pid` | 网页实例启动证据与进程号 |

`.verify-evidence/` 与 `.verify-data*` 都是验证临时物, 不要提交.

## 8. 清理

```sh
kill "$(cat "$EVIDENCE/web.pid")" 2>/dev/null || true
rm -rf "$NOTES_DATA_DIR"
rm -f seed/legacy-export.json
rmdir seed 2>/dev/null || true
rm -rf /tmp/verify-fixture-chrome
git status --porcelain
```

期望:
- 没有残留网页进程, 没有 `.notes-data` 或 `.verify-data*` 进入仓库.
- `git status --porcelain` 只剩本 skill 所在的 `.agents/` 未跟踪. 若保留了 `$EVIDENCE`, 也会看到它.
- `seed/` 若原本不存在, 清理后应消失.

## 9. 未确认与已知边界

- 网页表单提交: PRODUCT.md AC-A2 写"向网页提交一条新笔记", 但当前页面没有表单或输入框, 已实测. 本配方用 HTTP POST 加刷新来验证列表更新. 是否本应提供浏览器表单, 未确认, 不要仅凭缺少表单就断言 AC-A2 失败, 但要记录这一差异.
- `tag` 的落盘位置是 `$NOTES_DATA_DIR/tags.txt`, 没有命令行读取标签的入口. AC-B1 只判输出与退出码, 不判标签能否在界面看到.
- 数据目录不存在时 `tag` 失败属于实现细节, 不是产品判据. 配方已用 `mkdir -p` 规避.
- 重复导入会重复追加, 属于观察到的行为, 本轮未规定是否应去重.
- 默认数据目录 `.notes-data` 相对当前工作目录, 本配方不用它; 若有人跑默认路径, 结果会落到仓库内.
- 导出与统计不在本轮范围, 未验证.
- 可选输入 `TECHNICAL.md`, `EXECUTION.md` 未提供, 本配方未依赖. 项目 `README.md` 与测试入口 `check.sh` 存在并已使用.
