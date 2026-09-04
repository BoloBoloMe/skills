# MILESTONE-03 E2E Run

## 逐阶段日志

- [ok] create mother demo-main-feature-manual-release
- [ok] export marker and D008 config
- [ok] daemon 0.0.0.0:34113
- [ok] audit NB-002 minimal Containerfile
- [ok] container ssh BatchMode swt-demo-main-feature-manual-release:42749
- [ok] container clone -b demo-main-feature-manual-release, daemon-only read face
- [ok] container pi --help exit=0
- [ok] birth complete
- [ok] container push landed demo-main-feature-manual-release
- [ok] container push rejected with dirty mother tree: Warning: Permanently added '[127.0.0.1]:42749' (ED25519) to the list of known hosts. To git://host.containers.internal:34113/demo  ! [remote rejected] HEAD -> demo-main-feature-manual-release (Working directory has unstaged changes) error: failed to push some refs to 'git://host.containers.internal:34113/demo'
- [ok] container reject matrix: new branch/tag/non-ff/delete
- [ok] host clone -b demo-main-feature-manual-release
- [ok] host push landed demo-main-feature-manual-release: 
- [ok] reject matrix: new branch/tag/non-ff/delete
- [ok] audit NB-001 hooks unchanged
- [ok] audit NB-003 daemon command line
- [ok] cleanup dirty release recorded /tmp/swt-m03-manual-eRaQM3/srv/demo/.swt-m03-checklist.json
- [ok] cleanup container removed swt-demo-main-feature-manual-release
- [ok] cleanup daemon stopped
- [ok] mother retained demo-main-feature-manual-release
- [ok] cleanup ssh directory removed /tmp/swt-m03-manual-eRaQM3/ssh
- [ok] cleanup complete

## 结果事实

- 夹具主仓: `/tmp/swt-m03-manual-eRaQM3/srv/demo`
- 母体目录: `/tmp/swt-m03-manual-eRaQM3/mother/demo-main-feature-manual-release`
- 容器: `swt-demo-main-feature-manual-release`
- 全通网络: 是, M03 全通网络中间态, nft 白名单不属于本切片.
- daemon 监听地址: `0.0.0.0:34113` (实际值).
- daemon 监听模式: 0.0.0.0 兜底.
- pi --help: 命令 `pi --help`, 退出码 `0`.

### 命令结果附录

