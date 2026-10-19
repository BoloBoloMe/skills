---
name: verify-notes
description: 项目本地验证配方, 启动 notes-cli 并按功能驱动真实入口.
disable-model-invocation: true
---

# verify-notes

来源项目: notes-cli. 本配方只覆盖 `docs/PRODUCT.md` 当前确认的功能: 新建笔记, 搜索笔记.
产品是否通过以 `docs/PRODUCT.md` 为准, 配方和代码现状不能另立标准或弱化要求.
导出, 归档属于历史功能, 不在本配方范围; 归档只作为搜索功能的准备步骤使用.

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

期望输出首行为 `notes-cli 0.3.0`, 并含 `data_path` 与 `notes`.

## 驱动

用 `python3 app.py` 的真实子命令, 参数按 `app.py` 现状给全.
每步记录命令与输出. 配方失败时先分三类: 文档漂移 (本配方写错, 改配方), 驱动缺口 (入口/参数不存在, 改配方), 产品缺陷 (配方符合 PRODUCT.md 但产品不符, 单独报告, 不改产品代码也不改配方掩盖).

## 取证

命令输出与 `data/notes.json` 片段, 存到本 skill 的 `evidence/` 下.

## 清理

删除本次创建的 `data/` 目录和 `evidence/` 临时文件, 不删除他人数据.
失败迭代的残留同样清理, 但保留报告所需的取证.

## 功能入口

- [新建笔记](features/create-note.md)
- [搜索笔记](features/search-notes.md)
