## 父级
- `../EXECUTION.md`
## 执行
- [ ] 已实现
## 要构建什么
在 ISSUE-03 服务骨架上补 HTTP 端点与空闲自退:
`GET /` 与 `GET /index.html` 返回 `workflow/navigate/web/index.html` 内容 (本 issue 先落地最小占位页, ISSUE-05 重写为完整 SPA);
`GET /api/roadmap?path=<绝对路径>` 仅当路径以 `.json` 结尾且文件存在时返回其 JSON 内容, 否则返回错误响应 (页面据此渲染友好提示);
空闲自退: 最后一次请求后 24h 无新请求则进程退出并清理运行时文件, 空闲阈值经环境变量可缩短 (测试用).
结尾: 适合 AFK — 端点规则与安全边界由 D009/D011 定死, 空闲自退验证口径在 TECHNICAL.md 非功能要求中给定.
## 覆盖依据
- Product: `docs/changes/navigate-roadmap-json/PRODUCT.md`, AC-011, AC-015 (数据侧), AC-016
- Technical: `docs/changes/navigate-roadmap-json/TECHNICAL.md`, 模块接口 (展示服务 HTTP 端点), 安全策略, 非功能要求 (空闲自退), 测试接缝
## 相关决策
- `docs/changes/navigate-roadmap-json/DECISIONS.md`: D009, D010, D011, D015, D016
## 允许范围
- `workflow/navigate/scripts/web_server.py`
- 新增 `workflow/navigate/web/index.html` (最小占位页)
- `workflow/navigate/tests/`
## 禁止范围
- 不动 `roadmap.py`, `SKILL.md`, `TEMPLATES.md`, 其他 skill 目录
- 不实现完整 SPA (ISSUE-05/06); 不做旧格式迁移 (NG-001); 不引入认证 (NG-002); 不新增第三方依赖
## 代码定位提示
- 端点实现参照 `general/present/scripts/web_server.py` 的 BaseHTTPRequestHandler 用法; 空闲自退参照其空闲计时与自退机制
- 测试: 起真实实例绑 loopback, `urllib.request` 发真实请求 (对齐 present tests 先例)
## TDD 切片
- TS-001:
  接缝: loopback 真实 HTTP 请求 (TECHNICAL.md 测试接缝).
  测试用例: TC-016.
  先写的失败测试: `test_api_roadmap_rejects_non_json_and_missing` — 请求 `/etc/passwd` 被拒不返回内容; 请求不存在的 `x.json` 得错误响应.
  最小绿色实现范围: .json 后缀检查 + 文件存在性检查 + 错误响应.
  不得测试: 未确认的路径穿越变体.
  覆盖: AC-016.
- TS-002:
  接缝: 同上.
  测试用例: TC-015.
  先写的失败测试: `test_api_roadmap_error_shape_for_frontend` — 不存在路径返回结构化错误 (非 2xx 或 JSON error), 供前端渲染提示页.
  最小绿色实现范围: 错误响应的确定形态.
  覆盖: AC-015 (数据侧).
- TS-003:
  接缝: 环境变量覆盖运行时目录 + 真实实例.
  测试用例: TC-011.
  先写的失败测试: `test_idle_exit_after_shortened_threshold` — 空闲阈值缩到秒级, 起服务后不请求, 断言进程退出且运行时文件清理; 请求一次则计时重置.
  最小绿色实现范围: 最后请求时间戳 + 后台检查线程/定时器触发退出.
  不得测试: 计时器内部实现.
  覆盖: AC-011.
- TS-004:
  接缝: loopback 真实 HTTP 请求.
  测试用例: TC-008 扩展.
  先写的失败测试: `test_index_served` — `GET /` 与 `/index.html` 返回 200 text/html, 内容即 web/index.html.
  最小绿色实现范围: 静态文件端点 + 占位页文件.
  不得测试: 占位页内容细节.
  覆盖: AC-011 (伴随端点).
## 验证入口
- `uv run pytest workflow/navigate/tests/ -q` 全绿
- 手跑 start 后 `curl '<url>/api/roadmap?path=/etc/passwd'` 得拒绝, 指向存在的 .json 得内容
## 风险提示
- 空闲自退的 "最后请求" 须覆盖所有端点 (含被判活的请求), 否则服务可能在被使用中自退
- .json 检查要在任何文件读取之前, 避免以后缀之外的路径形态探测文件系统
## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止.
## 适合 AFK 的原因
端点放行规则, 错误形态, 自退口径均先定死, 无待决策项.
## 验收标准
- [ ] AC-016: 非 .json 路径与不存在文件均被拒, 不返回文件内容
- [ ] AC-015 数据侧: 不存在路线图返回结构化错误
- [ ] AC-011: 缩短阈值下空闲自退生效, 运行时文件清理
- [ ] GET / 返回占位页 200 text/html
- [ ] `uv run pytest workflow/navigate/tests/ -q` 全绿
## 被阻塞于
- `ISSUE-03-web-server-lifecycle.md`
