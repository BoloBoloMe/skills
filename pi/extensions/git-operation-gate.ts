import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { isToolCallEventType } from "@earendil-works/pi-coding-agent";

/**
 * git-operation-gate: 拦截智能体发起的危险 Git 操作, 向用户确认后才放行.
 *
 * 分级拦截:
 *   - 危险级 (danger): 不可逆破坏操作, 弹窗默认拒绝
 *   - 警告级 (warn): 可逆但有风险的操作, 弹窗默认允许
 *
 * 匹配策略:
 *   - 对整个命令字符串跨行全局扫描, 命中多条规则时取最高等级
 *   - 同等级多条规则命中时, 弹窗拼接展示所有理由
 *
 * 会话放行:
 *   - "本次会话都允许" 按规则粒度放行, 不落盘
 *   - `session_start` 事件清空允许列表 (切换/新建/重载会话)
 */

type DangerLevel = "warn" | "danger";

interface GitGuard {
  name: string;
  level: DangerLevel;
  reason: string;
  pattern: RegExp;
}

const LEVEL_LABEL: Record<DangerLevel, string> = {
  warn: "⚠️ 警告",
  danger: "🛑 危险",
};

const GUARDS: GitGuard[] = [
  // ==================== 危险级 ====================
  {
    name: "force-push",
    level: "danger",
    reason: "将覆盖远端历史，影响协作者",
    pattern: /\bgit\b[\s\S]*?\bpush\b[\s\S]*?(--force\b|-f\b)/i,
  },
  {
    name: "delete-remote-branch",
    level: "danger",
    reason: "将删除远端分支",
    pattern: /\bgit\b[\s\S]*?\bpush\b[\s\S]*?--delete\b/i,
  },
  {
    name: "hard-reset",
    level: "danger",
    reason: "将永久销毁暂存区和工作区改动",
    pattern: /\bgit\b[\s\S]*?\breset\b[\s\S]*?--hard\b/i,
  },
  {
    name: "force-delete-branch",
    level: "danger",
    reason: "将强制删除本地分支",
    pattern: /\bgit\b[\s\S]*?\bbranch\b[\s\S]*?-D\b/i,
  },
  {
    name: "clean",
    level: "danger",
    reason: "将永久删除未跟踪文件",
    pattern: /\bgit\b[\s\S]*?\bclean\b[\s\S]*?-f/i,
  },
  {
    name: "stash-clear",
    level: "danger",
    reason: "将清空全部 stash",
    pattern: /\bgit\b[\s\S]*?\bstash\b[\s\S]*?\bclear\b/i,
  },
  {
    name: "discard-file-checkout",
    level: "danger",
    reason: "将丢弃工作区文件修改 (checkout -- <file>)",
    pattern: /\bgit\b[\s\S]*?\bcheckout\b[\s\S]*?\s--\s+\S/i,
  },
  {
    name: "gc-prune",
    level: "danger",
    reason: "将永久删除不可达对象",
    pattern: /\bgit\b[\s\S]*?\bgc\b[\s\S]*?--prune\b/i,
  },

  // ==================== 警告级 ====================
  {
    name: "push",
    level: "warn",
    reason: "将推送到远端仓库",
    pattern: /\bgit\b[\s\S]*?\bpush\b/i,
  },
  {
    name: "rebase",
    level: "warn",
    reason: "将改写提交历史",
    pattern: /\bgit\b[\s\S]*?\brebase\b/i,
  },
  {
    name: "commit-amend",
    level: "warn",
    reason: "将改写最近一次提交",
    pattern: /\bgit\b[\s\S]*?\bcommit\b[\s\S]*?--amend\b/i,
  },
  {
    name: "stash-drop",
    level: "warn",
    reason: "将删除一个 stash 条目",
    pattern: /\bgit\b[\s\S]*?\bstash\b[\s\S]*?\bdrop\b/i,
  },
  {
    name: "tag-delete",
    level: "warn",
    reason: "将删除本地 tag",
    pattern: /\bgit\b[\s\S]*?\btag\b[\s\S]*?(?:-d\b|--delete\b)/i,
  },
  {
    name: "restore",
    level: "warn",
    reason: "将丢弃或取消暂存文件修改",
    pattern: /\bgit\b[\s\S]*?\brestore\b/i,
  },
];

export default function (pi: ExtensionAPI) {
  const allowlist = new Set<string>();

  pi.on("session_start", () => allowlist.clear());

  pi.on("tool_call", async (event, ctx) => {
    if (!isToolCallEventType("bash", event)) return;
    const cmd = event.input.command ?? "";

    // 收集所有命中的规则
    const hits = GUARDS.filter((g) => g.pattern.test(cmd));
    if (hits.length === 0) return;

    // 取最高危险等级
    const maxLevel: DangerLevel =
      hits.some((g) => g.level === "danger") ? "danger" : "warn";

    // 只保留该等级命中的规则
    const levelHits = hits.filter((g) => g.level === maxLevel);

    // 若所有命中的规则已在本会话放行, 跳过弹窗
    if (levelHits.every((g) => allowlist.has(g.name))) return;

    // 构建弹窗内容
    const reasons = levelHits
      .map((g) => `· ${g.name}: ${g.reason}`)
      .join("\n");

    const title = [
      `[${LEVEL_LABEL[maxLevel]}] 拦截到危险 Git 操作`,
      ``,
      `等级: ${maxLevel === "danger" ? "危险" : "警告"}`,
      `理由:`,
      reasons,
      ``,
      `命令:`,
      cmd,
    ].join("\n");

    const choice = await ctx.ui.select(title, [
      "拒绝",
      "允许本次",
      "本次会话都允许",
    ]);

    if (!choice || choice === "拒绝") {
      return { block: true, reason: "用户拒绝执行" };
    }

    if (choice === "本次会话都允许") {
      for (const g of levelHits) {
        allowlist.add(g.name);
      }
    }
    // "允许本次": 仅本次放行, 不记录
  });
}
