---
name: verify-notes
description: 项目本地验证配方, 启动 notes-cli 并按功能驱动真实入口.
disable-model-invocation: true
---

# verify-notes

来源项目: notes-cli 的旧配方, 覆盖多个历史功能.

## 启动

```bash
cd <项目根>
python3 app.py --version
```

期望输出 `0.3.0`.

## 健康检查

```bash
python3 app.py doctor
```

期望输出首行为 `notes-cli 0.2.0`.

## 驱动

用 `python3 app.py` 的真实子命令. 每步记录命令与输出.

## 取证

命令输出与 `data/notes.json` 片段, 存到本 skill 的 `evidence/` 下.

## 清理

删除本次创建的 `data/` 目录和 `evidence/` 临时文件, 不删除他人数据.

## 功能入口

- [新建笔记](features/create-note.md)
- [搜索笔记](features/search-notes.md)
