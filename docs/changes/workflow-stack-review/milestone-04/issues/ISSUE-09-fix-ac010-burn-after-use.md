## 父级
- `../EXECUTION.md`
## 执行
- [x] 已完成
## 来由
第三轮独立核验 (VERIFY-03) 仍判 AC-010 失败: `workflow/demo/SKILL.md:31` 通用规则 3 里"若问题涉及持久化, 用本地文件, 取醒目名字, 用后即焚"给持久化演示文件立了"用后即删"的义务, 与 AC-010 要求的"三处都没有用完即删的义务"直接冲突. 这句在基线就存在, 早先几轮的 grep 用的是"用完即焚", 没有命中"用后即焚"这个变体, 所以一直没被发现.

## 要交付什么
只改 `workflow/demo/SKILL.md` 通用规则 3 的最后一个分句, 让持久化演示文件同样归入"由仓库主人点名清理"的口径, 不再自带删除义务:
- 保留前半句"若问题涉及持久化, 用本地文件, 取醒目名字" (这是做法, 不变).
- 把"用后即焚"换成与规则 1 一致的清理口径, 例如"用完不必自行删除, 需要清理时由仓库主人点名" 或同义短句; 不要新增小节, 不要引入新概念.
- 规则 1 里已有的"演示材料与变体分支都可留着回看, 代理不主动删除; 需要清理时由仓库主人点名删除对象"保持不变.

## 允许范围
- `workflow/demo/SKILL.md` 规则 3 的那个分句.
- 本 issue 文件.

## 禁止范围
- 不改 `UI.md` / `LOGIC.md` / navigate / roadmap.py / 网页 / 测试 / 任何 spec.
- 不改规则 3 的前半句与规则 1, 2, 4, 5, 6.
- 不跑 sync-to-pi.py, 不改 ~/.agents 下真实安装的 skills.

## 验证入口
```bash
grep -n '即焚\|即删\|合并主干前' workflow/demo/SKILL.md workflow/demo/LOGIC.md workflow/demo/UI.md   # 零命中
sed -n '28,33p' workflow/demo/SKILL.md        # 规则 3 仍在, 分句改成点名清理口径
grep -n '变体分支' workflow/demo/SKILL.md workflow/demo/LOGIC.md workflow/demo/UI.md   # 三处仍在
uv run python general/writing-for-llm/check_skill.py workflow/demo/SKILL.md   # OK, 退出 0
uv run python -m pytest workflow/navigate/tests            # 退出 0, 无 failed (占端口先 stop 并确认 alive:false)
```

## 交付证据
执行后填写: 改后规则 3 原文, 各条 grep 结果, check_skill 与 pytest 退出码与汇总行, 原始输出放 `/tmp/m9-04-09/`.

改后规则 3 原文:

> 3. **默认不持久化.** 状态存内存. 持久化是演示要展示的东西, 不是演示该依赖的. 若问题涉及持久化, 用本地文件, 取醒目名字, 用完不必自行删除, 需要清理时由仓库主人点名删除对象.

- grep `即焚\|即删\|合并主干前` 三文件: 零命中 (grep 退出码 1).
- sed '28,33p': 规则 3 仍在, 前半句与规则 1, 2, 4, 5, 6 未动; 规则 1 原文不变.
- grep `变体分支` 三处均在: SKILL.md:28, LOGIC.md:62, UI.md:84.
- check_skill: `workflow/demo/SKILL.md: OK`, 退出码 0.
- pytest: `30 passed in 8.02s`, 退出码 0 (跑前 web_server stop, status alive:false; 收工后再次 stop, status alive:false).
- 原始输出: `/tmp/m9-04-09/{grep-and-sed.txt, check_skill.txt, server-stop.txt, server-status.txt, pytest.txt, server-stop-final.txt}`.
## 停止条件
需要改 Spec/决策; 需要动允许范围之外的文件. 停下报告.
## 验收标准
- [ ] 三文件里再无 即焚/即删/合并主干前 类删除义务.
- [ ] 规则 3 前半句与规则 1 不变; 三处的变体分支约定仍在.
- [ ] check_skill OK, pytest 全绿.
