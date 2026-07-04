# 步骤 05: 修复 diff 门禁

检查修复 worker 产出的 diff:

- git diff 非空
- 未越过当前 issue 允许范围
- 未触碰当前 issue 禁止范围
- 无 staged 文件
- 当前 issue 产物目录下 fix-note-aN.md 存在且完整

---

diff 非空且通过 → _current.md 写为 :03 (重新进入 review)
diff 为空 → _current.md 写为 :04 (重新启动修复 worker)
越过范围/未知变更 → 停止并报告
