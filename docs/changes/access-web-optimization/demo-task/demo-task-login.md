# 演示任务: GitHub 登录态保持与认证数据提取

## 目标

使用 `access-web` skill 的**交互浏览**模式, 在 headed 模式下由人类完成 GitHub 登录, 之后跨工具进程复用登录态, 提取仅认证可见的数据, 并用 `network_json` 携带 cookie 调用 GitHub API. 本任务展示日常最常见的场景: 一次登录, 后续自动化.

## 前置

- 已安装 `access-web` skill, 代码在 `general/access-web/` 下.
- 已执行 `python -m playwright install chromium`.
- 有 GitHub 账号, 可在浏览器中手动登录.
- 本任务分两阶段: **阶段 A** 需要你在屏幕前操作登录; **阶段 B** 全自动, 验证登录态保持.

## 关键概念

普通浏览器自动化工具在脚本退出后浏览器即关闭, 下次需要重新登录. 本 skill 用脱离式 Chromium + CDP, 工具进程退出后浏览器仍存活, 登录态保留在 profile 中. 下次调用自动连接同一浏览器, 无需重新登录.

本任务验证这一核心能力.

---

## 阶段 A: 人工登录 (需要你介入)

### 第 1 步: 启动 headed 浏览器, 导航到 GitHub 登录页

设置环境变量 `BROWSER_HEADED=true`, 用 `navigate` 打开 GitHub. Chromium 窗口会出现在屏幕上.

```python
import os
os.environ["BROWSER_HEADED"] = "true"

from browser_agent import navigate, status, screenshot

result = navigate("https://github.com/login")
print(f"navigate success={result.success}, url={result.url}")

st = status()
print(f"Browser started: pid={st.pid}, headed={st.headed}, cdp_port={st.cdp_port}")
```

### 第 2 步: 等待你完成登录

**现在请在弹出的 Chromium 窗口中手动操作:**
1. 输入 GitHub 用户名和密码.
2. 如有 2FA/MFA, 完成验证.
3. 等待登录成功, 页面跳转到 GitHub 首页或 dashboard.

脚本侧用 `wait_for_element` 轮询等待登录完成标志 (如头像菜单或首页 feed):

```python
from browser_agent import wait_for_element, extract_text, screenshot

# 等待登录后出现的元素 (GitHub 左上角 logo 或用户头像)
# 登录成功后 GitHub 会跳转到 https://github.com/ 或 dashboard
print("等待登录完成... (请在浏览器窗口中操作)")

# 轮询等待: 检测页面 URL 不再是 /login
import time
from browser_agent import status

for _ in range(60):  # 最多等 5 分钟
    time.sleep(5)
    st = status()
    if st.alive and "/login" not in (st.url or ""):
        print(f"登录成功! 当前页面: {st.title} ({st.url})")
        break
else:
    print("超时, 未检测到登录完成")

# 截图记录登录后状态
screenshot(path="access-web-demo-task-report/after_login.png")
```

### 第 3 步: 验证登录态 — 提取认证后可见内容

登录后, GitHub 导航栏右上角应显示用户头像, 首页应显示个性化 feed. 用 `evaluate_js` 提取这些仅认证可见的信息:

```python
from browser_agent import evaluate_js

# 提取登录用户名 (从页面元素)
js = """
(() => {
  // 方法1: 从 meta 标签
  const meta = document.querySelector('meta[name="user-login"]');
  if (meta) return { login: meta.content, source: 'meta' };

  // 方法2: 从头像 alt 属性
  const avatar = document.querySelector('img.avatar');
  if (avatar && avatar.alt) return { login: avatar.alt, source: 'avatar' };

  // 方法3: 从 JS 全局变量
  if (window.__INITIAL_STATE__?.user) {
    return { login: window.__INITIAL_STATE__.user.login, source: 'global' };
  }

  return { login: null, source: 'not_found' };
})()
"""

result = evaluate_js(js)
print(f"登录用户: {result.result}")
```

