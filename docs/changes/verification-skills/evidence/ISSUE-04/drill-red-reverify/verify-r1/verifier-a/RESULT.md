# 独立产品验收结果 - 第 1 组 (verifier-a)

- 项目: /tmp/orchestra-04/red-reverify
- 目标提交: cd087542b4610c49ded0a1278fe8065726b62d9d (开工时 `git rev-parse HEAD` 一致)
- pi session id: 01a15457-d661-738d-be16-621666a876ac
- 开工时间: 2026-10-19T21:27:11+08:00
- 收工时间: 2026-10-19T21:28:17+08:00 (落 marker 时刻)
- 判据来源: docs/changes/relay-board/PRODUCT.md 第 22-52 行 "验收标准" (confirmed-flow: v1)
- 证据目录: docs/changes/relay-board/verify-r1/verifier-a/
- 范围: 仅本次交给本组的 2 条 (AC-001 / BR-001)。未启动、未停止任何实例, 未占用 18101, 未修改源码/配置/测试, 未 git add/commit。

---

## BR-001 (审计) - 本次变更不新增第三方依赖, deps.txt 与上一提交逐项一致

- 编号: BR-001
- 材料类型: **当前观察**(对仓库对象的静态材料核对, 非运行行为结果)
- 结论: **通过**

### 实际命令
在 /tmp/orchestra-04/red-reverify 内执行, 全部原始输出见 `br-001-raw.txt`:

```
git show 8438934:deps.txt
git show cd08754:deps.txt
git diff 8438934 cd08754 -- deps.txt
git show 8438934:deps.txt | sha256sum
git show cd08754:deps.txt | sha256sum
git diff --stat 8438934 cd08754 -- deps.txt
git diff --name-status 8438934 cd08754
```

### 原始输出 (2026-10-19T21:27:15+08:00)

```
=== cmd1: git show 8438934:deps.txt ===
python3 标准库, 无第三方依赖
exit=0

=== cmd2: git show cd08754:deps.txt ===
python3 标准库, 无第三方依赖
exit=0

=== cmd3: git diff 8438934 cd08754 -- deps.txt ===
exit=0                 <- 无任何输出, 即零差异

=== cmd4: byte compare via sha256 ===
6390d8992b2242f1e885b0de7ad65c20fbcba97ecfc0980b1f9675b5f90f9d68  -
6390d8992b2242f1e885b0de7ad65c20fbcba97ecfc0980b1f9675b5f90f9d68  -
exit=0

=== cmd5: git diff --stat 8438934 cd08754 -- deps.txt ===
exit=0                 <- 无输出, 零改动行

=== cmd6: 两提交间全部改动文件 ===
M	app.py
exit=0
```

### 逐项核对 (deps.txt 两个版本逐行一致)
- 上一提交 8438934 内容: 1 行, 唯一样本 `python3 标准库, 无第三方依赖`
- 目标提交 cd08754 内容: 1 行, 唯一样本 `python3 标准库, 无第三方依赖`
- 行数一致 (1 = 1), 逐行文本一致, 且字节级一致 (两侧 sha256 相同: `6390d899...f9d68`), `git diff` 对该文件输出为空, 退出码 0
- 两提交间文件清单相同 (`git ls-tree -r --name-only` 均为 6 个文件: .gitignore, README.md, app.py, deps.txt, docs/changes/relay-board/PRODUCT.md, tests/test_app.py), 仅 app.py 内容被修改; 没有引入任何新的依赖描述文件 (无 requirements.txt / package.json / lock 文件等)

### 辅助材料 (不构成主判据)
`app.py` 的 import 清单, 原始输出见 `br-001-aux.txt`:

- 当前提交(工作区, 与 cd08754:app.py 一致, 仅多了 json):
  `argparse, json, sys, time, datetime/timezone, http.server BaseHTTPRequestHandler/ThreadingHTTPServer, pathlib Path, urllib.parse parse_qs/urlparse`, 函数内 `urllib.request`
