## 父级
- `../EXECUTION.md`
## 执行
- [x] 已实现
## 要构建什么
守门脚本 `workflow/navigate/scripts/roadmap.py` 端到端可用: `uv run python workflow/navigate/scripts/roadmap.py <save|delete|query> <file> [path] [content]`. save 写指定字段, 文件不存在则自动初始化顶层结构 (schema_version "0.0.1", title, destination, notes, milestones, unknown_seas, off_course), 中间节点自动创建; content 先按 JSON 解析, 失败按裸字符串存. path 点分隔, 数字段为数组下标: 下标 == 数组长度追加, > 长度报错. query 读指定字段, 路径不存在报错指明. delete 删整个文件, 文件不存在报错. 每次 save 经 fcntl 文件锁 + 临时文件 rename 原子替换. stdout 单行 UTF-8 JSON (`{"success": true/false, ...}`), 退出码 0/1. 本 issue 校验层只保证结构可写 (合法文档能存取), 枚举/必填/环校验归 ISSUE-02.
结尾: 适合 AFK — 接口/path 语义/schema/输出契约均由 D003/D004/D005 定死, 无待决策项.
## 覆盖依据
- Product: `docs/changes/navigate-roadmap-json/PRODUCT.md`, AC-001, AC-005, AC-006, AC-007, BR-007
- Technical: `docs/changes/navigate-roadmap-json/TECHNICAL.md`, 模块接口 (守门脚本), 接缝与适配器, 测试接缝
## 相关决策
- `docs/changes/navigate-roadmap-json/DECISIONS.md`: D001, D002, D003, D004, D005, D007, D015
## 允许范围
- 新增 `workflow/navigate/scripts/roadmap.py` (含包结构所需 `__init__.py`)
- 新增 `workflow/navigate/tests/`
- `pytest.ini` 追加 testpath `workflow/navigate/tests`
## 禁止范围
- 不创建/修改 `web_server.py`, `web/`, `SKILL.md`, `TEMPLATES.md`, 其他 skill 目录
- 不实现枚举/必填/引用/环校验 (ISSUE-02)
- 不新增第三方依赖 (BR-006); 不产生任何 .md 产物 (BR-007)
## 代码定位提示
- 结构参照 `general/present/scripts/web_server.py` 顶部 docstring 约定: run_* 命令核心返回 dict 不碰 stdout, main() 薄 CLI 适配器负责 JSON 序列化与退出码
- 测试参照 `general/present/tests/` 的 subprocess 调 CLI + tmp_path 风格 (如 test_web_server_cli.py)
## TDD 切片
- TS-001:
  接缝: subprocess 调 CLI + pytest tmp_path (TECHNICAL.md 测试接缝: AC-001 -> 守门脚本 -> CLI).
  测试用例: TC-001.
  先写的失败测试: `test_save_then_query_roundtrip` — 脚本尚不存在, subprocess 报 FileNotFound.
  最小绿色实现范围: save (含新建文件初始化与中间节点创建) + query + 单行 JSON 输出契约 + 退出码.
  不得测试: 内部函数, 私有方法.
  覆盖: AC-001.
- TS-002:
  接缝: 同上.
  测试用例: TC-005.
  先写的失败测试: `test_array_index_append_and_out_of_bounds` — notes 长度 2 时写 notes.2 应追加 (长度 3), 写 notes.5 应报错且文件不变; 现无实现故失败.
  最小绿色实现范围: 点分隔路径解析, 数字段下标定位, == 长度追加, > 长度报错.
  不得测试: 解析器内部结构.
  覆盖: AC-005.
- TS-003:
  接缝: 同上.
  测试用例: TC-006.
  先写的失败测试: `test_delete_removes_file_then_query_errors` — delete 后文件不存在, 再 query 报文件不存在.
  最小绿色实现范围: delete 子命令与文件不存在错误.
  覆盖: AC-006.
- TS-004:
  接缝: 同上.
  测试用例: TC-007.
  先写的失败测试: `test_query_missing_path_errors` — query `milestones.milestone-99` 报错且错误信息含该路径.
  最小绿色实现范围: query 路径不存在错误.
  覆盖: AC-007.
- TS-005:
  接缝: 同上.
  测试用例: TC-101.
  先写的失败测试: `test_no_md_or_temp_residue` — 跑一轮 save/query/delete 后断言目录内只有目标 .json, 无 .md 文件, 无残留临时文件.
  最小绿色实现范围: 原子写临时文件清理 (rename 成功后无残留).
  不得测试: 未确认用例.
  覆盖: BR-007.
## 验证入口
- `uv run pytest workflow/navigate/tests/ -q` 全绿
- 手跑 `uv run python workflow/navigate/scripts/roadmap.py save /tmp/x.json title 测试 && uv run python workflow/navigate/scripts/roadmap.py query /tmp/x.json title`, 确认输出单行 JSON 且 success true
## 风险提示
- 路径解析边界: 里程碑 id 形如 milestone-01 非纯数字, 数字段仅作数组下标 (D004); 注意 `notes.2` 与 `milestones.milestone-01` 两类定位的区分
- 并发写撕裂: fcntl 锁范围须覆盖 读-改-写 全程, 不只写瞬间
## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.
## 适合 AFK 的原因
接口, path 语义, schema, 输出契约, 参照文件均已定死, 实现无产品/API/架构决策点.
## 验收标准
- [ ] AC-001: 合法写入可经 query 读回, stdout 单行 JSON, 退出码正确
- [ ] AC-005: notes.2 追加成功, notes.5 越界报错且文件不变
- [ ] AC-006: delete 后文件消失, 再 query 报文件不存在
- [ ] AC-007: query 不存在路径报错且指明路径
- [ ] BR-007: 测试断言无 .md 产生, 无临时文件残留
- [ ] `uv run pytest workflow/navigate/tests/ -q` 全绿
## 被阻塞于
- 无