记录: 登录用户名. 如果能提取到, 说明登录成功且会话有效.

### 第 4 步: 用 network_json 调用 GitHub API (携带 cookie)

用 `network_json` 调用 GitHub 的认证 API (如 notifications), 浏览器 context 的 cookie 会自动携带, 无需单独配置 token:

```python
from browser_agent import network_json
import json

# 获取通知 (需要认证)
result = network_json("https://api.github.com/notifications", method="GET")
print(f"API status: {result.status}")

if result.status == 200:
    notifications = json.loads(result.body)
    print(f"未读通知数: {len(notifications)}")
    for n in notifications[:5]:
        print(f"  - {n['subject']['title']} ({n['repository']['full_name']})")
elif result.status == 401:
    print("未认证 (cookie 未携带或已过期)")
else:
    print(f"API 返回 {result.status}: {result.body[:200]}")
```

记录: API 返回 200 说明 cookie 有效, `network_json` 成功携带认证信息.

### 第 5 步: 提取 GitHub 首页 feed (仅认证可见)

```python
from browser_agent import navigate, evaluate_js

navigate("https://github.com/")

js = """
(() => {
  // 提取 feed 中的仓库推荐/动态
  const items = document.querySelectorAll('[data-testid="feed-item"], .feed-item, article');
  const feed = [];
  for (const item of items) {
    const text = item.textContent?.trim().slice(0, 100);
    if (text) feed.push(text);
  }
  return { count: feed.length, items: feed.slice(0, 5) };
})()
"""

result = evaluate_js(js)
print(f"Feed items: {result.result}")
```

### 第 6 步: 保存会话状态, 退出脚本

脚本退出前, 确认浏览器仍在运行. **不调用 stop/cleanup**, 让 Chromium 继续存活:

```python
from browser_agent import status

st = status()
print(f"脚本退出前状态: alive={st.alive}, pid={st.pid}")
print(f"Profile: {st.profile_dir}")
print("脚本将退出, Chromium 继续在后台运行.")
print("=> 阶段 A 完成. 请运行阶段 B 验证登录态保持.")
```

**此时脚本退出, 但 Chromium 进程仍然存活, 登录态保留在 profile 中.**

---

## 阶段 B: 自动复用登录态 (无需介入)

在**新的 Python 进程**中运行 (模拟新的工具调用). 不设置 `BROWSER_HEADED`, 用 headless 模式. 关键验证: 不需要重新登录.

### 第 7 步: 新进程连接已有会话

```python
# 新进程, 不设 BROWSER_HEADED (headless)
from browser_agent import navigate, status

# 连接到阶段 A 启动的 Chromium (同一 cwd, 同一 session-key)
result = navigate("https://github.com/")
st = status()
print(f"新进程连接: alive={st.alive}, pid={st.pid}")
print(f"URL: {st.url}, Title: {st.title}")
```

记录: `pid` 应与阶段 A 的 pid **相同** (复用同一 Chromium), 不是新启动的.

### 第 8 步: 验证仍然处于登录态

```python
from browser_agent import evaluate_js

# 再次提取登录用户名
js = """
(() => {
  const meta = document.querySelector('meta[name="user-login"]');
  return meta ? meta.content : null;
})()
"""

result = evaluate_js(js)
print(f"仍登录为: {result.result}")
print("登录态保持!" if result.result else "登录态丢失!")
```

记录: 仍能提取到用户名, 说明登录态跨进程保持.

### 第 9 步: 用 cookie 调用认证 API

```python
from browser_agent import network_json
import json

# 获取用户的仓库列表 (认证 API)
result = network_json("https://api.github.com/user/repos?sort=updated&per_page=5")
print(f"API status: {result.status}")

if result.status == 200:
    repos = json.loads(result.body)
    print(f"最近更新的仓库:")
    for repo in repos:
        print(f"  - {repo['full_name']} ({'private' if repo['private'] else 'public'}, {repo.get('language', '?')})")
```

记录: 能获取私有仓库列表, 说明 cookie 认证有效.

