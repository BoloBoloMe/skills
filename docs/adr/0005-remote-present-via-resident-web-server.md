# 远程 ssh 场景的展示经常驻 web 服务交付, 完全替代本地 Chromium

后续适用范围: [workflow-stack-review milestone-14 D001-D007](../changes/workflow-stack-review/milestone-14/DECISIONS.md) 已确认宿主/容器统一经 web 服务交付局域网 URL, 删除 present 本地浏览器路径和强制状态对象, 并接受无认证无 TLS 的长期开放, 不再空闲自退. 本文下方保留旧决策原文, 不再用其中的远程分支或 24h 自退作为当前判据. 管理接口仅本机可调用的边界仍保留; 当前实现改造归 milestone-15, 尚未因本节点落盘而通过验收.

present skill 原有展示路径是在主机上起本地 Chromium 窗口; 用户经 ssh 远程开会话时该路径不可用 (浏览器起在远端屏幕上). 决策: 新增常驻 web 服务器脚本 (`general/present/scripts/web_server.py`), 远程模式下生成 HTML 后挂载进该服务并直接向用户交付 URL, 完全替代浏览器路径, 且远程模式降级为纯展示 (无 `__PRESENTATION_STATE__` 回读, 反馈与确认全在 chat).

关键取舍: 服务无认证, 无 TLS, ssh 场景默认绑定 0.0.0.0 — 用户明确接受"绑定开放时网段内可读全部挂载目录". 该取舍的两个二阶后果已显式封堵: 服务 24h 空闲自退 (防"用户走后永久暴露"), 控制端点 (`/__control__/*`) 仅 loopback (防网段内挂载篡改). 备选方案 (加认证/TLS) 被拒绝: 对临时展示工具成本不成比例, 网段信任是 ssh 场景的既有前提.
