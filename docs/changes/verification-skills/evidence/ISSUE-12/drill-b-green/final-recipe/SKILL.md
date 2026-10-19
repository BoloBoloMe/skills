---
name: verify-notes
description: 项目本地验证配方, 启动 notes-cli 并按功能驱动真实入口.
disable-model-invocation: true
---

# verify-notes

来源项目: notes-cli. 覆盖当前 PRODUCT.md 的新建笔记, 搜索笔记, 导出笔记三个功能. 归档只是搜索验证的准备手段, 不是验证对象.

## 启动

```bash
cd <项目根>
python3 app.py --version
```

期望输出 `0.3.0`, 退出码 0.

## 健康检查

```bash
python3 app.py doctor
```

期望输出包含 `notes-cli 0.3.0`, `data_path: <项目根>/data/notes.json`, `notes: <条数>`, 退出码 0. 新环境下 notes 为 0.

## 驱动

每步从干净状态开始: 先删除项目根的 `data/`, 再用 `python3 app.py` 的真实子命令, 记录命令, 退出码和输出. 注意: `add` 直接接正文, 没有 `--text` 选项; 搜索子命令是 `search`.

## 取证

把每条命令, 退出码, 原始输出和 `data/notes.json` 片段保存到本 skill 的 `evidence/<功能>.log`. 导出功能额外保留导出文件副本 `evidence/export.tsv` 和 `wc -l` 的结果.

## 清理

删除本次创建的 `data/` 目录和导出用的临时文件, 保留 `evidence/` 供复核, 不删除他人数据.

## 功能入口

- [新建笔记](features/create-note.md)
- [搜索笔记](features/search-notes.md)
- [导出笔记](features/export-notes.md)
