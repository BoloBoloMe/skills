# navigate roadmap 产物从 markdown 文件集改为单 ROADMAP.json + 守门脚本 + skill 自持有展示服务

navigate skill 的路线图产物原是 ROADMAP.md + 多个 MILESTONE-NN.md, 由 llm 直接手写, 格式正确性取决于 llm 输出质量. 决策: 路线图全部信息收敛进单个 ROADMAP.json, llm 的一切读写必经 skill 提供的守门脚本 (save/delete/query, 写后整文档校验, 失败不落盘), 让格式与必填信息的保证从 "llm 自觉" 变为 "脚本强制"; 同时 navigate 自持有一个同 uid 单例的常驻 web 服务 + 自包含单页应用做路线图可视化 (宇宙/恒星/飞船隐喻), 取代制图时 present 画一次性 ROADMAP.html 的路径.

备选方案: 保留 markdown 文件集 + llm 直接读写 (被拒绝: 正确性无强制保障); 复用 present 的常驻展示服务 (被拒绝: 参照 ADR-0015 mailbox 独立先例, skill 自持有, navigate 不依赖 present); 旧格式迁移命令 (被拒绝: 一次性重建成本低于维护迁移器).

后果: ROADMAP.md/MILESTONE-NN.md 不再产生, 旧路线图出现时由 llm 读经脚本重建; JSON 不存任何展示信息, 恒星布局由前端按阻塞关系自动推导; present skill 不再参与 navigate 制图. 完整决策与 schema 见 docs/changes/navigate-roadmap-json/DECISIONS.md.
