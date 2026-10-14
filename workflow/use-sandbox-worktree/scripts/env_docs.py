"""容器环境事实文档生成器 (ISSUE-02).

纯函数: 由 birth (容器 create) 前可知的容器事实渲染生成节与四份 ~/docs/ 小抄.
无 IO, 无子进程, 无网络, 无 llm 调用; 同 facts 同字节.
"""
from __future__ import annotations

# 生成标记: birth 收尾验收 (D018) 用它判断挂载物确实是脚本生成.
BIRTH_MARKER = "birth 生成"
# 生成文档集合固定为四份 (D012).
DOC_FILES = ("identity.md", "network.md", "web-ports.md", "agents.md")

_UNCONFIRMED = "未确认"
_UNREGISTERED = "未登记"
# default_models 整键缺席时, 三个 agent 的模型均按缺席文案渲染 (D012).
_DEFAULT_AGENTS = ("pi", "codex", "kimi")


def _identity(facts) -> str:
    return "\n".join((
        f"# 容器身份 ({BIRTH_MARKER})",
        f"- 容器名: {facts.get('container', _UNREGISTERED)}",
        f"- 主仓路径 (宿主): {facts.get('repo_path', _UNREGISTERED)}",
        f"- 母体目录: {facts.get('mother_dir', _UNREGISTERED)}",
        f"- 分支: {facts.get('branch', _UNREGISTERED)}",
        f"- 容器内代码路径: {facts.get('code_path', _UNREGISTERED)}",
        "",
    ))


def _network(facts) -> str:
    mode = facts.get("mode")
    if mode not in ("whitelist", "blacklist"):
        mode = _UNREGISTERED
    lines = [
        f"# 网络管控 ({BIRTH_MARKER})",
        "birth 快照, deny 清单可能运行期变化, 以实际连通性为准.",
        f"- 模式: {mode}",
    ]
    deny = list(facts.get("deny") or [])
    if deny:
        lines.append("- deny 条目 (IP 级全端口):")
        lines.extend(f"  - {entry}" for entry in deny)
    lines.append("")
    return "\n".join(lines)


def _web_ports(facts) -> str:
    lan_ip = facts.get("lan_ip") or _UNCONFIRMED
    return "\n".join((
        f"# 展示页 ({BIRTH_MARKER})",
        f"- 已确认局域网地址: {lan_ip}",
        "- 宿主端口映射: 容器内 8800-8805 对应宿主环境变量 "
        "SWT_HOST_WEB_PORT, SWT_HOST_WEB_PORT_2.._6; create 后才知, "
        "从 env 读取, 缺席时经信箱向宿主会话索取.",
        "",
        "## 架桥配方 (navigate 交付展示页)",
        "容器里交付地图页时, 8801 固定归 navigate (8800 固定归 present); "
        "不挑'第一个空口', 两次探测间会撞车, 残留桥也会占口.",
        "1. 起服务: `web_server.py start` 拿 stdout 的 `url`, "
        "从中读出实际监听端口 P (navigate 自带服务端口不固定).",
        "2. 架桥: 接桥前先清容器 8801 上的残留死桥, 再用 socat 把 8801 桥到 P "
        "(`socat TCP-LISTEN:8801,fork,reuseaddr TCP:127.0.0.1:<P>`); "
        "桥随服务同生死 — 服务停即清桥.",
        "3. 拼 URL 交付: 主机取已确认局域网地址 SWT_HOST_LAN_IP, "
        "端口取 SWT_HOST_WEB_PORT_2 (对应容器 8801), 拼 "
        "`http://<SWT_HOST_LAN_IP>:<SWT_HOST_WEB_PORT_2>/?roadmap=<ROADMAP.json 绝对路径>`.",
        "4. 降级: 端口变量缺席 (旧容器/尚未确认) 或注入失败时保持软失败, "
        "交付包显式打一行 'web 端口未注入, 页面需走信箱协商', "
        "并发信箱向宿主会话索取网址.",
        "不改 web_server.py: 容器侧只加 socat 桥, 代码不动.",
        "",
    ))


def _agents(facts) -> str:
    lines = [
        f"# agent 配置 ({BIRTH_MARKER})",
        f"- 模板: {facts.get('template_name', _UNREGISTERED)} {facts.get('template_version', _UNREGISTERED)}",
        f"- 快照摘要: {facts.get('snapshot_digest', _UNREGISTERED)}",
        "- 默认模型:",
    ]
    models = facts.get("default_models")
    if models is None:
        for agent in _DEFAULT_AGENTS:
            lines.append(f"  - {agent}: {_UNREGISTERED}")
    else:
        for agent, model in models.items():
            lines.append(f"  - {agent}: {model}")
    lines.append("")
    return "\n".join(lines)


def render_docs(facts) -> dict:
    """由容器事实渲染四份 ~/docs/ 小抄文本, 键为文件名."""
    return {
        "identity.md": _identity(facts),
        "network.md": _network(facts),
        "web-ports.md": _web_ports(facts),
        "agents.md": _agents(facts),
    }


def render_generation_section(facts) -> str:
    """生成节 (D009 定稿 4 行触发式指针), 拼在 ENV.md 之后, 三份提示词相同."""
    return "\n".join((
        f"## 本容器事实 ({BIRTH_MARKER})",
        "- 网络访问不通/要判断某地址可连性 → 读 ~/docs/network.md (当前模式与 deny 条目)",
        "- 要自证/填报容器身份 (容器名/主仓/分支/代码路径) → 读 ~/docs/identity.md",
        "- 要拼给用户的展示页 URL / 在容器内交付展示页 (起服务/架桥) → "
        "读 ~/docs/web-ports.md (已确认局域网地址与架桥配方)",
        "- 要改 pi/codex/kimi 配置或换模型 → 读 ~/docs/agents.md (模板与默认模型)",
        "",
    ))
