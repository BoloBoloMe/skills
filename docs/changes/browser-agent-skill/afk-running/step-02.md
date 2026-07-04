# 步骤 02: diff 门禁

检查 worker 产出的 diff:

- git diff 非空
- 未越过当前 issue 允许范围
- 未触碰当前 issue 禁止范围
- 无 staged 文件 / 未知来源变更
- 当前 issue 产物目录下 worker-note-aN.md 存在且完整

---

diff 非空且通过 → _current.md 写为 :03
diff 为空 → _current.md 写为 :01 (重新启动 worker)
越过范围/未知变更 → 停止并报告
