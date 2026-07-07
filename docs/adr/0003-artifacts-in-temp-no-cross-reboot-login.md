# 浏览器产物全部存放系统临时目录, 不保证跨重启登录态

浏览器 profile (cookies/localStorage) 与 artifacts (截图/下载/日志) 全部放在 `tempfile.gettempdir()/access-web/<sha256(cwd)[:16]>/` 下, 运行时探测, 跨平台. 不在用户 cwd 或 home 写文件.

这是一个有意的边界取舍: OS 重启或 temp 定期清理后, profile 丢失, 用户需重新登录. 我们接受这一点, 因为 skill 的持久语义是 "pi 会话内复用登录态", 不是 "跨重启免登录". 持久 profile 体积大 (Chromium profile 数百 MB), 放 home 会污染且累积; 放 temp 自洽于 session 级语义. 若将来需要跨重启保登录, 加 `--persist-profile` 选项把 profile 指向 home 缓存即可, 不影响现有架构.
