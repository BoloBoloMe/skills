# Chromium 以脱离式子进程启动, 不用 launch_persistent_context 持有

ADR-0001 选了 CDP 直连, 但首次启动浏览器的手段需钉死. 直觉做法是 `chromium.launch_persistent_context(user_data_dir, args=[--remote-debugging-port=N])`. 但这样启动的 Chromium 是 Playwright driver 的子进程, 工具进程退出时 driver 退出, Chromium 被 driver 连坐杀掉 (Windows 上 Playwright 用 job object 确保清理), CDP 端口随之消失, 跨进程共享不成立.

改为用 `subprocess.Popen` 脱离式启动 Chromium 二进制 (Windows `creationflags=DETACHED_PROCESS|CREATE_NEW_PROCESS_GROUP`, POSIX `start_new_session=True`), 传 `--user-data-dir` + `--remote-debugging-port`. Chromium 成为独立常驻进程, 不认工具进程为父; 所有进程 (含首次) 再 `connect_over_cdp`.

## 备选方案

`launch_persistent_context` + 让首个工具进程常驻 — 退化为 controller 进程, 即 ADR-0001 否定的方案.

## 后果

需自行定位 Chromium 二进制 (经 `p.chromium.executable_path` 缓存) 并管理 `--user-data-dir`, 失去 `launch_persistent_context` 的部分 launch option 便利. 代价可接受, 换来浏览器真正脱离工具进程存活.