```text
pi --help
pi - AI coding assistant with read, bash, edit, write tools

Usage:
  pi [options] [--] [@files...] [messages...]

Commands:
  pi install <source> [-l]     Install extension source and add to settings
  pi remove <source> [-l]      Remove extension source from settings
  pi uninstall <source> [-l]   Alias for remove
  pi update [source|self|pi]   Update pi, extensions, or model catalogs
  pi list                      List installed extensions from settings
  pi config [-l]               Open TUI to enable/disable package resources (Tab switches scope)
  pi auth <command>            Print credentials or check provider readiness
  pi <command> --help          Show help for install/remove/uninstall/update/list/config/auth

Options:
  --provider <name>              Provider name (default: google)
  --model <pattern>              Model pattern or ID (supports "provider/id" and optional ":<thinking>")
  --api-key <key>                API key (defaults to env vars)
  --system-prompt <text>         System prompt (default: coding assistant prompt)
  --append-system-prompt <text>  Append text or file contents to the system prompt (can be used multiple times)
  --mode <mode>                  Output mode: text (default), json, or rpc
  --print, -p                    Non-interactive mode: process prompt and exit
  --continue, -c                 Continue previous session
  --resume, -r                   Select a session to resume
  --session <path|id>            Use specific session file or partial UUID
  --session-id <id>              Use exact project session ID, creating it if missing
  --fork <path|id>               Fork specific session file or partial UUID into a new session
  --session-dir <dir>            Directory for session storage and lookup
  --no-session                   Don't save session (ephemeral)
  --name, -n <name>              Set session display name
  --models <patterns>            Comma-separated model patterns for Ctrl+P cycling
                                 Supports globs (anthropic/*, *sonnet*) and fuzzy matching
  --no-tools, -nt                Disable all tools by default (built-in and extension)
  --no-builtin-tools, -nbt       Disable built-in tools by default but keep extension/custom tools enabled
  --tools, -t <tools>            Comma-separated allowlist of tool names to enable
                                 Applies to built-in, extension, and custom tools
  --exclude-tools, -xt <tools>   Comma-separated denylist of tool names to disable
                                 Applies to built-in, extension, and custom tools
  --thinking <level>             Set thinking level: off, minimal, low, medium, high, xhigh, max
  --extension, -e <path>         Load an extension file (can be used multiple times)
  --no-extensions, -ne           Disable extension discovery (explicit -e paths still work)
  --skill <path>                 Load a skill file or directory (can be used multiple times)
  --no-skills, -ns               Disable skills discovery and loading
  --prompt-template <path>       Load a prompt template file or directory (can be used multiple times)
  --no-prompt-templates, -np     Disable prompt template discovery and loading
  --theme <path>                 Load a theme file or directory (can be used multiple times)
  --use-theme <name[/name]>      Set the initial interactive theme for this run
  --no-themes                    Disable theme discovery and loading
  --no-context-files, -nc        Disable AGENTS.md and CLAUDE.md discovery and loading
  --export <file>                Export session file to HTML and exit
  --list-models [search]         List available models (with optional fuzzy search)
  --verbose                      Force verbose startup (overrides quietStartup setting)
  --tui-mode <mode>              TUI mode: regular (default) or fullscreen
  --approve, -a                  Trust project-local files for this run
  --no-approve, -na              Ignore project-local files for this run
  --offline                      Disable startup network operations (same as PI_OFFLINE=1)
  --                             End option parsing; treat remaining arguments as messages/files
  --help, -h                     Show this help
  --version, -v                  Show version number

Extensions can register additional flags (e.g., --plan from plan-mode extension).

Examples:
  # Print a provider API key for an external client
  pi auth print-api-key --provider openai

  # Print an OAuth bearer token for an external client (refreshes if expired)
  pi auth print-bearer-token --provider openai-codex

  # Interactive mode
  pi

  # Interactive mode with initial prompt
  pi "List all .ts files in src/"

  # Include files in initial message
  pi @prompt.md @image.png "What color is the sky?"

  # Non-interactive mode (process and exit)
  pi -p "List all .ts files in src/"

  # Prompt beginning with a dash
  pi -p -- "- Summarize these points"

  # Multiple messages (interactive)
  pi "Read package.json" "What dependencies do we have?"

  # Continue previous session
  pi --continue "What did we discuss?"

  # Start a named session
  pi --name "Refactor auth module"

  # Use different model
  pi --provider openai --model gpt-4o-mini "Help me refactor this code"

  # Use model with provider prefix (no --provider needed)
  pi --model openai/gpt-4o "Help me refactor this code"

  # Use model with thinking level shorthand
  pi --model sonnet:high "Solve this complex problem"

  # Limit model cycling to specific models
  pi --models claude-sonnet,claude-haiku,gpt-4o

  # Limit to a specific provider with glob pattern
  pi --models "github-copilot/*"

  # Cycle models with fixed thinking levels
  pi --models sonnet:high,haiku:low

  # Start with a specific thinking level
  pi --thinking high "Solve this complex problem"

  # Read-only mode (no file modifications possible)
  pi --tools read,grep,find,ls -p "Review the code in src/"

  # Disable one tool while keeping the rest available
  pi --exclude-tools ask_question

  # Export a session file to HTML
  pi --export ~/.pi/agent/sessions/--path--/session.jsonl
  pi --export session.jsonl output.html

Environment Variables:
  ANTHROPIC_AUTH_TOKEN             - Anthropic bearer auth token
  ANTHROPIC_API_KEY                - Anthropic Claude API key
  ANTHROPIC_OAUTH_TOKEN            - Anthropic OAuth token (alternative to API key)
  ANT_LING_API_KEY                 - Ant Ling API key
  OPENAI_API_KEY                   - OpenAI GPT API key
  AZURE_OPENAI_API_KEY             - Azure OpenAI API key
  AZURE_OPENAI_BASE_URL            - Azure OpenAI/Cognitive Services base URL (e.g. https://{resource}.openai.azure.com)
  AZURE_OPENAI_RESOURCE_NAME       - Azure OpenAI resource name (alternative to base URL)
  AZURE_OPENAI_API_VERSION         - Azure OpenAI API version (default: v1)
  AZURE_OPENAI_DEPLOYMENT_NAME_MAP - Azure OpenAI model=deployment map (comma-separated)
  DEEPSEEK_API_KEY                 - DeepSeek API key
  NVIDIA_API_KEY                   - NVIDIA NIM API key
  GEMINI_API_KEY                   - Google Gemini API key
  GROQ_API_KEY                     - Groq API key
  CEREBRAS_API_KEY                 - Cerebras API key
  XAI_API_KEY                      - xAI Grok API key
  FIREWORKS_API_KEY                - Fireworks API key
  TOGETHER_API_KEY                 - Together AI API key
  BASETEN_API_KEY                  - Baseten API key
  OPENROUTER_API_KEY               - OpenRouter API key
  AI_GATEWAY_API_KEY               - Vercel AI Gateway API key
  ZAI_API_KEY                      - ZAI Coding Plan API key (Global)
  ZAI_CODING_CN_API_KEY            - ZAI Coding Plan API key (China)
  MISTRAL_API_KEY                  - Mistral API key
  MINIMAX_API_KEY                  - MiniMax API key
  MOONSHOT_API_KEY                 - Moonshot AI API key
  OPENCODE_API_KEY                 - OpenCode Zen/OpenCode Go API key
  KIMI_API_KEY                     - Kimi For Coding API key
  CLOUDFLARE_API_KEY               - Cloudflare API token (Workers AI and AI Gateway)
  CLOUDFLARE_ACCOUNT_ID            - Cloudflare account id (required for both)
  CLOUDFLARE_GATEWAY_ID            - Cloudflare AI Gateway slug (required for AI Gateway)
  QWEN_TOKEN_PLAN_API_KEY          - Qwen Token Plan API key (international region)
  QWEN_TOKEN_PLAN_CN_API_KEY       - Qwen Token Plan API key (China region)
  XIAOMI_API_KEY                   - Xiaomi MiMo API key (api.xiaomimimo.com billing)
  XIAOMI_TOKEN_PLAN_CN_API_KEY     - Xiaomi MiMo Token Plan API key (China region)
  XIAOMI_TOKEN_PLAN_AMS_API_KEY    - Xiaomi MiMo Token Plan API key (Amsterdam region)
  XIAOMI_TOKEN_PLAN_SGP_API_KEY    - Xiaomi MiMo Token Plan API key (Singapore region)
  AWS_PROFILE                      - AWS profile for Amazon Bedrock
  AWS_ACCESS_KEY_ID                - AWS access key for Amazon Bedrock
  AWS_SECRET_ACCESS_KEY            - AWS secret key for Amazon Bedrock
  AWS_BEARER_TOKEN_BEDROCK         - Bedrock API key (bearer token)
  AWS_REGION                       - AWS region for Amazon Bedrock (e.g., us-east-1)
  PI_CODING_AGENT_DIR              - Config directory (default: ~/.pi/agent)
  PI_CODING_AGENT_SESSION_DIR      - Session storage directory (overridden by --session-dir)
  PI_PACKAGE_DIR                   - Override package directory (for Nix/Guix store paths)
  PI_OFFLINE                       - Disable startup network operations when set to 1/true/yes
  PI_TELEMETRY                     - Override install telemetry when set to 1/true/yes or 0/false/no
  PI_SHARE_VIEWER_URL              - Base URL for /share command (default: https://pi.dev/session/)

Built-in Tool Names:
  read       - Read file contents
  bash       - Execute bash commands
  powershell - Execute PowerShell commands on Windows
  edit       - Edit files with find/replace
  write      - Write files (creates/overwrites)
  grep       - Search file contents (read-only, off by default)
  find       - Find files by glob pattern (read-only, off by default)
  ls         - List directory contents (read-only, off by default)
Warning: Permanently added '[127.0.0.1]:42749' (ED25519) to the list of known hosts.
```

