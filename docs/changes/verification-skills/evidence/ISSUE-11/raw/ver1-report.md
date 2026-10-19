验收跑完, 4 条判据 3 条通过, 1 条只验了一半 (缺表单, 见下).

结果
- AC-A1 通过: `add` 输出 `added 1: 验证笔记A1-1792404190`, 退出码 0; `list` 一行 `1\t<同文字>`, grep 命中; `notes.json` 同文字.
- AC-A2 通过 (能验的部分): 根路径 HTML 有 `<h1>笔记</h1>` + `<ul>`, 提交前含 "网页前已有笔记"; `POST /` 返回 `HTTP/1.0 201 Created`, body `{"id": 2, "text": "网页提交的验证笔记"}`; 二次 GET 两条都在; chrome headless 截图可见标题与两条条目. 但页面 `form=absent`, 没有输入框/按钮, 所以 "在浏览器里提交" 这半句做不了, 提交只能走 curl.
- AC-B1 通过: 输出恰一行 `tagged: 验证标签B1`, 退出码 0, `tags.txt` 含该名.
- AC-C1 通过 (仅流程): `imported 3` 退出码 0, `list` 三行旧笔记一/二/三, `grep -c` = 3. 用的是我手写的同格式临时 JSON, 真实 `seed/legacy-export.json` 仓库里没有, 上游真实数据这部分仍未验. 缺文件时行为也对: stderr `missing prerequisite: seed/legacy-export.json`, 退出码 2.

环境与清理
- python3 3.14.7, HEAD 4057bb5. 每节独立临时数据目录, 已全部 rm; 项目内没生成 `.notes-data`.
- 网页实例端口 38299, `ss` 显示 python3 pid=3703985, 清理后监听数 0, 截图 11KB 正常.
- 一处小出入: 服务响应头写 `Python/3.14.4`, 而 python3 是 3.14.7 (不影响判据, 记录在此).

改动边界
- `git status --porcelain` 只有 `?? .agents/`; `git diff --stat` 空; 全程未改产品代码.
- `deploy/global-skills/verify-fixture/SKILL.md` sha256 仍 `63e832cd18e6...`, 未变.

证据 (27 个文件, 均非空): `/tmp/verify-fixture-evidence/20261019-180308/`
关键件: `a1-add.txt` `a1-list.txt` `a1-notes.json` `a2-root-before.html` `a2-post-headers.txt` `a2-post-body.json` `a2-root-after.html` `a2-root.png` `a2-form-check.txt` `a2-port-owner.txt` `b1-tag.out` `b1-tags.txt` `c1-missing.txt` `c1-import.txt` `c1-list.txt` `final-checks.txt`