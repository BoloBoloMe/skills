# 记录板

单实例本地记录板: 状态页, report 单行, 以及向部署方提供的 relay 服务同步一次事件.

## 启动实例

```bash
mkdir -p runtime/board
python3 app.py serve --port 18201 --instance board --data-dir runtime/board &
python3 app.py health --port 18201
```

## 命令

- `python3 app.py status --port 18201`: 打印状态页 HTML.
- `python3 app.py report --port 18201`: 打印 report 单行.
- `python3 app.py sync --port 18201 --relay-port 18290`: 同步一次事件到 relay 服务.

sync 需要部署方提供的 relay 服务在 127.0.0.1:18290 监听; 该服务不在本仓库内, 本项目也不提供它的替身.

## 依赖

`vendor/relaylib.py` 是随项目提交的依赖副本, 版本记录在 `deps.txt`.

## 测试

仓库没有自动化测试, 用上面的命令自查.

`runtime/` 与 `.agents/` 在 `.gitignore` 里.