### 第 10 步: 查看会话 cookie

```python
from browser_agent import cookies

ck = cookies()
print(f"Cookie 数量: {len(ck.cookies) if ck.cookies else 0}")
if ck.cookies:
    # 找 GitHub 认证相关 cookie
    auth_cookies = [c for c in ck.cookies if 'github' in c.get('domain', '')]
    print(f"GitHub cookie: {len(auth_cookies)}")
    for c in auth_cookies[:5]:
        print(f"  {c['name']}: {c['value'][:15]}... (domain={c['domain']}, httpOnly={c.get('httpOnly')})")
```

### 第 11 步: stop — 关浏览器但保留登录态

```python
from browser_agent import stop_browser_session, status

stop_browser_session()
st = status()
print(f"After stop: alive={st.alive}")  # False, 浏览器关闭
print("Profile 保留, 登录态仍在.")
```

### 第 12 步: 重连 — 验证 stop 后仍免登录

```python
from browser_agent import navigate, status, evaluate_js

# 重新 navigate, 应自愈重 launch, 用保留的 profile, 仍免登录
result = navigate("https://github.com/")
st = status()
print(f"重连: alive={st.alive}, pid={st.pid}")  # 新 pid, 但登录态在

# 验证仍登录
js = "document.querySelector('meta[name=\"user-login\"]')?.content || null"
r = evaluate_js(js)
print(f"重连后仍登录为: {r.result}")
```

记录: 新 pid (重新启动了 Chromium), 但仍处于登录态 (profile 保留).

### 第 13 步: cleanup — 彻底清理

```python
from browser_agent import cleanup_browser_session, status

cleanup_browser_session()
st = status()
print(f"After cleanup: alive={st.alive}")  # False
print("Session 目录已删除, 登录态彻底清除.")
print("下次调用需要重新登录.")
```

---

## 预期产物

所有产物写入项目根目录下的 `access-web-demo-task-report/` 目录:

| 文件 | 内容 |
|------|------|
| `access-web-demo-task-report/after_login.png` | 登录后 GitHub 首页截图 |
| `access-web-demo-task-report/github_session_report.md` | 汇总报告 |

## 验证清单

### 阶段 A (人工登录)
- [ ] headed Chromium 窗口弹出, 显示 GitHub 登录页
- [ ] 手动登录成功, 脚本检测到页面跳转
- [ ] `evaluate_js` 提取到登录用户名
- [ ] `network_json` 调用 GitHub API 返回 200 (cookie 认证有效)
- [ ] 首页 feed 提取到个性化内容
- [ ] 脚本退出后 Chromium 仍存活 (任务管理器可见)

### 阶段 B (自动复用)
- [ ] 新进程 `navigate` 连接到同一 Chromium (相同 pid)
- [ ] 仍能提取登录用户名 (登录态保持)
- [ ] `network_json` 获取私有仓库列表成功
- [ ] cookie 列表包含 GitHub 认证 cookie
- [ ] `stop` 后 alive=False, profile 保留
- [ ] 重连后新 pid 但仍免登录
- [ ] `cleanup` 后 alive=False, session 目录删除

## 注意

- **阶段 A 必须在能看到屏幕的环境运行** (本地桌面, 非 SSH/无头服务器).
- 阶段 A 和阶段 B 必须在**同一 cwd** 下运行, session-key 基于 cwd 计算.
- 阶段 A 退出后不要手动关 Chromium 窗口, 让它后台存活.
- 如果 Chromium 被 OS 或用户误杀, 阶段 B 的 `navigate` 会自愈重 launch, 但登录态依赖 profile 是否完好.
- `network_json` 携带的是浏览器 context cookie, 不是 GitHub Personal Access Token. 适合临时自动化, 不适合长期 CI (cookie 会过期).
- GitHub 可能要求 2FA, 请在 headed 窗口中正常完成.
- 如果不想用 GitHub, 可替换为任何需要登录的网站 (Gitea, GitLab, 内部系统等), 调整 JS 选择器即可.
