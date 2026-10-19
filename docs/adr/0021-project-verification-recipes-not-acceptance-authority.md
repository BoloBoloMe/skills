# 项目验证配方提供操作能力, 不成为另一套验收标准

create-verification-skill / maintain-verification-skill 生成和维护项目本地的启动/实例检查/真实入口操作/取证/清理配方及功能地图, 以已确认的 PRODUCT.md 为必需输入并只覆盖其相关范围, TECHNICAL.md/EXECUTION.md 仅作可选线索, 产品是否通过仍以已确认的 PRODUCT.md 为准, 不以地图或当前代码现状另立 AC 或弱化要求.

生成/维护会话可以调查和编写配方, 但默认由一名未参与编写的新子会话实跑本次全部新增或修改的功能配方, 不再套 verify-change 重复产品验收; 修改范围仅项目本地验证 skill 自身文档和辅助脚本, 产品坏了就报告, 不借维护修产品或自动开 PR.

这样保留可复用操作知识而不制造第二套产品权威或递归验收流程; 当前仅完成设计落账, 完整规则见 [验证 skills 账本](../changes/verification-skills/DECISIONS.md) 的 D005-D006/D011-D012/D017/D020/D022-D024/D036.
