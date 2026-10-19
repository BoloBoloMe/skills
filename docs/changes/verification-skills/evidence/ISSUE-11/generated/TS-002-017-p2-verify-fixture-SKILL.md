---
name: verify-fixture
description: fixture 笔记应用的项目级验证配方, 按 PRODUCT.md 跑命令行增改查, 标签, 历史导入与网页列表并留证.
disable-model-invocation: true
---

# verify-fixture: 笔记应用验证配方

## 这份配方验什么

本轮只验 `PRODUCT.md` 的三条功能 (A 笔记记录, B 标签, C 历史数据导入), 共 4 条判据: AC-A1, AC-A2, AC-B1, AC-C1. 判据以项目根的 `PRODUCT.md` 为准; 本配方只写怎么跑, 看什么, 证据放哪.

不覆盖, 理由:

- `tools/export_csv.py` 导出与 `tools/stats.py` 统计: `PRODUCT.md` 明确列为非目标.
- 网页 `/notes` JSON 接口: `PRODUCT.md` 没把它列为用户入口.
- `./check.sh` 单元测试: 开发自测, 不是产品判据, 只能当辅助信号.
- `deploy/global-skills/verify-fixture/SKILL.md`: 固定副本, 只读核对, 不得修改, 也不得当作本次加载来源.

## 共用规则 (每节都适用)

### 1. 项目根

本文件位于 `<项目根>/.agents/skills/verify-fixture/SKILL.md`, 项目根 = 向上三级. 下面所有 `python3 -m ...` 都在项目根执行, 否则 `notes` 包导入失败.

### 2. 解释器

`PRODUCT.md` 写的是 `python3 -m notes.cli` / `python3 -m notes.web`. 本机 `python3 --version` 是 3.14.7. `uv run python -m ...` 也能跑, 配方统一写 `python3`, 两种都试过.

### 3. 数据目录隔离 (每个功能都先做)

默认数据目录是项目里的 `.notes-data`, 直接跑会把验证数据留在项目里. 每节开头换新的临时目录:

```sh
export NOTES_DATA_DIR=$(mktemp -d /tmp/verify-fixture-data.XXXXXX)
echo "$NOTES_DATA_DIR"
```

必须 `export`, 同一节的 add / list / tag / import-legacy / web 共用它. 本节验完 `rm -rf "$NOTES_DATA_DIR"`.

### 4. 端口 (网页节)

不要用默认 8791, 免得撞上别的实例. 取空闲端口:

```sh
PORT=$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1]);s.close()')
```

服务只监听 `127.0.0.1`, 访问地址是 `http://127.0.0.1:$PORT/`.

### 5. 证据目录

证据放仓库外的固定根目录, 每次一个 run 子目录, 免得污染 `git status`:

```sh
EVIDENCE=/tmp/verify-fixture-evidence/$(date +%Y%m%d-%H%M%S)
mkdir -p "$EVIDENCE"
python3 --version > "$EVIDENCE/env.txt"
git -C <项目根> rev-parse --short HEAD >> "$EVIDENCE/env.txt" 2>&1
git -C <项目根> status --porcelain >> "$EVIDENCE/env.txt"
```

每一节的 "取证" 小节列出该节必须留下的文件名.

### 6. 只读实例检查

网页节用这三样, 全是只读:

```sh
ss -ltnp "sport = :$PORT"        # 端口归属: 期望 python3.x, pid=<服务 pid>
cat "$EVIDENCE/web-server.log"   # 首行 listening on http://127.0.0.1:<端口>/
python3 --version                # 解释器版本
```

杀进程只用 `ss` 或日志里确认过的 pid, 不要按进程名批量杀.

### 7. 清理

```sh
kill "$SERVER_PID"; sleep 0.3
ss -ltn "sport = :$PORT" | tail -n +2 | wc -l   # 期望 0
rm -rf "$NOTES_DATA_DIR"
```

清理命令与实际输出写进 `$EVIDENCE/cleanup.txt`.

### 8. 改动边界

验证只允许产生三类东西: `.agents/skills/verify-fixture/` 下的文件, 仓库外 `/tmp` 下的证据与临时数据, 以及被 `.gitignore` 忽略的 `__pycache__/`. 交付前对照:

```sh
git -C <项目根> status --porcelain   # 期望只有 `?? .agents/`
git -C <项目根> diff --stat          # 期望空
```

