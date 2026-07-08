# 演示任务: Hacker News 热帖调查与数据交叉验证

## 目标

使用 `access-web` skill 完成 Hacker News (HN) 热门帖子调查, 提取结构化数据, 用 API 交叉验证, 采集浏览器运行时指标. 本任务覆盖 skill 的全部能力层: 只读抓取, L1 语义化操作, L2 escape hatch, L3 裸 CDP, 生命周期管理.

## 前置

- 已安装 `access-web` skill, 代码在 `general/access-web/` 下.
- 已执行 `python -m playwright install chromium`.
- Python 环境可运行 `general/access-web/browse/` 下的代码.
- 无需登录, 全程 headless.

## 步骤

### 第 1 步: 只读抓取 — 搜索 Hacker News

用 `scrape` 子命令搜索 "Hacker News top stories", 获取搜索结果摘要. 目的: 展示只读抓取模式.

```bash
cd general/access-web
python scrape/scripts/scrape.py search "Hacker News top stories" -n 5
```

记录: 搜索结果中是否包含 `news.ycombinator.com` 链接.

### 第 2 步: 只读抓取 — 提取 HN 首页正文

用 `scrape` 子命令提取 HN 首页正文. 目的: 展示只读抓取对 JS 渲染页面的局限性 (HN 首页是 server-rendered, 应该能提取).

```bash
python scrape/scripts/scrape.py browse https://news.ycombinator.com --mode extract
```

记录: `extraction.confidence`, `extraction.warnings`, 提取到的文本是否包含帖子标题.

### 第 3 步: 交互浏览 — 导航到 HN 首页 (L1)

用 `navigate` 打开 HN 首页. 目的: 启动脱离式 Chromium, 建立 CDP 会话.

```python
from browser_agent import navigate, status

result = navigate("https://news.ycombinator.com")
print(f"navigate success={result.success}, url={result.url}")

st = status()
print(f"alive={st.alive}, pid={st.pid}, cdp_port={st.cdp_port}, pages={st.pages}")
```

记录: `navigate` 成功, `status` 显示浏览器存活, pid 和 cdp_port 非空.

### 第 4 步: 页面结构 — 获取 DOM 结构 (L1)

用 `get_page_structure` 获取页面结构. 目的: 展示语义化页面结构提取.

```python
from browser_agent import get_page_structure

struct = get_page_structure(max_elements=100)
print(f"success={struct.success}, elements={len(struct.data) if struct.data else 0}")
```

记录: 结构中是否包含帖子列表的 role/name 信息.

### 第 5 步: 数据提取 — 用 evaluate_js 提取热帖 (L2)

用 `evaluate_js` 在页面上执行 JS, 提取前 5 条帖子的标题/分数/评论数/链接. 目的: 展示 L2 escape hatch 对 SPA/动态页面的数据提取能力.

```python
from browser_agent import evaluate_js

js = """
(() => {
  const rows = document.querySelectorAll('.athing');
  const posts = [];
  for (let i = 0; i < Math.min(5, rows.length); i++) {
    const row = rows[i];
    const titleEl = row.querySelector('.titleline > a');
    const subtext = row.nextElementSibling?.querySelector('.subtext');
    const score = subtext?.querySelector('.score')?.textContent || '0 points';
    const comments = subtext?.querySelectorAll('a')?.[subtext.querySelectorAll('a').length - 1]?.textContent || '0 comments';
    posts.push({
      rank: i + 1,
      title: titleEl?.textContent || '',
      url: titleEl?.href || '',
      score: score,
      comments: comments
    });
  }
  return posts;
})()
"""

result = evaluate_js(js)
print(f"success={result.success}")
if result.result:
    for post in result.result:
        print(f"  #{post['rank']} [{post['score']}] {post['title']} ({post['comments']})")
```

记录: 5 条帖子的标题/分数/评论数. 保存到 `access-web-demo-task-report/posts_from_dom.json` (需在保存前 `os.makedirs("access-web-demo-task-report", exist_ok=True)`).

### 第 6 步: 交叉验证 — 用 network_json 调用 HN API (L2)

用 `network_json` 调用 HN 官方 Firebase API 获取热帖, 与 DOM 提取结果对比. 目的: 展示 `network_json` 携带浏览器 cookie 发 HTTP 请求, 绕过 CORS.

```python
from browser_agent import network_json
import json

# HN API: top stories
result = network_json("https://hacker-news.firebaseio.com/v0/topstories.json")
print(f"success={result.success}, status={result.status}")

if result.success:
    top_ids = json.loads(result.body)[:5]
    api_posts = []
    for story_id in top_ids:
        r = network_json(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
        if r.success:
            item = json.loads(r.body)
            api_posts.append({
                "title": item.get("title", ""),
                "score": f"{item.get('score', 0)} points",
                "comments": f"{item.get('descendants', 0)} comments",
                "url": item.get("url", "")
            })
            print(f"  API: [{item.get('score', 0)} points] {item.get('title', '')}")

    # 保存 API 结果
    import os; os.makedirs("access-web-demo-task-report", exist_ok=True)
    with open("access-web-demo-task-report/posts_from_api.json", "w") as f:
        json.dump(api_posts, f, indent=2)
```

记录: API 返回的 5 条帖子. 对比 DOM 和 API 结果的标题是否大致一致 (顺序可能不同, 但热门帖子应高度重叠).

### 第 7 步: 裸 CDP — 获取浏览器性能指标 (L3)