- 上一提交 8438934: 同上但无 `json`
- 全部为标准库模块, 无第三方包名

### 可复核位置
- 证据: `docs/changes/relay-board/verify-r1/verifier-a/br-001-raw.txt`, `br-001-aux.txt`
- 复核命令: `git diff 8438934 cd08754 -- deps.txt` (应为空), `git show cd08754:deps.txt`

---

## AC-001 / 场景 AC-001-1 状态页截图

- 编号: AC-001-1
- 材料类型: **当前观察**(浏览器真实渲染 + 截图目视核对)
- 结论: **通过**

### 假定条件先验证
`python3 app.py health --port 18101` 轮询, 原始逐条记录见 `ac-001-health-polls.txt`。第 1-8 次 `Exit 1 / Connection refused`, 第 9 次 (2026-10-19T21:28:00+08:00) 得到:

```
[2026-10-19T21:28:00+08:00] poll#9 exit=0 out=ok instance=alpha
```

假定成立 (实例由第 2 组 verify-g2 启动, 本组全程未启停实例、未占用端口)。截图前又复核一次: `ok instance=alpha`, exit=0 (见 `ac-001-screenshot-raw.txt` 首段)。

### 实际命令 (README 第 23-24 行的无头 Chrome 方式, 输出改到证据目录)

```
google-chrome --headless --disable-gpu --no-sandbox --window-size=900,400 \
  --screenshot=<证据目录>/ac-001-status-page.png \
  --virtual-time-budget=3000 http://127.0.0.1:18101/status-page
```

### 原始输出 (2026-10-19T21:28:03+08:00, 见 `ac-001-screenshot-raw.txt`)

```
health re-check: ok instance=alpha   exit=0
Google Chrome 154.0.8037.97          exit=0
8788 bytes written to file .../ac-001-status-page.png
exit=0
-rw-rw-r-- 1 bolo bolo 8788 Oct 19 21:28 ac-001-status-page.png
PNG image data, 900 x 400, 8-bit/color RGB, non-interlaced
md5 57e24e1551247a5497cee2a3ce6bf0b0
```

### 目视核对截图 (本人查看图片, 逐处写出所见字符)
证据图片: `ac-001-status-page.png` (900x400, 白底, 见下)

- 标题行: 我看到浏览器页面左上角渲染出加粗大字 `relay board`
- 第 1 行正文: 我看到字符 `instance=alpha`  (逐字符: i n s t a n c e = a l p h a)
- 第 2 行正文: 我看到字符 `state=ready`  (逐字符: s t a t e = r e a d y)
- 第 3 行正文: 我看到字符 `version=relay-v1`  (逐字符: v e r s i o n = r e l a y - v 1)

一处正文一行的三处文本与判据要求的 `instance=alpha`, `state=ready`, `version=relay-v1` 完全一致, 无多余字符、无被截断/遮挡, 页面无报错信息, 无空白页。

### 辅助证据 (不替代截图)
`ac-001-http-status-page.txt`: `curl -sS -i http://127.0.0.1:18101/status-page` 返回 `HTTP/1.0 200 OK`, `Content-Type: text/html; charset=utf-8`, `Content-Length: 190`, 正文为
`<h1>relay board</h1><p>instance=alpha</p><p>state=ready</p><p>version=relay-v1</p>` 。

### 偏差
无。仅一处执行细节说明: README 的截图路径是 `runtime/alpha-status.png`, 按本组纪律 (不改动 runtime/ 他人产物) 改存到本证据目录, 命令其余参数一致。

---

## 汇总

| 编号 | 材料类型 | 结论 |
|---|---|---|
| BR-001 | 当前观察 (静态材料核对, 非运行行为) | 通过 |
| AC-001-1 | 当前观察 (浏览器渲染截图目视) | 通过 |

- 未验证项: 无
- 缺陷: 未发现
- 本组未做的必验项之外内容一律未涉及 (AC-002/003/004 属其他分工)