出现别的改动就说明验证动了产品, 记下来并停手.

## 功能 A: 笔记记录

### A-1 命令行 add / list (AC-A1)

前置: 无, 空数据目录也能跑 (`list` 输出为空, 退出码 0).

步骤:

```sh
export NOTES_DATA_DIR=$(mktemp -d /tmp/verify-fixture-data.XXXXXX)
cd <项目根>
TEXT="验证笔记A1-$(date +%s)"
python3 -m notes.cli add "$TEXT" | tee "$EVIDENCE/a1-add.txt"
python3 -m notes.cli list | tee "$EVIDENCE/a1-list.txt"
cp "$NOTES_DATA_DIR/notes.json" "$EVIDENCE/a1-notes.json"
grep -F "$TEXT" "$EVIDENCE/a1-list.txt"
```

期望:

- `add` 退出码 0, 输出 `added 1: <文字>`.
- `list` 退出码 0, 输出一行 `<id>\t<文字>`, 上面那条 `grep` 命中.
- `a1-notes.json` 里能读到同一条文字.

取证: `a1-add.txt`, `a1-list.txt`, `a1-notes.json`.

### A-2 网页 (AC-A2)

前置: 网页读同一个 `NOTES_DATA_DIR`; 先放一条已有笔记, 才能同时验 "已有笔记可见" 和 "提交后可见".

一条命令跑完 (我跑过, 输出 PASS):

```sh
.agents/skills/verify-fixture/run-ac-a2-web.sh [证据目录]
```

脚本做的事: 建临时数据目录并塞一条已有笔记, 取空闲端口启动 `python3 -m notes.web --port <端口>`, 轮询到可访问, GET 根路径存 `a2-root-before.html`, 用 `ss` 记端口归属, POST 一条新笔记, 再 GET 存 `a2-root-after.html`, 用 `google-chrome --headless=new` 截 `a2-root.png`, 最后杀进程并确认端口释放. 输出 `PASS` / `FAIL` 行, 有 FAIL 时退出码非 0.

想自己敲的等价步骤:

```sh
export NOTES_DATA_DIR=$(mktemp -d /tmp/verify-fixture-data.XXXXXX)
cd <项目根>
python3 -m notes.cli add "网页前已有笔记"
PORT=$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1]);s.close()')
python3 -m notes.web --port "$PORT" > "$EVIDENCE/web-server.log" 2>&1 &
SERVER_PID=$!
for i in $(seq 1 50); do curl -fsS "http://127.0.0.1:$PORT/" >/dev/null 2>&1 && break; sleep 0.2; done
curl -sS "http://127.0.0.1:$PORT/" -o "$EVIDENCE/a2-root-before.html"
curl -sS -i -X POST --data-urlencode "text=网页提交的验证笔记" "http://127.0.0.1:$PORT/" > "$EVIDENCE/a2-post.txt"
curl -sS "http://127.0.0.1:$PORT/" -o "$EVIDENCE/a2-root-after.html"
grep -F "网页前已有笔记" "$EVIDENCE/a2-root-before.html"
grep -F "网页提交的验证笔记" "$EVIDENCE/a2-root-after.html"
```

期望:

- 启动日志首行 `listening on http://127.0.0.1:<端口>/`.
- 根路径 HTML 形如 `...<h1>笔记</h1><ul><li>...`; 提交前含已有笔记.
- POST 返回 `HTTP/1.0 201 Created`, body 为 `{"id": 2, "text": "网页提交的验证笔记"}`.
- 第二次 GET 的列表里两条文字都在.
- 截图里能看到标题 "笔记" 和笔记条目.

取证: `a2-root-before.html`, `a2-post.txt` (脚本里拆成 `a2-post-headers.txt` 与 `a2-post-status.txt`), `a2-root-after.html`, `a2-port-owner.txt`, `web-server.log` (脚本里是 `a2-server.log`), `a2-root.png`, `a2-form-check.txt`, `a2-cleanup.txt`.

已知缺口 (AC-A2 后半句): 根页面只有 `<ul>` 列表, 没有 `<form>`, 没有输入框和按钮, 所以 "在浏览器里提交一条新笔记" 在页面上做不了, 浏览器只能看不能提交. 提交入口是 `POST /` (表单编码, 或 JSON `{"text": ...}`), 只能用 curl 之类直接发. 见 `a2-form-check.txt` 里的 `form=absent` 与截图. 这一项按未验证记录, 见文末清单.