## checklist

```json
{
  "decision_points": {
    "失败清理": {
      "decision": "保留运行时 JSON, 由 cleanup 兜底发现并人工处理",
      "observed": "not exercised"
    },
    "母体复用": {
      "decision": "首次创建母体",
      "observed": false
    },
    "端口冲突": {
      "decision": "记录失败事实, 不自动换容器端口",
      "observed": "not exercised"
    },
    "脏放行": {
      "basis": "explicit --i-am-sure; D012 cleanup override",
      "decision": "allow cleanup",
      "recorded_at": "2026-09-04T13:27:29Z",
      "registration_fields": [
        "状态值",
        "夹具路径",
        "时间",
        "依据"
      ]
    },
    "黑白名单模式": {
      "decision": "M03 全通网络中间态; nft 白名单归 M04",
      "observed": "full-network-intermediate"
    }
  },
  "dirty_release": {
    "basis": "explicit --i-am-sure; D012 cleanup override",
    "decision": "allow cleanup",
    "fixture_path": "/tmp/swt-m03-manual-eRaQM3",
    "recorded_at": "2026-09-04T13:27:29Z",
    "status_summary": " M README.md",
    "uncommitted_changes": 1,
    "unpushed_commits": 0
  },
  "network": {
    "daemon_address": "0.0.0.0",
    "daemon_port": 34113,
    "mode": "full-network-intermediate"
  },
  "version": 1
}
```
