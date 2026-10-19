---
name: verify-notes
description: 项目本地验证配方, 按 docs/PRODUCT.md 驱动 notes-cli 的新建与搜索入口.
disable-model-invocation: true
---

# verify-notes

范围: 只覆盖当前 PRODUCT.md 的功能: 新建笔记, 搜索笔记. `features/export-notes.md` 属历史功能, 不在当前范围, 不验证.

## 启动

在项目根执行:

```bash
cd <项目根>
python3 app.py --version
```

期望输出 `0.3.0`.

## 健康检查

```bash
python3 app.py doctor
```

期望首行 `notes-cli 0.3.0`, 并输出 `data_path` 和当前笔记数.

## 驱动

用 `python3 app.py` 的真实子命令: `add`, `list`, `search`; `archive` 只作搜索验证的准备步骤. 每步记录完整命令, 退出码和输出, 失败也记录.

每个功能入口开始前先 `rm -rf data/`, 让该功能从 id 1 开始并独立取证. 连续跑多个功能时不能共用同一份 `data/`, 否则编号与期望值对不上.

## 取证

把命令输出和 `data/notes.json` 片段写入本 skill 的 `evidence/`, 文件名带时间戳. `evidence/` 已在 `.gitignore` 中.

## 清理

删除本次创建的 `data/` 目录和临时文件; 保留 `evidence/` 供复核; 不删除他人数据.

## 功能入口

- [新建笔记](features/create-note.md)
- [搜索笔记](features/search-notes.md)