用 `cdp_send` 发送 CDP 命令获取性能指标. 目的: 展示 L3 裸 CDP 对 browser 级操作的访问能力.

```python
from browser_agent import cdp_send

# 获取性能指标
perf = cdp_send("Performance.getMetrics")
print(f"success={perf.success}")
if perf.result:
    for metric in perf.result.get("metrics", []):
        print(f"  {metric['name']}: {metric['value']}")

# 获取当前页面导航历史
nav = cdp_send("Page.getNavigationHistory")
print(f"nav success={nav.success}")
if nav.result:
    entries = nav.result.get("entries", [])
    for e in entries:
        print(f"  nav: {e.get('title', '')} -> {e.get('url', '')}")
```

记录: 性能指标 (JSHeapUsedSize, Nodes, LayoutCount 等), 导航历史.

### 第 8 步: 截图 — 保存 HN 首页截图 (L1)

```python
from browser_agent import screenshot

result = screenshot(path="access-web-demo-task-report/hn_screenshot.png", full_page=False)
print(f"success={result.success}, path={result.path}")
```

记录: 截图文件是否生成.

### 第 9 步: Cookie 与会话状态

```python
from browser_agent import cookies, status

ck = cookies()
print(f"cookies success={ck.success}, count={len(ck.cookies) if ck.cookies else 0}")
if ck.cookies:
    for c in ck.cookies[:3]:
        print(f"  {c['name']}={c['value'][:20]}... (domain={c['domain']})")

st = status()
print(f"\nFinal status:")
print(f"  alive={st.alive}")
print(f"  url={st.url}")
print(f"  title={st.title}")
print(f"  pid={st.pid}")
print(f"  headed={st.headed}")
print(f"  cdp_port={st.cdp_port}")
print(f"  profile_dir={st.profile_dir}")
print(f"  pages={st.pages}")
```

记录: cookie 列表, 最终会话状态.

### 第 10 步: 会话持久性验证 — 跨进程复用

在第一个 Python 进程中完成上述步骤后, **启动一个新的 Python 进程**, 在同一 cwd 下调用 `navigate`. 目的: 验证脱离式 Chromium 跨进程复用.

```python
# 新进程中的代码
from browser_agent import navigate, status

# 不应重新启动 Chromium, 应复用已有会话
result = navigate("https://news.ycombinator.com")
st = status()
print(f"Cross-process: alive={st.alive}, pid={st.pid}")
print(f"Browser reused: {st.alive}")
```

记录: 新进程连接到同一 Chromium (相同 pid), 无需重新启动浏览器.

### 第 11 步: 生命周期管理 — stop + 重连

```python
from browser_agent import stop_browser_session, status, navigate

# stop: 杀 Chromium, 保留 profile
stop_browser_session()
st = status()
print(f"After stop: alive={st.alive}")  # 应为 False

# 重新 navigate: 应自愈重 launch, 登录态保留
result = navigate("https://news.ycombinator.com")
st = status()
print(f"After relaunch: alive={st.alive}, pid={st.pid}")  # 应为 True, 新 pid
```

记录: stop 后 alive=False, 重新 navigate 后 alive=True 且 pid 不同.

### 第 12 步: 清理

```python
from browser_agent import cleanup_browser_session, status

cleanup_browser_session()
st = status()
print(f"After cleanup: alive={st.alive}")  # 应为 False
```

记录: cleanup 后浏览器死亡, session 目录已删除.

## 预期产物

所有产物写入项目根目录下的 `access-web-demo-task-report/` 目录:

| 文件 | 内容 |
|------|------|
| `access-web-demo-task-report/posts_from_dom.json` | 从 DOM 提取的 5 条热帖 (标题/分数/评论数/链接) |
| `access-web-demo-task-report/posts_from_api.json` | 从 HN API 获取的 5 条热帖 |
| `access-web-demo-task-report/hn_screenshot.png` | HN 首页截图 |
| `access-web-demo-task-report/demo-report.md` | 汇总报告: 各步结果, DOM vs API 对比, 性能指标, 会话状态 |

## 验证清单

- [ ] scrape search 返回搜索结果
- [ ] scrape browse 提取 HN 首页正文
- [ ] navigate 成功, status 显示 alive=True
- [ ] get_page_structure 返回页面结构
- [ ] evaluate_js 提取 5 条帖子结构化数据
- [ ] network_json 调用 HN API 成功, 返回 JSON
- [ ] DOM 与 API 结果标题大致一致
- [ ] cdp_send 返回性能指标和导航历史
- [ ] screenshot 生成 PNG 文件
- [ ] cookies 返回当前 context cookie
- [ ] 跨进程 navigate 复用同一 Chromium (相同 pid)
- [ ] stop 后 alive=False, 重 navigate 后 alive=True (新 pid)
- [ ] cleanup 后 alive=False, session 目录删除

## 注意

- 全程 headless, 不需要人工干预.
- HN 首页是 server-rendered, scrape 和 browse 都能提取, 但 browse 的 evaluate_js 能提取更精确的结构化数据.
- HN Firebase API 是公开 API, 无需认证, 但 network_json 会自动携带浏览器 context cookie.
- 跨进程复用验证 (第 10 步) 需要在同一 cwd 下运行新 Python 进程, session-key 基于 cwd 计算.
- 所有操作失败时返回 `success=False`, 不抛异常, 检查 `.error` 字段获取原因.