## 功能 B: 标签 (AC-B1)

前置: 数据目录可写; 不需要先有笔记.

步骤:

```sh
export NOTES_DATA_DIR=$(mktemp -d /tmp/verify-fixture-data.XXXXXX)
cd <项目根>
set +e
python3 -m notes.cli tag "验证标签B1" > "$EVIDENCE/b1-tag.out" 2>&1
echo "exit=$?" >> "$EVIDENCE/b1-tag.out"
set -e
cat "$EVIDENCE/b1-tag.out"
cp "$NOTES_DATA_DIR/tags.txt" "$EVIDENCE/b1-tags.txt"
```

期望: 输出恰好一行 `tagged: 验证标签B1`, 接着一行 `exit=0`; `b1-tags.txt` 含该标签名.

取证: `b1-tag.out`, `b1-tags.txt`.

备注: 标签不查重, 重复执行会重复写进 `tags.txt`. 这是观察到的行为, 不是本轮判据.

## 功能 C: 历史数据导入 (AC-C1)

前置: 上游导出流程产出的 `seed/legacy-export.json`, 仓库里没有. 可用环境变量 `NOTES_LEGACY_EXPORT` 指向别的路径; 不设时按当前目录找 `seed/legacy-export.json`.

### C-0 缺前置时的行为 (我跑过)

```sh
cd <项目根>
python3 -m notes.cli import-legacy; echo "exit=$?"
```

期望: stderr 一行 `missing prerequisite: seed/legacy-export.json`, exit=2. 这是缺前置的报错, 不算 AC-C1 通过.

取证: `c1-missing.txt` (命令与输出一起重定向).

### C-1 提供文件后 (我跑过, 用的是仓库外临时文件)

```sh
export NOTES_DATA_DIR=$(mktemp -d /tmp/verify-fixture-data.XXXXXX)
cd <项目根>
SYNTH=$(mktemp -d /tmp/verify-fixture-export.XXXXXX)
printf '["旧笔记一", "旧笔记二", "旧笔记三"]' > "$SYNTH/legacy-export.json"
NOTES_LEGACY_EXPORT="$SYNTH/legacy-export.json" python3 -m notes.cli import-legacy | tee "$EVIDENCE/c1-import.txt"
python3 -m notes.cli list | tee "$EVIDENCE/c1-list.txt"
cp "$NOTES_DATA_DIR/notes.json" "$EVIDENCE/c1-notes.json"
grep -c "旧笔记" "$EVIDENCE/c1-list.txt"
```

期望: `imported 3` 且 exit=0; `list` 三行, 三段文字都在; `grep -c` 输出 `3`.

取证: `c1-import.txt`, `c1-list.txt`, `c1-notes.json`.

重要限制: `$SYNTH/legacy-export.json` 是我手写的 JSON 字符串数组, 只用来验证导入流程, 不是上游真实导出. 真实 `seed/legacy-export.json` 未提供, 所以 AC-C1 针对真实历史数据的那部分按未验证记录. 不要把临时文件放进仓库冒充 `seed/`.

## 未验证清单 (截至本配方生成时)

- AC-A2 在浏览器里直接提交新笔记: 页面无表单无输入框, 做不了. 已验的是 GET 根路径 (curl 与 chrome headless 截图) 和 `POST /` 接口.
- AC-C1 用上游真实导出文件: 仓库无 `seed/legacy-export.json`, 也没有上游产物. 已验的是同格式临时文件.
- 默认端口 8791: 没单独跑, 配方一律用 `--port` 指定空闲端口.
- 并发写入与持久化边界: 不在本轮判据, 未验.

## 交付前自检

1. `sh -n .agents/skills/verify-fixture/run-ac-a2-web.sh` 无语法错误.
2. 每节跑完后核对上面 "取证" 列出的文件都存在且非空.
3. `git status --porcelain` 只有 `?? .agents/`; `git diff --stat` 为空.
4. 加载来源核对: 在项目里用 `/skill:verify-fixture` 加载时, 宿主报的 location 必须是 `<项目根>/.agents/skills/verify-fixture/SKILL.md`, 不是 `deploy/global-skills/verify-fixture/SKILL.md`. 后者是固定副本, sha256 以 `63e832cd` 开头, 运行前后都不许变.
