# codebase-map: 宿主常驻自建服务 + 构建期汉化, 纯手动调用

后续约定(已确认, 待实施): [ADR-0028](0028-artifact-mechanization-and-unified-presentation.md) 将 codebase-map 的展示托管和生命周期合入 present, 不再自建展示后端; 分析能力, 专用可视化和纯手动调用定位保留. 实施时须重核原 stop 语义, 不能让局部操作误停共用页面. 本次仅记录方案, 当前实现未迁移, 下方保留历史原文.

背景: 我们要一个"把任意代码库画成可交互结构地图"的工具. [milestone-12 侦查](../changes/workflow-stack-review/milestone-12/FINDINGS.md) 得出结论: 城市观感只有 CodeCharta 能给, 但它的分析端要 Java 22 + Node 22.19, 与仓库"纯 python + uv"的栈冲突; 前端可以单独取用. [milestone-13 账本](../changes/workflow-stack-review/milestone-13/DECISIONS.md) 记了逐条裁决与依据.

决策: 三条合并成一个形态.

> 适配指针 (milestone-25 补, 不改下文历史原文): 本 ADR 写于 milestone-13, 其中三处已被后续裁决收窄. (a) 分析端 tag 改用纯数字 `2.3.0`, 版本以镜像 digest 核对 (milestone-24 U002); (b) "高度=层号" 一类自定指标不复存在, 指标按官方默认, 层号与环在官方依赖视图看 (milestone-24 U003); (c) 汉化不再属于第一版, 它拆成 v1 之后的第二片 (milestone-13 D027), v1 直接用官方 `web.zip` 前端. 服务形态, 单例, 端口纪律, 数据落点与纯手动调用这些条款仍然有效.

1. **分析端借官方镜像, 不自建** — 用 `codecharta/codecharta-analysis` (钉 `ana-2.3.0`) 在宿主的 podman 里跑, 因此宿主不需要装 JDK. 自建 python 分析器只在"要与 ccsh 输出不同"时才有意义, 当前没有这种需求, 而且它拿不到 ccsh 独有的层号/环/向上依赖.
2. **前端构建期汉化, 零 fork** — clone 上游 `visualization` (钉 `vis-2.9.1`), 用三通道词表替换 (模板静态文案 / `.ts` 整条字面量 / 绑定与插值内字面量), 再 `npm run build`. 只做整条完全相等替换, 幂等可重放; 升级只改 tag. 不跑上游单测 (汉化必然打红 62 个测试文件的文本断言), 改用自建截图冒烟.
3. **交付走自建 python 常驻服务** — 一个进程负责调 podman、托管构建产物、记录状态、提供 stop (上游是 hash 路由, 服务端只看到 `/`, 不需要深链回退; 详见 D021/F011). 单例, 一个端口, 多库靠 `?file=`; 交付局域网 URL 而不是 loopback 或文件路径. 不引 nginx: 它只为一份配置和一个镜像, 换来的能力几十行 python 就够.
4. **纯手动, 不进流程** — 任何 skill 都不调用它, 只在宿主上手动用, 运行状态与构建缓存放宿主 `~/.agents/codebase-map/`, 分析产物跟被分析的库走 (`.codebase-map/cc.json`), 本仓库不入库任何数据或前端产物.

后果:

- 宿主成为唯一运行环境, 沙箱容器内不支持也不降级; 环境缺失时报错停下 (D003). 这让能力边界与"部署在哪"绑死, 以后要在容器里用需要重新裁决.
- 汉化是无 fork 的构建期替换, 代价是词表维护 (约 900-1000 条) 与每次升级后跑一次 `--check` 看哪些词失效.
- 自建服务接管了 nginx 的职责 (托管产物, 端口、单例与状态记录), 理由是常驻单例与状态记录, 不是深链回退 — 那条需求已被证伪 (D021/F011).
- 前端与 ccsh 版本钉死, 升级是显式动作, 不跟 latest.
