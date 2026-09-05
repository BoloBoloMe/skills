# MILESTONE-03 E2E Run

## 逐阶段日志

- [ok] create mother demo-main-feature-pi-report
- [ok] export marker and D008 config
- [ok] daemon 0.0.0.0:44651
- [ok] audit NB-002 minimal Containerfile
- [ok] container ssh BatchMode swt-demo-main-feature-pi-report:42329
- [ok] container clone -b demo-main-feature-pi-report, daemon-only read face
- [ok] container pi --help exit=0
- [ok] birth complete
- [ok] container push landed demo-main-feature-pi-report
- [ok] container push rejected with dirty mother tree: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts. To git://host.containers.internal:44651/demo  ! [remote rejected] HEAD -> demo-main-feature-pi-report (Working directory has unstaged changes) error: failed to push some refs to 'git://host.containers.internal:44651/demo'
- [ok] container reject matrix: new branch/tag/non-ff/delete
- [ok] host clone -b demo-main-feature-pi-report
- [ok] host push landed demo-main-feature-pi-report:
- [ok] reject matrix: new branch/tag/non-ff/delete
- [ok] audit NB-001 hooks unchanged
- [ok] audit NB-003 daemon command line
- [ok] cleanup container removed swt-demo-main-feature-pi-report
- [ok] cleanup daemon stopped
- [ok] mother retained demo-main-feature-pi-report
- [ok] cleanup ssh directory removed /tmp/swt-m03-test-2qvld9t9/ssh
- [ok] cleanup complete

## 结果事实

- 夹具主仓: `/tmp/swt-m03-test-2qvld9t9/srv/demo`
- 母体目录: `/tmp/swt-m03-test-2qvld9t9/mother/demo-main-feature-pi-report`
- 容器: `swt-demo-main-feature-pi-report`
- 全通网络: 是, M03 全通网络中间态, nft 白名单不属于本切片.
- daemon 监听地址: `0.0.0.0:44651` (实际值).
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
Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.
```

### 全链命令与输出附录

以下记录实际调用的 git/podman/ssh/daemon 命令及结果.

```text
$ uv run python /home/bolo/Workspace/skills/workflow/use-worktree/scripts/slug.py demo main feature/pi-report
exit=0
stdout: project=demo
source_branch=main
source_slug=main
target_branch=feature/pi-report
target_slug=feature-pi-report
dir=demo-main-feature-pi-report
stderr: (empty)

$ ps -eo pid=,args=
exit=0
stdout:       1 /usr/lib/systemd/systemd --switched-root --system --deserialize=53 splas
      2 [kthreadd]
      3 [pool_workqueue_release]
      4 [kworker/R-rcu_gp]
      5 [kworker/R-sync_wq]
      6 [kworker/R-kvfree_rcu_reclaim]
      7 [kworker/R-slub_flushwq]
      8 [kworker/R-netns]
     10 [kworker/0:0H-kblockd]
     13 [kworker/R-mm_percpu_wq]
     14 [ksoftirqd/0]
     15 [rcu_preempt]
     16 [rcu_exp_par_gp_kthread_worker/0]
     17 [rcu_exp_gp_kthread_worker]
     18 [migration/0]
     19 [kprobe-optimizer]
     20 [idle_inject/0]
     21 [cpuhp/0]
     22 [cpuhp/2]
     23 [idle_inject/2]
     24 [migration/2]
     25 [ksoftirqd/2]
     27 [kworker/2:0H-kblockd]
     28 [cpuhp/4]
     29 [idle_inject/4]
     30 [migration/4]
     31 [ksoftirqd/4]
     33 [kworker/4:0H-kblockd]
     34 [cpuhp/6]
     35 [idle_inject/6]
     36 [migration/6]
     37 [ksoftirqd/6]
     39 [kworker/6:0H-kblockd]
     40 [cpuhp/8]
     41 [idle_inject/8]
     42 [migration/8]
     43 [ksoftirqd/8]
     45 [kworker/8:0H-kblockd]
     46 [cpuhp/10]
     47 [idle_inject/10]
     48 [migration/10]
     49 [ksoftirqd/10]
     51 [kworker/10:0H-kblockd]
     52 [cpuhp/1]
     53 [idle_inject/1]
     54 [migration/1]
     55 [ksoftirqd/1]
     57 [kworker/1:0H-kblockd]
     58 [cpuhp/3]
     59 [idle_inject/3]
     60 [migration/3]
     61 [ksoftirqd/3]
     63 [kworker/3:0H-kblockd]
     64 [cpuhp/5]
     65 [idle_inject/5]
     66 [migration/5]
     67 [ksoftirqd/5]
     69 [kworker/5:0H-kblockd]
     70 [cpuhp/7]
     71 [idle_inject/7]
     72 [migration/7]
     73 [ksoftirqd/7]
     75 [kworker/7:0H-kblockd]
     76 [cpuhp/9]
     77 [idle_inject/9]
     78 [migration/9]
     79 [ksoftirqd/9]
     81 [kworker/9:0H-kblockd]
     82 [cpuhp/11]
     83 [idle_inject/11]
     84 [migration/11]
     85 [ksoftirqd/11]
     87 [kworker/11:0H-kblockd]
     88 [kdevtmpfs]
     89 [kworker/R-inet_frag_wq]
     90 [rcu_tasks_kthread]
     91 [rcu_tasks_rude_kthread]
     92 [kauditd]
     93 [khungtaskd]
     94 [oom_reaper]
     97 [kworker/R-writeback]
     98 [kcompactd0]
     99 [ksmd]
    100 [khugepaged]
    101 [kworker/R-kblockd]
    102 [kworker/R-blkcg_punt_bio]
    103 [kworker/R-kintegrityd]
    104 [irq/9-acpi]
    107 [kworker/R-tpm_dev_wq]
    108 [kworker/R-ata_sff]
    109 [kworker/R-md_bitmap]
    110 [kworker/R-md_llbitmap_io]
    111 [kworker/R-md_llbitmap_unplug]
    112 [kworker/R-edac-poller]
    113 [kworker/R-devfreq_wq]
    114 [watchdogd]
    115 [kworker/R-quota_events_unbound]
    119 [irq/25-AMD-Vi0-Evt]
    120 [irq/26-AMD-Vi0-PPR]
    121 [irq/27-AMD-Vi0-GA]
    122 [kswapd0]
    123 [ecryptfs-kthread]
    124 [kworker/R-kthrotld]
    126 [kworker/R-acpi_thermal_pm]
    127 [kworker/R-mld]
    128 [kworker/R-ipv6_addrconf]
    129 [kworker/R-kstrp]
    151 [kworker/R-charger_manager]
    152 [irq/28-ACPI:Event]
    153 [irq/29-ACPI:Event]
    154 [irq/30-ACPI:Event]
    155 [irq/31-ACPI:Event]
    156 [irq/32-ACPI:Event]
    157 [irq/33-ACPI:Event]
    158 [irq/34-ACPI:Event]
    368 [irq/60-ITE8227:00]
    369 [irq/58-MSFT0001:00]
    378 [kworker/R-nvme-wq]
    379 [kworker/R-nvme-reset-wq]
    380 [kworker/R-nvme-delete-wq]
    381 [kworker/R-nvme-auth-wq]
    396 [kworker/10:1H-kblockd]
    397 [kworker/3:1H-kblockd]
    410 [kworker/2:1H-kblockd]
    413 [jbd2/nvme0n1p2-8]
    414 [kworker/R-ext4-rsv-conversion]
    468 [kworker/R-USBC000:00-con1]
    476 /usr/lib/systemd/systemd-journald
    521 [kworker/4:1H-kblockd]
    522 [kworker/8:1H-kblockd]
    523 [kworker/6:1H-kblockd]
    524 /usr/lib/systemd/systemd-resolved
    525 [kworker/5:1H-kblockd]
    528 /usr/lib/systemd/systemd-oomd
    531 /usr/lib/systemd/systemd-udevd
    536 [psimon]
    581 [kworker/9:1H-kblockd]
    605 [kworker/R-cfg80211]
    839 [kworker/0:1H-kblockd]
    841 [kworker/1:1H-kblockd]
    855 [kworker/7:1H-kblockd]
    857 [kworker/11:1H-kblockd]
    859 [irq/80-rtw89_pci]
   1288 avahi-daemon: running [bolo-Yoga.local]
   1289 /usr/libexec/bluetooth/bluetoothd
   1291 /bin/sh /usr/lib/systemd/scripts/chronyd-starter.sh -n -F 1
   1292 @dbus-daemon --system --address=systemd: --nofork --nopidfile --systemd-
   1298 /usr/libexec/iio-sensor-proxy
   1301 /usr/bin/python3 /usr/bin/networkd-dispatcher --run-startup-triggers
   1303 /usr/lib/polkit-1/polkitd --no-debug --log-level=notice
   1312 /usr/lib/snapd/snapd
   1315 /usr/libexec/accounts-daemon
   1330 /usr/sbin/cron -f -P
   1333 /usr/libexec/switcheroo-control
   1336 /usr/lib/systemd/systemd-logind
   1338 /usr/libexec/udisks2/udisksd
   1375 avahi-daemon: chroot helper
   1399 /usr/sbin/rsyslogd -n -iNONE
   1415 /usr/sbin/NetworkManager --no-daemon
   1431 /usr/sbin/chronyd -n -F 1
   1432 /usr/sbin/wpa_supplicant -u -s -O DIR=/run/wpa_supplicant GROUP=netdev
   1443 /usr/sbin/chronyd -n -F 1
   1496 /usr/sbin/ModemManager
   1591 /usr/bin/python3 /usr/share/unattended-upgrades/unattended-upgrade-shutd
   1602 sshd: /usr/sbin/sshd -D [listener] 0 of 10-100 startups
   1617 /usr/sbin/gdm3
   1644 [kworker/R-USBC000:00-con2]
   1653 [kworker/R-amdgpu-reset-dev]
   1671 [kworker/R-ttm]
   1699 [kworker/R-amdgpu_dm_hpd_rx_offload_wq]
   1700 [kworker/R-amdgpu_dm_hpd_rx_offload_wq]
   1701 [kworker/R-amdgpu_dm_hpd_rx_offload_wq]
   1702 [kworker/R-dm_vblank_control_workqueue]
   1703 [card1-crtc0]
   1704 [card1-crtc1]
   1705 [card1-crtc2]
   1706 [card1-crtc3]
   1707 [kworker/R-gfx]
   1708 [kworker/R-comp_1.0.0]
   1709 [kworker/R-comp_1.1.0]
   1710 [kworker/R-comp_1.2.0]
   1711 [kworker/R-comp_1.3.0]
   1712 [kworker/R-comp_1.0.1]
   1713 [kworker/R-comp_1.1.1]
   1714 [kworker/R-comp_1.2.1]
   1715 [kworker/R-comp_1.3.1]
   1716 [kworker/R-sdma0]
   1717 [kworker/R-vcn_dec]
   1718 [kworker/R-vcn_enc0]
   1719 [kworker/R-vcn_enc1]
   1720 [kworker/R-jpeg_dec]
   2097 /usr/libexec/rtkit-daemon
   2225 [krfcommd]
   2333 /usr/libexec/colord
   2370 /usr/libexec/upowerd
   3238 /usr/libexec/power-profiles-daemon
   3373 gdm-session-worker [pam/gdm-password]
   3554 /usr/lib/systemd/systemd --user
   3579 (sd-pam)
   3609 /usr/bin/dbus-daemon --session --address=systemd: --nofork --nopidfile -
   3610 /usr/bin/pipewire
   3614 /usr/bin/gnome-keyring-daemon --foreground --components=pkcs11,secrets -
   3628 /usr/bin/mpris-proxy
   3630 /usr/bin/wireplumber
   3632 /usr/bin/pipewire -c filter-chain.conf
   3634 /usr/bin/pipewire-pulse
   3713 /usr/libexec/xdg-document-portal
   3717 /usr/libexec/xdg-permission-store
   3724 fusermount3 -o rw,nosuid,nodev,fsname=portal,auto_unmount,subtype=portal
   3751 /usr/libexec/gdm-wayland-session /usr/bin/gnome-session --session=ubuntu
   3763 /usr/libexec/gnome-session-init-worker ubuntu
   3974 /usr/libexec/gcr-ssh-agent --base-dir /run/user/1000/gcr
   3975 /usr/libexec/gnome-remote-desktop-daemon
   3976 /usr/libexec/gnome-session-ctl --monitor
   3977 /usr/bin/ssh-agent -D
   3992 /usr/libexec/gvfsd
   4007 /usr/libexec/gvfsd-fuse /run/user/1000/gvfs -f
   4010 /usr/libexec/gnome-session-service --session=ubuntu
   4046 /usr/bin/gnome-shell --mode=ubuntu
   4122 /usr/libexec/at-spi-bus-launcher
   4129 /usr/bin/dbus-daemon --config-file=/usr/share/defaults/at-spi2/accessibi
   4131 /usr/libexec/at-spi2-registryd --use-gnome-session
   4154 /usr/libexec/gnome-shell-calendar-server
   4161 /usr/libexec/evolution-source-registry
   4173 /usr/bin/gjs -m /usr/share/gnome-shell/org.gnome.Shell.Notifications
   4193 /usr/libexec/gsd-a11y-settings
   4195 /usr/libexec/gsd-color
   4197 /usr/libexec/gsd-datetime
   4198 /usr/libexec/gsd-housekeeping
   4199 /usr/libexec/gsd-keyboard
   4203 /usr/libexec/gsd-media-keys
   4205 /usr/libexec/gsd-power
   4209 /usr/libexec/gsd-print-notifications
   4215 /usr/libexec/gsd-rfkill
   4217 /usr/libexec/gsd-screensaver-proxy
   4218 /usr/libexec/gsd-sharing
   4228 /usr/libexec/gsd-smartcard
   4232 /usr/libexec/gsd-sound
   4233 /usr/libexec/gsd-usb-protection
   4237 /usr/libexec/gsd-disk-utility-notify
   4243 /usr/libexec/gsd-wwan
   4245 /usr/libexec/evolution-data-server/evolution-alarm-notify
   4273 /usr/bin/update-notifier
   4281 /usr/libexec/goa-daemon
   4346 /usr/bin/gjs -m /usr/share/gnome-shell/org.gnome.ScreenSaver
   4371 /usr/libexec/gsd-printer
   4375 /usr/libexec/goa-identity-service
   4402 /usr/libexec/evolution-calendar-factory
   4444 /usr/libexec/evolution-addressbook-factory
   4445 /usr/libexec/localsearch-3
   4450 /usr/libexec/xdg-desktop-portal
   4475 /usr/libexec/xdg-desktop-portal-gnome
   4488 /usr/libexec/gvfs-udisks2-volume-monitor
   4501 /usr/libexec/gvfs-gphoto2-volume-monitor
   4506 /usr/libexec/gvfs-goa-volume-monitor
   4511 /usr/libexec/gvfs-mtp-volume-monitor
   4516 /usr/libexec/gvfs-afc-volume-monitor
   4578 /usr/libexec/gvfsd-metadata
   4753 /usr/libexec/dconf-service
   4837 /usr/libexec/gvfsd-trash --spawner :1.22 /org/gtk/gvfs/exec_spaw/0
   4871 /usr/libexec/xdg-desktop-portal-gtk
   5174 /snap/snapd-desktop-integration/391/usr/bin/user-session-helper /snap/sn
   5239 /snap/snapd-desktop-integration/391/usr/bin/snapd-desktop-integration
   5338 /home/bolo/.local/bin/herdr server
   5355 /bin/bash
   5757 /usr/bin/fcitx5
   5760 /usr/bin/Xwayland :0 -rootless -noreset -accessx -core -auth /run/user/1
   5775 /usr/libexec/gsd-xsettings
   5783 /usr/libexec/mutter-x11-frames
   6471 /usr/bin/ssh-agent -D -a /run/user/1000/gcr/.ssh
   7716 pi
  12947 /usr/libexec/fwupd/fwupd
  27519 /bin/bash
  27535 pi
  37410 /usr/libexec/gvfsd-http --spawner :1.22 /org/gtk/gvfs/exec_spaw/1
  48391 /bin/bash
  48416 pi
  48624 catatonit -P
  56314 bwrap --unshare-all --die-with-parent --chdir / --ro-bind /usr /usr --de
  56315 bwrap --unshare-all --die-with-parent --chdir / --ro-bind /usr /usr --de
  56316 /usr/libexec/glycin-loaders/2+/glycin-image-rs --dbus-fd 220
  68539 /bin/bash
  68556 pi
  86994 /usr/sbin/cupsd -l
  86996 /usr/sbin/cups-browsed
  92607 /bin/bash
  92628 /bin/bash
  92648 pi
  92676 pi
  93427 /usr/bin/ghostty --gtk-single-instance=true --initial-window=false --she
  93470 /bin/sh -c /bin/bash --posix
  93475 /bin/bash --posix
  93492 herdr
  99250 /usr/bin/snap userd
 103702 /usr/libexec/gvfsd-network --spawner :1.22 /org/gtk/gvfs/exec_spaw/2
 103748 /usr/libexec/gvfsd-dnssd --spawner :1.22 /org/gtk/gvfs/exec_spaw/3
 103793 /usr/libexec/gvfsd-wsdd --spawner :1.22 /org/gtk/gvfs/exec_spaw/4
 103798 python3 /usr/bin/wsdd --no-host --discovery --listen /run/user/1000/gvfs
 103933 /usr/sbin/uuidd --socket-activation --cont-clock
 261481 /opt/google/chrome/chrome
 261485 cat
 261486 cat
 261488 /opt/google/chrome/chrome_crashpad_handler --monitor-self --monitor-self
 261490 /opt/google/chrome/chrome_crashpad_handler --no-periodic-tasks --monitor
 261503 /opt/google/chrome/chrome --type=zygote --no-zygote-sandbox --crashpad-h
 261504 /opt/google/chrome/chrome --type=zygote --crashpad-handler-pid=261488 --
 261506 /opt/google/chrome/chrome --type=zygote --crashpad-handler-pid=261488 --
 261541 /opt/google/chrome/chrome --type=gpu-process --ozone-platform=wayland --
 261543 /opt/google/chrome/chrome --type=utility --utility-sub-type=network.mojo
 261545 /opt/google/chrome/chrome --type=utility --utility-sub-type=storage.mojo
 261599 /opt/google/chrome/chrome --type=renderer --top-chrome-webui --crashpad-
 261648 /opt/google/chrome/chrome --type=renderer --crashpad-handler-pid=261488
 261765 /opt/google/chrome/chrome --type=renderer --crashpad-handler-pid=261488
 271841 [kworker/1:2-cgroup_release]
 316653 /bin/bash
 316682 pi
 319253 [kworker/2:0-events_long]
 319901 [kworker/5:1-memcg]
 323946 [kworker/11:0-mm_percpu_wq]
 355854 /bin/bash
 355885 pi
 358564 [kworker/3:0-memcg]
 365049 [psimon]
 367092 [kworker/0:2-events]
 367790 /usr/lib/git-core/git-daemon --enable=receive-pack --base-path=/tmp/swt-
 367799 /usr/lib/git-core/git-daemon --enable=receive-pack --base-path=/tmp/swt-
 368864 [kworker/u48:3-async]
 368865 [kworker/u48:4-events_unbound]
 389477 [kworker/9:2-events]
 399726 [kworker/u48:8-async]
 399730 [kworker/4:0-events]
 412695 [kworker/u48:2-async]
 413087 [kworker/10:1-events]
 417485 [kworker/2:2-cgroup_release]
 418342 [kworker/7:0-cgroup_free]
 423912 [kworker/8:1-events]
 428084 [kworker/11:1-mm_percpu_wq]
 430018 [kworker/u49:0-ttm]
 432710 [kworker/9:1-events]
 433492 [kworker/6:0-events]
 433873 [kworker/5:2-memcg]
 433888 [kworker/7:2-kacpi_notify]
 436654 /opt/google/chrome/chrome --type=renderer --crashpad-handler-pid=261488
 437183 [kworker/u48:5-async]
 437189 /opt/google/chrome/chrome --type=renderer --crashpad-handler-pid=261488
 438325 [kworker/2:1-events]
 439476 [kworker/1:1-events]
 439790 [kworker/4:1-events]
 439795 [kworker/3:1-memcg]
 440979 [kworker/u49:2-ttm]
 441018 [kworker/9:0-events]
 441096 [kworker/u49:3-ttm]
 441097 [kworker/u49:4-ttm]
 441426 [kworker/6:1-cgroup_release]
 441433 [kworker/10:2-events]
 441449 [kworker/u48:0-async]
 441956 [kworker/0:0-events]
 441986 [kworker/4:2-cgroup_free]
 442243 [kworker/8:0-mm_percpu_wq]
 442259 [kworker/u48:1-async]
 442273 [kworker/7:1-memcg]
 443226 [kworker/u48:6-async]
 443653 [kworker/11:2-mm_percpu_wq]
 445720 [kworker/5:0-cgroup_release]
 446506 [kworker/3:2-cgroup_release]
 450846 /bin/bash -c herdr agent send-keys m3-reviewer 'alt+\' && sleep 3 && her
 450854 herdr agent wait m3-reviewer --timeout 900000
 450855 grep -o "agent_status":"[a-z]*"
 450865 uv run --with pytest pytest tests/test_swt_m03.py
 450879 /home/bolo/.cache/uv/builds-v0/.tmpZmURCh/bin/python /home/bolo/.cache/u
 453314 [kworker/7:3]
 453426 [kworker/u48:7-async]
 453427 [kworker/u48:9-async]
 453428 [kworker/u48:10-async]
 453429 [kworker/u48:11-async]
 453430 [kworker/u48:12-async]
 453431 [kworker/u48:13-async]
 453432 [kworker/u48:14-async]
 453433 [kworker/u48:15-async]
 453434 [kworker/u48:16-async]
 453435 [kworker/u48:17-flush-259:0]
 453436 [kworker/u48:18-async]
 453437 [kworker/u48:19-async]
 453438 [kworker/11:3]
 453439 [kworker/u48:20-async]
 453440 [kworker/u48:21-async]
 453441 [kworker/u48:22-flush-259:0]
 453442 [kworker/u48:23-flush-259:0]
 453443 [kworker/u48:24-flush-259:0]
 453444 [kworker/u48:25-async]
 453445 [kworker/u48:26-async]
 453446 [kworker/u48:27-flush-259:0]
 453447 [kworker/u48:28-events_unbound]
 453448 [kworker/u48:29-ext4-rsv-conversion]
 453449 [kworker/u48:30-async]
 453450 [kworker/u48:31-async]
 453451 [kworker/u48:32-ext4-rsv-conversion]
 453452 [kworker/u48:33-async]
 453453 [kworker/u48:34]
 453454 [kworker/u48:35-ipv6_addrconf]
 453455 [kworker/9:3-events]
 453456 [kworker/1:0]
 453457 [kworker/2:3-events]
 453458 [kworker/2:4]
 453459 [kworker/2:5-events]
 454949 gjs /usr/share/gnome-shell/extensions/ding@rastersoft.com/app/ding.js -E
 455199 /opt/google/chrome/chrome --type=utility --utility-sub-type=audio.mojom.
 456011 /usr/bin/gnome-control-center --gapplication-service
 456151 /usr/libexec/nm-openvpn-service --bus-name org.freedesktop.NetworkManage
 456201 /usr/sbin/openvpn --remote oavpn-office01.changzhi.top 11944 udp --expli
 459557 [kworker/0:1-rcu_gp]
 459868 /opt/google/chrome/chrome --type=renderer --crashpad-handler-pid=261488
 460018 [kworker/8:2-events]
 460722 [kworker/6:2-events]
 460881 [kworker/u49:1]
 460887 /bin/sh -c /bin/bash --posix
 460890 /bin/bash --posix
 461174 [kworker/10:0-events]
 461513 uv run python /home/bolo/Workspace/skills/workflow/use-sandbox-worktree/
 461516 /home/bolo/.cache/uv/builds-v0/.tmpZmURCh/bin/python3 /home/bolo/Workspa
 461522 /bin/bash --posix
 461523 /usr/bin/python3 /usr/lib/command-not-found -- vim
 461524 ps -eo pid=,args=
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/srv/demo worktree add -b demo-main-feature-pi-report /tmp/swt-m03-test-2qvld9t9/mother/demo-main-feature-pi-report main
exit=0
stdout: HEAD 现在位于 b96b9d6 initial fixture
stderr: 准备工作区（新分支 'demo-main-feature-pi-report'）

$ git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --get-all receive.denyCurrentBranch
exit=1
stdout: (empty)
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --get-all receive.denyNonFastForwards
exit=1
stdout: (empty)
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --get-all receive.denyDeletes
exit=1
stdout: (empty)
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --get-all receive.hideRefs
exit=1
stdout: (empty)
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --get-all uploadpack.hideRefs
exit=1
stdout: (empty)
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config receive.denyCurrentBranch updateInstead
exit=0
stdout: (empty)
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config receive.denyNonFastForwards true
exit=0
stdout: (empty)
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config receive.denyDeletes true
exit=0
stdout: (empty)
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --add receive.hideRefs refs/heads
exit=0
stdout: (empty)
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --add receive.hideRefs '!refs/heads/demo-main-feature-pi-report'
exit=0
stdout: (empty)
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --add receive.hideRefs refs/tags
exit=0
stdout: (empty)
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --add uploadpack.hideRefs refs/heads
exit=0
stdout: (empty)
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --add uploadpack.hideRefs '!refs/heads/demo-main-feature-pi-report'
exit=0
stdout: (empty)
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --add uploadpack.hideRefs refs/tags
exit=0
stdout: (empty)
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --get-all receive.denyCurrentBranch
exit=0
stdout: updateInstead
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --get-all receive.denyNonFastForwards
exit=0
stdout: true
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --get-all receive.denyDeletes
exit=0
stdout: true
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --get-all receive.hideRefs
exit=0
stdout: refs/heads
!refs/heads/demo-main-feature-pi-report
refs/tags
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --get-all uploadpack.hideRefs
exit=0
stdout: refs/heads
!refs/heads/demo-main-feature-pi-report
refs/tags
stderr: (empty)

$ ip -o -4 addr show
exit=0
stdout: 1: lo    inet 127.0.0.1/8 scope host lo\       valid_lft forever preferred_lft forever
2: wlp1s0    inet 192.168.31.252/24 brd 192.168.31.255 scope global dynamic noprefixroute wlp1s0\       valid_lft 43123sec preferred_lft 43123sec
7: tun0    inet 192.168.216.62/21 brd 192.168.223.255 scope global noprefixroute tun0\       valid_lft forever preferred_lft forever
stderr: (empty)

$ git daemon --enable=receive-pack --base-path=/tmp/swt-m03-test-2qvld9t9/srv --listen=0.0.0.0 --port=44651 --reuseaddr --log-destination=none /tmp/swt-m03-test-2qvld9t9/srv
exit=None
stdout: (empty)
stderr: (empty)

$ daemon-probe 127.0.0.1:44651
exit=0
stdout: (empty)
stderr: (empty)

$ podman image exists localhost/swt-m03:latest
exit=0
stdout: (empty)
stderr: (empty)

$ podman create --name swt-demo-main-feature-pi-report --label sandbox-worktree.name=demo-main-feature-pi-report --label sandbox-worktree.repo=/tmp/swt-m03-test-2qvld9t9/srv/demo --label sandbox-worktree.branch=demo-main-feature-pi-report -p 22 localhost/swt-m03:latest
exit=0
stdout: 6fe45aabbed377e45b0f307092bcfad9cb70e3890384deafb29c30b2cbc9d5d8
stderr: (empty)

$ podman start swt-demo-main-feature-pi-report
exit=0
stdout: swt-demo-main-feature-pi-report
stderr: (empty)

$ podman port swt-demo-main-feature-pi-report 22
exit=0
stdout: 0.0.0.0:42329
stderr: (empty)

$ ssh-keygen -q -t ed25519 -N '' -f /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519
exit=0
stdout: (empty)
stderr: (empty)

$ podman exec -i swt-demo-main-feature-pi-report sh -c 'install -d -m 700 -o agent -g agent /home/agent/.ssh && cat > /home/agent/.ssh/authorized_keys && chown agent:agent /home/agent/.ssh/authorized_keys && chmod 600 /home/agent/.ssh/authorized_keys'
exit=0
stdout: (empty)
stderr: (empty)

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 true
exit=0
stdout: (empty)
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'rm -rf /home/agent/workspace && git clone -b demo-main-feature-pi-report git://host.containers.internal:44651/demo /home/agent/workspace'
exit=0
stdout: (empty)
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.
Cloning into '/home/agent/workspace'...

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace branch --show-current'
exit=0
stdout: demo-main-feature-pi-report
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace remote -v'
exit=0
stdout: origin	git://host.containers.internal:44651/demo (fetch)
origin	git://host.containers.internal:44651/demo (push)
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace ls-remote origin'
exit=0
stdout: b96b9d63cb4f7a121e217d66ca09bb5b48093fe4	HEAD
b96b9d63cb4f7a121e217d66ca09bb5b48093fe4	refs/heads/demo-main-feature-pi-report
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace branch -r '"'"'--format=%(refname:short)'"'"''
exit=0
stdout: origin/demo-main-feature-pi-report
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'pi --help'
exit=0
stdout: pi - AI coding assistant with read, bash, edit, write tools

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
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace config user.name swt-m03'
exit=0
stdout: (empty)
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace config user.email swt-m03@example.invalid'
exit=0
stdout: (empty)
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace status --porcelain'
exit=0
stdout: (empty)
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'printf '"'"'%s\n'"'"' '"'"'container client smoke'"'"' > /home/agent/workspace/container-client.txt && printf '"'"'%s\n'"'"' '"'"'container-client-run-1788572829712312582.txt'"'"' > /home/agent/workspace/container-client-run-1788572829712312582.txt'
exit=0
stdout: (empty)
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace add container-client.txt container-client-run-1788572829712312582.txt'
exit=0
stdout: (empty)
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace commit -m '"'"'container client push'"'"''
exit=0
stdout: [demo-main-feature-pi-report d7a67f5] container client push
 2 files changed, 2 insertions(+)
 create mode 100644 container-client-run-1788572829712312582.txt
 create mode 100644 container-client.txt
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace push origin HEAD:refs/heads/demo-main-feature-pi-report'
exit=0
stdout: (empty)
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.
To git://host.containers.internal:44651/demo
   b96b9d6..d7a67f5  HEAD -> demo-main-feature-pi-report

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'printf '"'"'%s\n'"'"' '"'"'container dirty push'"'"' > /home/agent/workspace/container-dirty.txt'
exit=0
stdout: (empty)
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace add container-dirty.txt'
exit=0
stdout: (empty)
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace commit -m '"'"'container dirty tree push'"'"''
exit=0
stdout: [demo-main-feature-pi-report fb2c6a6] container dirty tree push
 1 file changed, 1 insertion(+)
 create mode 100644 container-dirty.txt
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace push origin HEAD:refs/heads/demo-main-feature-pi-report'
exit=1
stdout: (empty)
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.
To git://host.containers.internal:44651/demo
 ! [remote rejected] HEAD -> demo-main-feature-pi-report (Working directory has unstaged changes)
error: failed to push some refs to 'git://host.containers.internal:44651/demo'

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace reset --hard origin/demo-main-feature-pi-report'
exit=0
stdout: HEAD is now at d7a67f5 container client push
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.

$ git -C /tmp/swt-m03-test-2qvld9t9/mother/demo-main-feature-pi-report checkout -- README.md
exit=0
stdout: (empty)
stderr: (empty)

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace switch -c oob-container-new-branch'
exit=0
stdout: (empty)
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.
Switched to a new branch 'oob-container-new-branch'

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace push origin HEAD:refs/heads/oob-container-new-branch'
exit=1
stdout: (empty)
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.
To git://host.containers.internal:44651/demo
 ! [remote rejected] HEAD -> oob-container-new-branch (deny updating a hidden ref)
error: failed to push some refs to 'git://host.containers.internal:44651/demo'

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace switch demo-main-feature-pi-report'
exit=0
stdout: Your branch is up to date with 'origin/demo-main-feature-pi-report'.
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.
Switched to branch 'demo-main-feature-pi-report'

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace tag oob-container-tag'
exit=0
stdout: (empty)
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace push origin refs/tags/oob-container-tag'
exit=1
stdout: (empty)
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.
To git://host.containers.internal:44651/demo
 ! [remote rejected] oob-container-tag -> oob-container-tag (deny updating a hidden ref)
error: failed to push some refs to 'git://host.containers.internal:44651/demo'

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace reset --hard HEAD^'
exit=0
stdout: HEAD is now at b96b9d6 initial fixture
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'printf '"'"'%s\n'"'"' '"'"'container non-fast-forward'"'"' > /home/agent/workspace/container-non-ff.txt'
exit=0
stdout: (empty)
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace add container-non-ff.txt'
exit=0
stdout: (empty)
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace commit -m '"'"'container non-fast-forward'"'"''
exit=0
stdout: [demo-main-feature-pi-report 70eff6a] container non-fast-forward
 1 file changed, 1 insertion(+)
 create mode 100644 container-non-ff.txt
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace push origin --force HEAD:refs/heads/demo-main-feature-pi-report'
exit=1
stdout: (empty)
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.
remote: error: denying non-fast-forward refs/heads/demo-main-feature-pi-report (you should pull first)
To git://host.containers.internal:44651/demo
 ! [remote rejected] HEAD -> demo-main-feature-pi-report (non-fast-forward)
error: failed to push some refs to 'git://host.containers.internal:44651/demo'

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace reset --hard origin/demo-main-feature-pi-report'
exit=0
stdout: HEAD is now at d7a67f5 container client push
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace push origin :refs/heads/demo-main-feature-pi-report'
exit=1
stdout: (empty)
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.
remote: error: denying ref deletion for refs/heads/demo-main-feature-pi-report
To git://host.containers.internal:44651/demo
 ! [remote rejected] demo-main-feature-pi-report (deletion prohibited)
error: failed to push some refs to 'git://host.containers.internal:44651/demo'

$ git clone -b demo-main-feature-pi-report git://127.0.0.1:44651/demo /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone
exit=0
stdout: (empty)
stderr: 正克隆到 '/tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone'...

$ git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone branch --show-current
exit=0
stdout: demo-main-feature-pi-report
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone config user.name swt-m03
exit=0
stdout: (empty)
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone config user.email swt-m03@example.invalid
exit=0
stdout: (empty)
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone add host-client.txt host-client-run-1788572834834496554.txt
exit=0
stdout: (empty)
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone commit -m 'host client push'
exit=0
stdout: [demo-main-feature-pi-report c29101e] host client push
 2 files changed, 2 insertions(+)
 create mode 100644 host-client-run-1788572834834496554.txt
 create mode 100644 host-client.txt
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone push origin HEAD:refs/heads/demo-main-feature-pi-report
exit=0
stdout: (empty)
stderr: To git://127.0.0.1:44651/demo
   d7a67f5..c29101e  HEAD -> demo-main-feature-pi-report

$ git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone switch -c oob-new-branch
exit=0
stdout: (empty)
stderr: 切换到一个新分支 'oob-new-branch'

$ git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone push git://127.0.0.1:44651/demo HEAD:refs/heads/oob-new-branch
exit=1
stdout: (empty)
stderr: To git://127.0.0.1:44651/demo
 ! [remote rejected] HEAD -> oob-new-branch (deny updating a hidden ref)
error: 无法推送一些引用到 'git://127.0.0.1:44651/demo'

$ git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone switch demo-main-feature-pi-report
exit=0
stdout: 您的分支与上游分支 'origin/demo-main-feature-pi-report' 一致。
stderr: 切换到分支 'demo-main-feature-pi-report'

$ git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone tag oob-tag
exit=0
stdout: (empty)
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone push git://127.0.0.1:44651/demo refs/tags/oob-tag
exit=1
stdout: (empty)
stderr: To git://127.0.0.1:44651/demo
 ! [remote rejected] oob-tag -> oob-tag (deny updating a hidden ref)
error: 无法推送一些引用到 'git://127.0.0.1:44651/demo'

$ git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone reset --hard 'HEAD^'
exit=0
stdout: HEAD 现在位于 d7a67f5 container client push
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone add oob-non-ff.txt
exit=0
stdout: (empty)
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone commit -m 'oob non-fast-forward'
exit=0
stdout: [demo-main-feature-pi-report b84e744] oob non-fast-forward
 1 file changed, 1 insertion(+)
 create mode 100644 oob-non-ff.txt
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone push git://127.0.0.1:44651/demo --force HEAD:refs/heads/demo-main-feature-pi-report
exit=1
stdout: (empty)
stderr: remote: error: denying non-fast-forward refs/heads/demo-main-feature-pi-report (you should pull first)
To git://127.0.0.1:44651/demo
 ! [remote rejected] HEAD -> demo-main-feature-pi-report (non-fast-forward)
error: 无法推送一些引用到 'git://127.0.0.1:44651/demo'

$ git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone push git://127.0.0.1:44651/demo :refs/heads/demo-main-feature-pi-report
exit=1
stdout: (empty)
stderr: remote: error: denying ref deletion for refs/heads/demo-main-feature-pi-report
To git://127.0.0.1:44651/demo
 ! [remote rejected] demo-main-feature-pi-report (deletion prohibited)
error: 无法推送一些引用到 'git://127.0.0.1:44651/demo'

$ pgrep -af 'git( daemon|-daemon).*/tmp/swt\-m03\-test\-2qvld9t9/srv'
exit=0
stdout: 461554 git daemon --enable=receive-pack --base-path=/tmp/swt-m03-test-2qvld9t9/srv --listen=0.0.0.0 --port=44651 --reuseaddr --log-destination=none /tmp/swt-m03-test-2qvld9t9/srv
461555 /usr/lib/git-core/git-daemon --enable=receive-pack --base-path=/tmp/swt-m03-test-2qvld9t9/srv --listen=0.0.0.0 --port=44651 --reuseaddr --log-destination=none /tmp/swt-m03-test-2qvld9t9/srv
stderr: (empty)

$ podman ps -a --filter label=sandbox-worktree.repo=/tmp/swt-m03-test-2qvld9t9/srv/demo --format '{{.Names}}'
exit=0
stdout: swt-demo-main-feature-pi-report
stderr: (empty)

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace status --porcelain=v1'
exit=0
stdout: (empty)
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.

$ ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace rev-list --count origin/demo-main-feature-pi-report..HEAD'
exit=0
stdout: 0
stderr: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.

$ podman rm -f swt-demo-main-feature-pi-report
exit=0
stdout: swt-demo-main-feature-pi-report
stderr: (empty)

$ podman ps -a --filter label=sandbox-worktree.repo=/tmp/swt-m03-test-2qvld9t9/srv/demo --format '{{.Names}}'
exit=0
stdout: (empty)
stderr: (empty)

$ kill -TERM 461554
exit=0
stdout: (empty)
stderr: (empty)

$ pgrep -af 'git( daemon|-daemon).*/tmp/swt\-m03\-test\-2qvld9t9/srv'
exit=1
stdout: (empty)
stderr: (empty)

$ pgrep -af 'git( daemon|-daemon).*/tmp/swt\-m03\-test\-2qvld9t9/srv'
exit=1
stdout: (empty)
stderr: (empty)

$ git -C /tmp/swt-m03-test-2qvld9t9/srv/demo show-ref --verify refs/heads/demo-main-feature-pi-report
exit=0
stdout: c29101ef74be54622eea0acaf53a5117190d2f91 refs/heads/demo-main-feature-pi-report
stderr: (empty)

```

## checklist

```json
{
  "command_log_history": [
    {
      "command": "uv run python /home/bolo/Workspace/skills/workflow/use-worktree/scripts/slug.py demo main feature/pi-report",
      "returncode": 0,
      "stderr": "",
      "stdout": "project=demo\nsource_branch=main\nsource_slug=main\ntarget_branch=feature/pi-report\ntarget_slug=feature-pi-report\ndir=demo-main-feature-pi-report\n"
    },
    {
      "command": "ps -eo pid=,args=",
      "returncode": 0,
      "stderr": "",
      "stdout": "      1 /usr/lib/systemd/systemd --switched-root --system --deserialize=53 splas\n      2 [kthreadd]\n      3 [pool_workqueue_release]\n      4 [kworker/R-rcu_gp]\n      5 [kworker/R-sync_wq]\n      6 [kworker/R-kvfree_rcu_reclaim]\n      7 [kworker/R-slub_flushwq]\n      8 [kworker/R-netns]\n     10 [kworker/0:0H-kblockd]\n     13 [kworker/R-mm_percpu_wq]\n     14 [ksoftirqd/0]\n     15 [rcu_preempt]\n     16 [rcu_exp_par_gp_kthread_worker/0]\n     17 [rcu_exp_gp_kthread_worker]\n     18 [migration/0]\n     19 [kprobe-optimizer]\n     20 [idle_inject/0]\n     21 [cpuhp/0]\n     22 [cpuhp/2]\n     23 [idle_inject/2]\n     24 [migration/2]\n     25 [ksoftirqd/2]\n     27 [kworker/2:0H-kblockd]\n     28 [cpuhp/4]\n     29 [idle_inject/4]\n     30 [migration/4]\n     31 [ksoftirqd/4]\n     33 [kworker/4:0H-kblockd]\n     34 [cpuhp/6]\n     35 [idle_inject/6]\n     36 [migration/6]\n     37 [ksoftirqd/6]\n     39 [kworker/6:0H-kblockd]\n     40 [cpuhp/8]\n     41 [idle_inject/8]\n     42 [migration/8]\n     43 [ksoftirqd/8]\n     45 [kworker/8:0H-kblockd]\n     46 [cpuhp/10]\n     47 [idle_inject/10]\n     48 [migration/10]\n     49 [ksoftirqd/10]\n     51 [kworker/10:0H-kblockd]\n     52 [cpuhp/1]\n     53 [idle_inject/1]\n     54 [migration/1]\n     55 [ksoftirqd/1]\n     57 [kworker/1:0H-kblockd]\n     58 [cpuhp/3]\n     59 [idle_inject/3]\n     60 [migration/3]\n     61 [ksoftirqd/3]\n     63 [kworker/3:0H-kblockd]\n     64 [cpuhp/5]\n     65 [idle_inject/5]\n     66 [migration/5]\n     67 [ksoftirqd/5]\n     69 [kworker/5:0H-kblockd]\n     70 [cpuhp/7]\n     71 [idle_inject/7]\n     72 [migration/7]\n     73 [ksoftirqd/7]\n     75 [kworker/7:0H-kblockd]\n     76 [cpuhp/9]\n     77 [idle_inject/9]\n     78 [migration/9]\n     79 [ksoftirqd/9]\n     81 [kworker/9:0H-kblockd]\n     82 [cpuhp/11]\n     83 [idle_inject/11]\n     84 [migration/11]\n     85 [ksoftirqd/11]\n     87 [kworker/11:0H-kblockd]\n     88 [kdevtmpfs]\n     89 [kworker/R-inet_frag_wq]\n     90 [rcu_tasks_kthread]\n     91 [rcu_tasks_rude_kthread]\n     92 [kauditd]\n     93 [khungtaskd]\n     94 [oom_reaper]\n     97 [kworker/R-writeback]\n     98 [kcompactd0]\n     99 [ksmd]\n    100 [khugepaged]\n    101 [kworker/R-kblockd]\n    102 [kworker/R-blkcg_punt_bio]\n    103 [kworker/R-kintegrityd]\n    104 [irq/9-acpi]\n    107 [kworker/R-tpm_dev_wq]\n    108 [kworker/R-ata_sff]\n    109 [kworker/R-md_bitmap]\n    110 [kworker/R-md_llbitmap_io]\n    111 [kworker/R-md_llbitmap_unplug]\n    112 [kworker/R-edac-poller]\n    113 [kworker/R-devfreq_wq]\n    114 [watchdogd]\n    115 [kworker/R-quota_events_unbound]\n    119 [irq/25-AMD-Vi0-Evt]\n    120 [irq/26-AMD-Vi0-PPR]\n    121 [irq/27-AMD-Vi0-GA]\n    122 [kswapd0]\n    123 [ecryptfs-kthread]\n    124 [kworker/R-kthrotld]\n    126 [kworker/R-acpi_thermal_pm]\n    127 [kworker/R-mld]\n    128 [kworker/R-ipv6_addrconf]\n    129 [kworker/R-kstrp]\n    151 [kworker/R-charger_manager]\n    152 [irq/28-ACPI:Event]\n    153 [irq/29-ACPI:Event]\n    154 [irq/30-ACPI:Event]\n    155 [irq/31-ACPI:Event]\n    156 [irq/32-ACPI:Event]\n    157 [irq/33-ACPI:Event]\n    158 [irq/34-ACPI:Event]\n    368 [irq/60-ITE8227:00]\n    369 [irq/58-MSFT0001:00]\n    378 [kworker/R-nvme-wq]\n    379 [kworker/R-nvme-reset-wq]\n    380 [kworker/R-nvme-delete-wq]\n    381 [kworker/R-nvme-auth-wq]\n    396 [kworker/10:1H-kblockd]\n    397 [kworker/3:1H-kblockd]\n    410 [kworker/2:1H-kblockd]\n    413 [jbd2/nvme0n1p2-8]\n    414 [kworker/R-ext4-rsv-conversion]\n    468 [kworker/R-USBC000:00-con1]\n    476 /usr/lib/systemd/systemd-journald\n    521 [kworker/4:1H-kblockd]\n    522 [kworker/8:1H-kblockd]\n    523 [kworker/6:1H-kblockd]\n    524 /usr/lib/systemd/systemd-resolved\n    525 [kworker/5:1H-kblockd]\n    528 /usr/lib/systemd/systemd-oomd\n    531 /usr/lib/systemd/systemd-udevd\n    536 [psimon]\n    581 [kworker/9:1H-kblockd]\n    605 [kworker/R-cfg80211]\n    839 [kworker/0:1H-kblockd]\n    841 [kworker/1:1H-kblockd]\n    855 [kworker/7:1H-kblockd]\n    857 [kworker/11:1H-kblockd]\n    859 [irq/80-rtw89_pci]\n   1288 avahi-daemon: running [bolo-Yoga.local]\n   1289 /usr/libexec/bluetooth/bluetoothd\n   1291 /bin/sh /usr/lib/systemd/scripts/chronyd-starter.sh -n -F 1\n   1292 @dbus-daemon --system --address=systemd: --nofork --nopidfile --systemd-\n   1298 /usr/libexec/iio-sensor-proxy\n   1301 /usr/bin/python3 /usr/bin/networkd-dispatcher --run-startup-triggers\n   1303 /usr/lib/polkit-1/polkitd --no-debug --log-level=notice\n   1312 /usr/lib/snapd/snapd\n   1315 /usr/libexec/accounts-daemon\n   1330 /usr/sbin/cron -f -P\n   1333 /usr/libexec/switcheroo-control\n   1336 /usr/lib/systemd/systemd-logind\n   1338 /usr/libexec/udisks2/udisksd\n   1375 avahi-daemon: chroot helper\n   1399 /usr/sbin/rsyslogd -n -iNONE\n   1415 /usr/sbin/NetworkManager --no-daemon\n   1431 /usr/sbin/chronyd -n -F 1\n   1432 /usr/sbin/wpa_supplicant -u -s -O DIR=/run/wpa_supplicant GROUP=netdev\n   1443 /usr/sbin/chronyd -n -F 1\n   1496 /usr/sbin/ModemManager\n   1591 /usr/bin/python3 /usr/share/unattended-upgrades/unattended-upgrade-shutd\n   1602 sshd: /usr/sbin/sshd -D [listener] 0 of 10-100 startups\n   1617 /usr/sbin/gdm3\n   1644 [kworker/R-USBC000:00-con2]\n   1653 [kworker/R-amdgpu-reset-dev]\n   1671 [kworker/R-ttm]\n   1699 [kworker/R-amdgpu_dm_hpd_rx_offload_wq]\n   1700 [kworker/R-amdgpu_dm_hpd_rx_offload_wq]\n   1701 [kworker/R-amdgpu_dm_hpd_rx_offload_wq]\n   1702 [kworker/R-dm_vblank_control_workqueue]\n   1703 [card1-crtc0]\n   1704 [card1-crtc1]\n   1705 [card1-crtc2]\n   1706 [card1-crtc3]\n   1707 [kworker/R-gfx]\n   1708 [kworker/R-comp_1.0.0]\n   1709 [kworker/R-comp_1.1.0]\n   1710 [kworker/R-comp_1.2.0]\n   1711 [kworker/R-comp_1.3.0]\n   1712 [kworker/R-comp_1.0.1]\n   1713 [kworker/R-comp_1.1.1]\n   1714 [kworker/R-comp_1.2.1]\n   1715 [kworker/R-comp_1.3.1]\n   1716 [kworker/R-sdma0]\n   1717 [kworker/R-vcn_dec]\n   1718 [kworker/R-vcn_enc0]\n   1719 [kworker/R-vcn_enc1]\n   1720 [kworker/R-jpeg_dec]\n   2097 /usr/libexec/rtkit-daemon\n   2225 [krfcommd]\n   2333 /usr/libexec/colord\n   2370 /usr/libexec/upowerd\n   3238 /usr/libexec/power-profiles-daemon\n   3373 gdm-session-worker [pam/gdm-password]\n   3554 /usr/lib/systemd/systemd --user\n   3579 (sd-pam)\n   3609 /usr/bin/dbus-daemon --session --address=systemd: --nofork --nopidfile -\n   3610 /usr/bin/pipewire\n   3614 /usr/bin/gnome-keyring-daemon --foreground --components=pkcs11,secrets -\n   3628 /usr/bin/mpris-proxy\n   3630 /usr/bin/wireplumber\n   3632 /usr/bin/pipewire -c filter-chain.conf\n   3634 /usr/bin/pipewire-pulse\n   3713 /usr/libexec/xdg-document-portal\n   3717 /usr/libexec/xdg-permission-store\n   3724 fusermount3 -o rw,nosuid,nodev,fsname=portal,auto_unmount,subtype=portal\n   3751 /usr/libexec/gdm-wayland-session /usr/bin/gnome-session --session=ubuntu\n   3763 /usr/libexec/gnome-session-init-worker ubuntu\n   3974 /usr/libexec/gcr-ssh-agent --base-dir /run/user/1000/gcr\n   3975 /usr/libexec/gnome-remote-desktop-daemon\n   3976 /usr/libexec/gnome-session-ctl --monitor\n   3977 /usr/bin/ssh-agent -D\n   3992 /usr/libexec/gvfsd\n   4007 /usr/libexec/gvfsd-fuse /run/user/1000/gvfs -f\n   4010 /usr/libexec/gnome-session-service --session=ubuntu\n   4046 /usr/bin/gnome-shell --mode=ubuntu\n   4122 /usr/libexec/at-spi-bus-launcher\n   4129 /usr/bin/dbus-daemon --config-file=/usr/share/defaults/at-spi2/accessibi\n   4131 /usr/libexec/at-spi2-registryd --use-gnome-session\n   4154 /usr/libexec/gnome-shell-calendar-server\n   4161 /usr/libexec/evolution-source-registry\n   4173 /usr/bin/gjs -m /usr/share/gnome-shell/org.gnome.Shell.Notifications\n   4193 /usr/libexec/gsd-a11y-settings\n   4195 /usr/libexec/gsd-color\n   4197 /usr/libexec/gsd-datetime\n   4198 /usr/libexec/gsd-housekeeping\n   4199 /usr/libexec/gsd-keyboard\n   4203 /usr/libexec/gsd-media-keys\n   4205 /usr/libexec/gsd-power\n   4209 /usr/libexec/gsd-print-notifications\n   4215 /usr/libexec/gsd-rfkill\n   4217 /usr/libexec/gsd-screensaver-proxy\n   4218 /usr/libexec/gsd-sharing\n   4228 /usr/libexec/gsd-smartcard\n   4232 /usr/libexec/gsd-sound\n   4233 /usr/libexec/gsd-usb-protection\n   4237 /usr/libexec/gsd-disk-utility-notify\n   4243 /usr/libexec/gsd-wwan\n   4245 /usr/libexec/evolution-data-server/evolution-alarm-notify\n   4273 /usr/bin/update-notifier\n   4281 /usr/libexec/goa-daemon\n   4346 /usr/bin/gjs -m /usr/share/gnome-shell/org.gnome.ScreenSaver\n   4371 /usr/libexec/gsd-printer\n   4375 /usr/libexec/goa-identity-service\n   4402 /usr/libexec/evolution-calendar-factory\n   4444 /usr/libexec/evolution-addressbook-factory\n   4445 /usr/libexec/localsearch-3\n   4450 /usr/libexec/xdg-desktop-portal\n   4475 /usr/libexec/xdg-desktop-portal-gnome\n   4488 /usr/libexec/gvfs-udisks2-volume-monitor\n   4501 /usr/libexec/gvfs-gphoto2-volume-monitor\n   4506 /usr/libexec/gvfs-goa-volume-monitor\n   4511 /usr/libexec/gvfs-mtp-volume-monitor\n   4516 /usr/libexec/gvfs-afc-volume-monitor\n   4578 /usr/libexec/gvfsd-metadata\n   4753 /usr/libexec/dconf-service\n   4837 /usr/libexec/gvfsd-trash --spawner :1.22 /org/gtk/gvfs/exec_spaw/0\n   4871 /usr/libexec/xdg-desktop-portal-gtk\n   5174 /snap/snapd-desktop-integration/391/usr/bin/user-session-helper /snap/sn\n   5239 /snap/snapd-desktop-integration/391/usr/bin/snapd-desktop-integration\n   5338 /home/bolo/.local/bin/herdr server\n   5355 /bin/bash\n   5757 /usr/bin/fcitx5\n   5760 /usr/bin/Xwayland :0 -rootless -noreset -accessx -core -auth /run/user/1\n   5775 /usr/libexec/gsd-xsettings\n   5783 /usr/libexec/mutter-x11-frames\n   6471 /usr/bin/ssh-agent -D -a /run/user/1000/gcr/.ssh\n   7716 pi\n  12947 /usr/libexec/fwupd/fwupd\n  27519 /bin/bash\n  27535 pi\n  37410 /usr/libexec/gvfsd-http --spawner :1.22 /org/gtk/gvfs/exec_spaw/1\n  48391 /bin/bash\n  48416 pi\n  48624 catatonit -P\n  56314 bwrap --unshare-all --die-with-parent --chdir / --ro-bind /usr /usr --de\n  56315 bwrap --unshare-all --die-with-parent --chdir / --ro-bind /usr /usr --de\n  56316 /usr/libexec/glycin-loaders/2+/glycin-image-rs --dbus-fd 220\n  68539 /bin/bash\n  68556 pi\n  86994 /usr/sbin/cupsd -l\n  86996 /usr/sbin/cups-browsed\n  92607 /bin/bash\n  92628 /bin/bash\n  92648 pi\n  92676 pi\n  93427 /usr/bin/ghostty --gtk-single-instance=true --initial-window=false --she\n  93470 /bin/sh -c /bin/bash --posix\n  93475 /bin/bash --posix\n  93492 herdr\n  99250 /usr/bin/snap userd\n 103702 /usr/libexec/gvfsd-network --spawner :1.22 /org/gtk/gvfs/exec_spaw/2\n 103748 /usr/libexec/gvfsd-dnssd --spawner :1.22 /org/gtk/gvfs/exec_spaw/3\n 103793 /usr/libexec/gvfsd-wsdd --spawner :1.22 /org/gtk/gvfs/exec_spaw/4\n 103798 python3 /usr/bin/wsdd --no-host --discovery --listen /run/user/1000/gvfs\n 103933 /usr/sbin/uuidd --socket-activation --cont-clock\n 261481 /opt/google/chrome/chrome\n 261485 cat\n 261486 cat\n 261488 /opt/google/chrome/chrome_crashpad_handler --monitor-self --monitor-self\n 261490 /opt/google/chrome/chrome_crashpad_handler --no-periodic-tasks --monitor\n 261503 /opt/google/chrome/chrome --type=zygote --no-zygote-sandbox --crashpad-h\n 261504 /opt/google/chrome/chrome --type=zygote --crashpad-handler-pid=261488 --\n 261506 /opt/google/chrome/chrome --type=zygote --crashpad-handler-pid=261488 --\n 261541 /opt/google/chrome/chrome --type=gpu-process --ozone-platform=wayland --\n 261543 /opt/google/chrome/chrome --type=utility --utility-sub-type=network.mojo\n 261545 /opt/google/chrome/chrome --type=utility --utility-sub-type=storage.mojo\n 261599 /opt/google/chrome/chrome --type=renderer --top-chrome-webui --crashpad-\n 261648 /opt/google/chrome/chrome --type=renderer --crashpad-handler-pid=261488 \n 261765 /opt/google/chrome/chrome --type=renderer --crashpad-handler-pid=261488 \n 271841 [kworker/1:2-cgroup_release]\n 316653 /bin/bash\n 316682 pi\n 319253 [kworker/2:0-events_long]\n 319901 [kworker/5:1-memcg]\n 323946 [kworker/11:0-mm_percpu_wq]\n 355854 /bin/bash\n 355885 pi\n 358564 [kworker/3:0-memcg]\n 365049 [psimon]\n 367092 [kworker/0:2-events]\n 367790 /usr/lib/git-core/git-daemon --enable=receive-pack --base-path=/tmp/swt-\n 367799 /usr/lib/git-core/git-daemon --enable=receive-pack --base-path=/tmp/swt-\n 368864 [kworker/u48:3-async]\n 368865 [kworker/u48:4-events_unbound]\n 389477 [kworker/9:2-events]\n 399726 [kworker/u48:8-async]\n 399730 [kworker/4:0-events]\n 412695 [kworker/u48:2-async]\n 413087 [kworker/10:1-events]\n 417485 [kworker/2:2-cgroup_release]\n 418342 [kworker/7:0-cgroup_free]\n 423912 [kworker/8:1-events]\n 428084 [kworker/11:1-mm_percpu_wq]\n 430018 [kworker/u49:0-ttm]\n 432710 [kworker/9:1-events]\n 433492 [kworker/6:0-events]\n 433873 [kworker/5:2-memcg]\n 433888 [kworker/7:2-kacpi_notify]\n 436654 /opt/google/chrome/chrome --type=renderer --crashpad-handler-pid=261488 \n 437183 [kworker/u48:5-async]\n 437189 /opt/google/chrome/chrome --type=renderer --crashpad-handler-pid=261488 \n 438325 [kworker/2:1-events]\n 439476 [kworker/1:1-events]\n 439790 [kworker/4:1-events]\n 439795 [kworker/3:1-memcg]\n 440979 [kworker/u49:2-ttm]\n 441018 [kworker/9:0-events]\n 441096 [kworker/u49:3-ttm]\n 441097 [kworker/u49:4-ttm]\n 441426 [kworker/6:1-cgroup_release]\n 441433 [kworker/10:2-events]\n 441449 [kworker/u48:0-async]\n 441956 [kworker/0:0-events]\n 441986 [kworker/4:2-cgroup_free]\n 442243 [kworker/8:0-mm_percpu_wq]\n 442259 [kworker/u48:1-async]\n 442273 [kworker/7:1-memcg]\n 443226 [kworker/u48:6-async]\n 443653 [kworker/11:2-mm_percpu_wq]\n 445720 [kworker/5:0-cgroup_release]\n 446506 [kworker/3:2-cgroup_release]\n 450846 /bin/bash -c herdr agent send-keys m3-reviewer 'alt+\\' && sleep 3 && her\n 450854 herdr agent wait m3-reviewer --timeout 900000\n 450855 grep -o \"agent_status\":\"[a-z]*\"\n 450865 uv run --with pytest pytest tests/test_swt_m03.py\n 450879 /home/bolo/.cache/uv/builds-v0/.tmpZmURCh/bin/python /home/bolo/.cache/u\n 453314 [kworker/7:3]\n 453426 [kworker/u48:7-async]\n 453427 [kworker/u48:9-async]\n 453428 [kworker/u48:10-async]\n 453429 [kworker/u48:11-async]\n 453430 [kworker/u48:12-async]\n 453431 [kworker/u48:13-async]\n 453432 [kworker/u48:14-async]\n 453433 [kworker/u48:15-async]\n 453434 [kworker/u48:16-async]\n 453435 [kworker/u48:17-flush-259:0]\n 453436 [kworker/u48:18-async]\n 453437 [kworker/u48:19-async]\n 453438 [kworker/11:3]\n 453439 [kworker/u48:20-async]\n 453440 [kworker/u48:21-async]\n 453441 [kworker/u48:22-flush-259:0]\n 453442 [kworker/u48:23-flush-259:0]\n 453443 [kworker/u48:24-flush-259:0]\n 453444 [kworker/u48:25-async]\n 453445 [kworker/u48:26-async]\n 453446 [kworker/u48:27-flush-259:0]\n 453447 [kworker/u48:28-events_unbound]\n 453448 [kworker/u48:29-ext4-rsv-conversion]\n 453449 [kworker/u48:30-async]\n 453450 [kworker/u48:31-async]\n 453451 [kworker/u48:32-ext4-rsv-conversion]\n 453452 [kworker/u48:33-async]\n 453453 [kworker/u48:34]\n 453454 [kworker/u48:35-ipv6_addrconf]\n 453455 [kworker/9:3-events]\n 453456 [kworker/1:0]\n 453457 [kworker/2:3-events]\n 453458 [kworker/2:4]\n 453459 [kworker/2:5-events]\n 454949 gjs /usr/share/gnome-shell/extensions/ding@rastersoft.com/app/ding.js -E\n 455199 /opt/google/chrome/chrome --type=utility --utility-sub-type=audio.mojom.\n 456011 /usr/bin/gnome-control-center --gapplication-service\n 456151 /usr/libexec/nm-openvpn-service --bus-name org.freedesktop.NetworkManage\n 456201 /usr/sbin/openvpn --remote oavpn-office01.changzhi.top 11944 udp --expli\n 459557 [kworker/0:1-rcu_gp]\n 459868 /opt/google/chrome/chrome --type=renderer --crashpad-handler-pid=261488 \n 460018 [kworker/8:2-events]\n 460722 [kworker/6:2-events]\n 460881 [kworker/u49:1]\n 460887 /bin/sh -c /bin/bash --posix\n 460890 /bin/bash --posix\n 461174 [kworker/10:0-events]\n 461513 uv run python /home/bolo/Workspace/skills/workflow/use-sandbox-worktree/\n 461516 /home/bolo/.cache/uv/builds-v0/.tmpZmURCh/bin/python3 /home/bolo/Workspa\n 461522 /bin/bash --posix\n 461523 /usr/bin/python3 /usr/lib/command-not-found -- vim\n 461524 ps -eo pid=,args=\n"
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/srv/demo worktree add -b demo-main-feature-pi-report /tmp/swt-m03-test-2qvld9t9/mother/demo-main-feature-pi-report main",
      "returncode": 0,
      "stderr": "准备工作区（新分支 'demo-main-feature-pi-report'）\n",
      "stdout": "HEAD 现在位于 b96b9d6 initial fixture\n"
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --get-all receive.denyCurrentBranch",
      "returncode": 1,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --get-all receive.denyNonFastForwards",
      "returncode": 1,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --get-all receive.denyDeletes",
      "returncode": 1,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --get-all receive.hideRefs",
      "returncode": 1,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --get-all uploadpack.hideRefs",
      "returncode": 1,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config receive.denyCurrentBranch updateInstead",
      "returncode": 0,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config receive.denyNonFastForwards true",
      "returncode": 0,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config receive.denyDeletes true",
      "returncode": 0,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --add receive.hideRefs refs/heads",
      "returncode": 0,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --add receive.hideRefs '!refs/heads/demo-main-feature-pi-report'",
      "returncode": 0,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --add receive.hideRefs refs/tags",
      "returncode": 0,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --add uploadpack.hideRefs refs/heads",
      "returncode": 0,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --add uploadpack.hideRefs '!refs/heads/demo-main-feature-pi-report'",
      "returncode": 0,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --add uploadpack.hideRefs refs/tags",
      "returncode": 0,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --get-all receive.denyCurrentBranch",
      "returncode": 0,
      "stderr": "",
      "stdout": "updateInstead\n"
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --get-all receive.denyNonFastForwards",
      "returncode": 0,
      "stderr": "",
      "stdout": "true\n"
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --get-all receive.denyDeletes",
      "returncode": 0,
      "stderr": "",
      "stdout": "true\n"
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --get-all receive.hideRefs",
      "returncode": 0,
      "stderr": "",
      "stdout": "refs/heads\n!refs/heads/demo-main-feature-pi-report\nrefs/tags\n"
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/srv/demo config --get-all uploadpack.hideRefs",
      "returncode": 0,
      "stderr": "",
      "stdout": "refs/heads\n!refs/heads/demo-main-feature-pi-report\nrefs/tags\n"
    },
    {
      "command": "ip -o -4 addr show",
      "returncode": 0,
      "stderr": "",
      "stdout": "1: lo    inet 127.0.0.1/8 scope host lo\\       valid_lft forever preferred_lft forever\n2: wlp1s0    inet 192.168.31.252/24 brd 192.168.31.255 scope global dynamic noprefixroute wlp1s0\\       valid_lft 43123sec preferred_lft 43123sec\n7: tun0    inet 192.168.216.62/21 brd 192.168.223.255 scope global noprefixroute tun0\\       valid_lft forever preferred_lft forever\n"
    },
    {
      "command": "git daemon --enable=receive-pack --base-path=/tmp/swt-m03-test-2qvld9t9/srv --listen=0.0.0.0 --port=44651 --reuseaddr --log-destination=none /tmp/swt-m03-test-2qvld9t9/srv",
      "returncode": null,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "daemon-probe 127.0.0.1:44651",
      "returncode": 0,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "podman image exists localhost/swt-m03:latest",
      "returncode": 0,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "podman create --name swt-demo-main-feature-pi-report --label sandbox-worktree.name=demo-main-feature-pi-report --label sandbox-worktree.repo=/tmp/swt-m03-test-2qvld9t9/srv/demo --label sandbox-worktree.branch=demo-main-feature-pi-report -p 22 localhost/swt-m03:latest",
      "returncode": 0,
      "stderr": "",
      "stdout": "6fe45aabbed377e45b0f307092bcfad9cb70e3890384deafb29c30b2cbc9d5d8\n"
    },
    {
      "command": "podman start swt-demo-main-feature-pi-report",
      "returncode": 0,
      "stderr": "",
      "stdout": "swt-demo-main-feature-pi-report\n"
    },
    {
      "command": "podman port swt-demo-main-feature-pi-report 22",
      "returncode": 0,
      "stderr": "",
      "stdout": "0.0.0.0:42329\n"
    },
    {
      "command": "ssh-keygen -q -t ed25519 -N '' -f /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519",
      "returncode": 0,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "podman exec -i swt-demo-main-feature-pi-report sh -c 'install -d -m 700 -o agent -g agent /home/agent/.ssh && cat > /home/agent/.ssh/authorized_keys && chown agent:agent /home/agent/.ssh/authorized_keys && chmod 600 /home/agent/.ssh/authorized_keys'",
      "returncode": 0,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 true",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\n",
      "stdout": ""
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'rm -rf /home/agent/workspace && git clone -b demo-main-feature-pi-report git://host.containers.internal:44651/demo /home/agent/workspace'",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\nCloning into '/home/agent/workspace'...\n",
      "stdout": ""
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace branch --show-current'",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\n",
      "stdout": "demo-main-feature-pi-report\n"
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace remote -v'",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\n",
      "stdout": "origin\tgit://host.containers.internal:44651/demo (fetch)\norigin\tgit://host.containers.internal:44651/demo (push)\n"
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace ls-remote origin'",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\n",
      "stdout": "b96b9d63cb4f7a121e217d66ca09bb5b48093fe4\tHEAD\nb96b9d63cb4f7a121e217d66ca09bb5b48093fe4\trefs/heads/demo-main-feature-pi-report\n"
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace branch -r '\"'\"'--format=%(refname:short)'\"'\"''",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\n",
      "stdout": "origin/demo-main-feature-pi-report\n"
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'pi --help'",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\n",
      "stdout": "pi - AI coding assistant with read, bash, edit, write tools\n\nUsage:\n  pi [options] [--] [@files...] [messages...]\n\nCommands:\n  pi install <source> [-l]     Install extension source and add to settings\n  pi remove <source> [-l]      Remove extension source from settings\n  pi uninstall <source> [-l]   Alias for remove\n  pi update [source|self|pi]   Update pi, extensions, or model catalogs\n  pi list                      List installed extensions from settings\n  pi config [-l]               Open TUI to enable/disable package resources (Tab switches scope)\n  pi auth <command>            Print credentials or check provider readiness\n  pi <command> --help          Show help for install/remove/uninstall/update/list/config/auth\n\nOptions:\n  --provider <name>              Provider name (default: google)\n  --model <pattern>              Model pattern or ID (supports \"provider/id\" and optional \":<thinking>\")\n  --api-key <key>                API key (defaults to env vars)\n  --system-prompt <text>         System prompt (default: coding assistant prompt)\n  --append-system-prompt <text>  Append text or file contents to the system prompt (can be used multiple times)\n  --mode <mode>                  Output mode: text (default), json, or rpc\n  --print, -p                    Non-interactive mode: process prompt and exit\n  --continue, -c                 Continue previous session\n  --resume, -r                   Select a session to resume\n  --session <path|id>            Use specific session file or partial UUID\n  --session-id <id>              Use exact project session ID, creating it if missing\n  --fork <path|id>               Fork specific session file or partial UUID into a new session\n  --session-dir <dir>            Directory for session storage and lookup\n  --no-session                   Don't save session (ephemeral)\n  --name, -n <name>              Set session display name\n  --models <patterns>            Comma-separated model patterns for Ctrl+P cycling\n                                 Supports globs (anthropic/*, *sonnet*) and fuzzy matching\n  --no-tools, -nt                Disable all tools by default (built-in and extension)\n  --no-builtin-tools, -nbt       Disable built-in tools by default but keep extension/custom tools enabled\n  --tools, -t <tools>            Comma-separated allowlist of tool names to enable\n                                 Applies to built-in, extension, and custom tools\n  --exclude-tools, -xt <tools>   Comma-separated denylist of tool names to disable\n                                 Applies to built-in, extension, and custom tools\n  --thinking <level>             Set thinking level: off, minimal, low, medium, high, xhigh, max\n  --extension, -e <path>         Load an extension file (can be used multiple times)\n  --no-extensions, -ne           Disable extension discovery (explicit -e paths still work)\n  --skill <path>                 Load a skill file or directory (can be used multiple times)\n  --no-skills, -ns               Disable skills discovery and loading\n  --prompt-template <path>       Load a prompt template file or directory (can be used multiple times)\n  --no-prompt-templates, -np     Disable prompt template discovery and loading\n  --theme <path>                 Load a theme file or directory (can be used multiple times)\n  --use-theme <name[/name]>      Set the initial interactive theme for this run\n  --no-themes                    Disable theme discovery and loading\n  --no-context-files, -nc        Disable AGENTS.md and CLAUDE.md discovery and loading\n  --export <file>                Export session file to HTML and exit\n  --list-models [search]         List available models (with optional fuzzy search)\n  --verbose                      Force verbose startup (overrides quietStartup setting)\n  --tui-mode <mode>              TUI mode: regular (default) or fullscreen\n  --approve, -a                  Trust project-local files for this run\n  --no-approve, -na              Ignore project-local files for this run\n  --offline                      Disable startup network operations (same as PI_OFFLINE=1)\n  --                             End option parsing; treat remaining arguments as messages/files\n  --help, -h                     Show this help\n  --version, -v                  Show version number\n\nExtensions can register additional flags (e.g., --plan from plan-mode extension).\n\nExamples:\n  # Print a provider API key for an external client\n  pi auth print-api-key --provider openai\n\n  # Print an OAuth bearer token for an external client (refreshes if expired)\n  pi auth print-bearer-token --provider openai-codex\n\n  # Interactive mode\n  pi\n\n  # Interactive mode with initial prompt\n  pi \"List all .ts files in src/\"\n\n  # Include files in initial message\n  pi @prompt.md @image.png \"What color is the sky?\"\n\n  # Non-interactive mode (process and exit)\n  pi -p \"List all .ts files in src/\"\n\n  # Prompt beginning with a dash\n  pi -p -- \"- Summarize these points\"\n\n  # Multiple messages (interactive)\n  pi \"Read package.json\" \"What dependencies do we have?\"\n\n  # Continue previous session\n  pi --continue \"What did we discuss?\"\n\n  # Start a named session\n  pi --name \"Refactor auth module\"\n\n  # Use different model\n  pi --provider openai --model gpt-4o-mini \"Help me refactor this code\"\n\n  # Use model with provider prefix (no --provider needed)\n  pi --model openai/gpt-4o \"Help me refactor this code\"\n\n  # Use model with thinking level shorthand\n  pi --model sonnet:high \"Solve this complex problem\"\n\n  # Limit model cycling to specific models\n  pi --models claude-sonnet,claude-haiku,gpt-4o\n\n  # Limit to a specific provider with glob pattern\n  pi --models \"github-copilot/*\"\n\n  # Cycle models with fixed thinking levels\n  pi --models sonnet:high,haiku:low\n\n  # Start with a specific thinking level\n  pi --thinking high \"Solve this complex problem\"\n\n  # Read-only mode (no file modifications possible)\n  pi --tools read,grep,find,ls -p \"Review the code in src/\"\n\n  # Disable one tool while keeping the rest available\n  pi --exclude-tools ask_question\n\n  # Export a session file to HTML\n  pi --export ~/.pi/agent/sessions/--path--/session.jsonl\n  pi --export session.jsonl output.html\n\nEnvironment Variables:\n  ANTHROPIC_AUTH_TOKEN             - Anthropic bearer auth token\n  ANTHROPIC_API_KEY                - Anthropic Claude API key\n  ANTHROPIC_OAUTH_TOKEN            - Anthropic OAuth token (alternative to API key)\n  ANT_LING_API_KEY                 - Ant Ling API key\n  OPENAI_API_KEY                   - OpenAI GPT API key\n  AZURE_OPENAI_API_KEY             - Azure OpenAI API key\n  AZURE_OPENAI_BASE_URL            - Azure OpenAI/Cognitive Services base URL (e.g. https://{resource}.openai.azure.com)\n  AZURE_OPENAI_RESOURCE_NAME       - Azure OpenAI resource name (alternative to base URL)\n  AZURE_OPENAI_API_VERSION         - Azure OpenAI API version (default: v1)\n  AZURE_OPENAI_DEPLOYMENT_NAME_MAP - Azure OpenAI model=deployment map (comma-separated)\n  DEEPSEEK_API_KEY                 - DeepSeek API key\n  NVIDIA_API_KEY                   - NVIDIA NIM API key\n  GEMINI_API_KEY                   - Google Gemini API key\n  GROQ_API_KEY                     - Groq API key\n  CEREBRAS_API_KEY                 - Cerebras API key\n  XAI_API_KEY                      - xAI Grok API key\n  FIREWORKS_API_KEY                - Fireworks API key\n  TOGETHER_API_KEY                 - Together AI API key\n  BASETEN_API_KEY                  - Baseten API key\n  OPENROUTER_API_KEY               - OpenRouter API key\n  AI_GATEWAY_API_KEY               - Vercel AI Gateway API key\n  ZAI_API_KEY                      - ZAI Coding Plan API key (Global)\n  ZAI_CODING_CN_API_KEY            - ZAI Coding Plan API key (China)\n  MISTRAL_API_KEY                  - Mistral API key\n  MINIMAX_API_KEY                  - MiniMax API key\n  MOONSHOT_API_KEY                 - Moonshot AI API key\n  OPENCODE_API_KEY                 - OpenCode Zen/OpenCode Go API key\n  KIMI_API_KEY                     - Kimi For Coding API key\n  CLOUDFLARE_API_KEY               - Cloudflare API token (Workers AI and AI Gateway)\n  CLOUDFLARE_ACCOUNT_ID            - Cloudflare account id (required for both)\n  CLOUDFLARE_GATEWAY_ID            - Cloudflare AI Gateway slug (required for AI Gateway)\n  QWEN_TOKEN_PLAN_API_KEY          - Qwen Token Plan API key (international region)\n  QWEN_TOKEN_PLAN_CN_API_KEY       - Qwen Token Plan API key (China region)\n  XIAOMI_API_KEY                   - Xiaomi MiMo API key (api.xiaomimimo.com billing)\n  XIAOMI_TOKEN_PLAN_CN_API_KEY     - Xiaomi MiMo Token Plan API key (China region)\n  XIAOMI_TOKEN_PLAN_AMS_API_KEY    - Xiaomi MiMo Token Plan API key (Amsterdam region)\n  XIAOMI_TOKEN_PLAN_SGP_API_KEY    - Xiaomi MiMo Token Plan API key (Singapore region)\n  AWS_PROFILE                      - AWS profile for Amazon Bedrock\n  AWS_ACCESS_KEY_ID                - AWS access key for Amazon Bedrock\n  AWS_SECRET_ACCESS_KEY            - AWS secret key for Amazon Bedrock\n  AWS_BEARER_TOKEN_BEDROCK         - Bedrock API key (bearer token)\n  AWS_REGION                       - AWS region for Amazon Bedrock (e.g., us-east-1)\n  PI_CODING_AGENT_DIR              - Config directory (default: ~/.pi/agent)\n  PI_CODING_AGENT_SESSION_DIR      - Session storage directory (overridden by --session-dir)\n  PI_PACKAGE_DIR                   - Override package directory (for Nix/Guix store paths)\n  PI_OFFLINE                       - Disable startup network operations when set to 1/true/yes\n  PI_TELEMETRY                     - Override install telemetry when set to 1/true/yes or 0/false/no\n  PI_SHARE_VIEWER_URL              - Base URL for /share command (default: https://pi.dev/session/)\n\nBuilt-in Tool Names:\n  read       - Read file contents\n  bash       - Execute bash commands\n  powershell - Execute PowerShell commands on Windows\n  edit       - Edit files with find/replace\n  write      - Write files (creates/overwrites)\n  grep       - Search file contents (read-only, off by default)\n  find       - Find files by glob pattern (read-only, off by default)\n  ls         - List directory contents (read-only, off by default)\n\n"
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace config user.name swt-m03'",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\n",
      "stdout": ""
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace config user.email swt-m03@example.invalid'",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\n",
      "stdout": ""
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace status --porcelain'",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\n",
      "stdout": ""
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'printf '\"'\"'%s\\n'\"'\"' '\"'\"'container client smoke'\"'\"' > /home/agent/workspace/container-client.txt && printf '\"'\"'%s\\n'\"'\"' '\"'\"'container-client-run-1788572829712312582.txt'\"'\"' > /home/agent/workspace/container-client-run-1788572829712312582.txt'",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\n",
      "stdout": ""
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace add container-client.txt container-client-run-1788572829712312582.txt'",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\n",
      "stdout": ""
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace commit -m '\"'\"'container client push'\"'\"''",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\n",
      "stdout": "[demo-main-feature-pi-report d7a67f5] container client push\n 2 files changed, 2 insertions(+)\n create mode 100644 container-client-run-1788572829712312582.txt\n create mode 100644 container-client.txt\n"
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace push origin HEAD:refs/heads/demo-main-feature-pi-report'",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\nTo git://host.containers.internal:44651/demo\n   b96b9d6..d7a67f5  HEAD -> demo-main-feature-pi-report\n",
      "stdout": ""
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'printf '\"'\"'%s\\n'\"'\"' '\"'\"'container dirty push'\"'\"' > /home/agent/workspace/container-dirty.txt'",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\n",
      "stdout": ""
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace add container-dirty.txt'",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\n",
      "stdout": ""
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace commit -m '\"'\"'container dirty tree push'\"'\"''",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\n",
      "stdout": "[demo-main-feature-pi-report fb2c6a6] container dirty tree push\n 1 file changed, 1 insertion(+)\n create mode 100644 container-dirty.txt\n"
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace push origin HEAD:refs/heads/demo-main-feature-pi-report'",
      "returncode": 1,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\nTo git://host.containers.internal:44651/demo\n ! [remote rejected] HEAD -> demo-main-feature-pi-report (Working directory has unstaged changes)\nerror: failed to push some refs to 'git://host.containers.internal:44651/demo'\n",
      "stdout": ""
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace reset --hard origin/demo-main-feature-pi-report'",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\n",
      "stdout": "HEAD is now at d7a67f5 container client push\n"
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/mother/demo-main-feature-pi-report checkout -- README.md",
      "returncode": 0,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace switch -c oob-container-new-branch'",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\nSwitched to a new branch 'oob-container-new-branch'\n",
      "stdout": ""
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace push origin HEAD:refs/heads/oob-container-new-branch'",
      "returncode": 1,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\nTo git://host.containers.internal:44651/demo\n ! [remote rejected] HEAD -> oob-container-new-branch (deny updating a hidden ref)\nerror: failed to push some refs to 'git://host.containers.internal:44651/demo'\n",
      "stdout": ""
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace switch demo-main-feature-pi-report'",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\nSwitched to branch 'demo-main-feature-pi-report'\n",
      "stdout": "Your branch is up to date with 'origin/demo-main-feature-pi-report'.\n"
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace tag oob-container-tag'",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\n",
      "stdout": ""
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace push origin refs/tags/oob-container-tag'",
      "returncode": 1,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\nTo git://host.containers.internal:44651/demo\n ! [remote rejected] oob-container-tag -> oob-container-tag (deny updating a hidden ref)\nerror: failed to push some refs to 'git://host.containers.internal:44651/demo'\n",
      "stdout": ""
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace reset --hard HEAD^'",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\n",
      "stdout": "HEAD is now at b96b9d6 initial fixture\n"
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'printf '\"'\"'%s\\n'\"'\"' '\"'\"'container non-fast-forward'\"'\"' > /home/agent/workspace/container-non-ff.txt'",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\n",
      "stdout": ""
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace add container-non-ff.txt'",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\n",
      "stdout": ""
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace commit -m '\"'\"'container non-fast-forward'\"'\"''",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\n",
      "stdout": "[demo-main-feature-pi-report 70eff6a] container non-fast-forward\n 1 file changed, 1 insertion(+)\n create mode 100644 container-non-ff.txt\n"
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace push origin --force HEAD:refs/heads/demo-main-feature-pi-report'",
      "returncode": 1,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\nremote: error: denying non-fast-forward refs/heads/demo-main-feature-pi-report (you should pull first)        \nTo git://host.containers.internal:44651/demo\n ! [remote rejected] HEAD -> demo-main-feature-pi-report (non-fast-forward)\nerror: failed to push some refs to 'git://host.containers.internal:44651/demo'\n",
      "stdout": ""
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace reset --hard origin/demo-main-feature-pi-report'",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\n",
      "stdout": "HEAD is now at d7a67f5 container client push\n"
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace push origin :refs/heads/demo-main-feature-pi-report'",
      "returncode": 1,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\nremote: error: denying ref deletion for refs/heads/demo-main-feature-pi-report        \nTo git://host.containers.internal:44651/demo\n ! [remote rejected] demo-main-feature-pi-report (deletion prohibited)\nerror: failed to push some refs to 'git://host.containers.internal:44651/demo'\n",
      "stdout": ""
    },
    {
      "command": "git clone -b demo-main-feature-pi-report git://127.0.0.1:44651/demo /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone",
      "returncode": 0,
      "stderr": "正克隆到 '/tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone'...\n",
      "stdout": ""
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone branch --show-current",
      "returncode": 0,
      "stderr": "",
      "stdout": "demo-main-feature-pi-report\n"
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone config user.name swt-m03",
      "returncode": 0,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone config user.email swt-m03@example.invalid",
      "returncode": 0,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone add host-client.txt host-client-run-1788572834834496554.txt",
      "returncode": 0,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone commit -m 'host client push'",
      "returncode": 0,
      "stderr": "",
      "stdout": "[demo-main-feature-pi-report c29101e] host client push\n 2 files changed, 2 insertions(+)\n create mode 100644 host-client-run-1788572834834496554.txt\n create mode 100644 host-client.txt\n"
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone push origin HEAD:refs/heads/demo-main-feature-pi-report",
      "returncode": 0,
      "stderr": "To git://127.0.0.1:44651/demo\n   d7a67f5..c29101e  HEAD -> demo-main-feature-pi-report\n",
      "stdout": ""
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone switch -c oob-new-branch",
      "returncode": 0,
      "stderr": "切换到一个新分支 'oob-new-branch'\n",
      "stdout": ""
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone push git://127.0.0.1:44651/demo HEAD:refs/heads/oob-new-branch",
      "returncode": 1,
      "stderr": "To git://127.0.0.1:44651/demo\n ! [remote rejected] HEAD -> oob-new-branch (deny updating a hidden ref)\nerror: 无法推送一些引用到 'git://127.0.0.1:44651/demo'\n",
      "stdout": ""
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone switch demo-main-feature-pi-report",
      "returncode": 0,
      "stderr": "切换到分支 'demo-main-feature-pi-report'\n",
      "stdout": "您的分支与上游分支 'origin/demo-main-feature-pi-report' 一致。\n"
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone tag oob-tag",
      "returncode": 0,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone push git://127.0.0.1:44651/demo refs/tags/oob-tag",
      "returncode": 1,
      "stderr": "To git://127.0.0.1:44651/demo\n ! [remote rejected] oob-tag -> oob-tag (deny updating a hidden ref)\nerror: 无法推送一些引用到 'git://127.0.0.1:44651/demo'\n",
      "stdout": ""
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone reset --hard 'HEAD^'",
      "returncode": 0,
      "stderr": "",
      "stdout": "HEAD 现在位于 d7a67f5 container client push\n"
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone add oob-non-ff.txt",
      "returncode": 0,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone commit -m 'oob non-fast-forward'",
      "returncode": 0,
      "stderr": "",
      "stdout": "[demo-main-feature-pi-report b84e744] oob non-fast-forward\n 1 file changed, 1 insertion(+)\n create mode 100644 oob-non-ff.txt\n"
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone push git://127.0.0.1:44651/demo --force HEAD:refs/heads/demo-main-feature-pi-report",
      "returncode": 1,
      "stderr": "remote: error: denying non-fast-forward refs/heads/demo-main-feature-pi-report (you should pull first)        \nTo git://127.0.0.1:44651/demo\n ! [remote rejected] HEAD -> demo-main-feature-pi-report (non-fast-forward)\nerror: 无法推送一些引用到 'git://127.0.0.1:44651/demo'\n",
      "stdout": ""
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/swt-m03-client-demo-main-feature-pi-report-981p_oqs/clone push git://127.0.0.1:44651/demo :refs/heads/demo-main-feature-pi-report",
      "returncode": 1,
      "stderr": "remote: error: denying ref deletion for refs/heads/demo-main-feature-pi-report        \nTo git://127.0.0.1:44651/demo\n ! [remote rejected] demo-main-feature-pi-report (deletion prohibited)\nerror: 无法推送一些引用到 'git://127.0.0.1:44651/demo'\n",
      "stdout": ""
    },
    {
      "command": "pgrep -af 'git( daemon|-daemon).*/tmp/swt\\-m03\\-test\\-2qvld9t9/srv'",
      "returncode": 0,
      "stderr": "",
      "stdout": "461554 git daemon --enable=receive-pack --base-path=/tmp/swt-m03-test-2qvld9t9/srv --listen=0.0.0.0 --port=44651 --reuseaddr --log-destination=none /tmp/swt-m03-test-2qvld9t9/srv\n461555 /usr/lib/git-core/git-daemon --enable=receive-pack --base-path=/tmp/swt-m03-test-2qvld9t9/srv --listen=0.0.0.0 --port=44651 --reuseaddr --log-destination=none /tmp/swt-m03-test-2qvld9t9/srv\n"
    },
    {
      "command": "podman ps -a --filter label=sandbox-worktree.repo=/tmp/swt-m03-test-2qvld9t9/srv/demo --format '{{.Names}}'",
      "returncode": 0,
      "stderr": "",
      "stdout": "swt-demo-main-feature-pi-report\n"
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace status --porcelain=v1'",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\n",
      "stdout": ""
    },
    {
      "command": "ssh -i /tmp/swt-m03-test-2qvld9t9/ssh/demo-main-feature-pi-report-1788572826527893398.ed25519 -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 42329 agent@127.0.0.1 'git -C /home/agent/workspace rev-list --count origin/demo-main-feature-pi-report..HEAD'",
      "returncode": 0,
      "stderr": "Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts.\n",
      "stdout": "0\n"
    },
    {
      "command": "podman rm -f swt-demo-main-feature-pi-report",
      "returncode": 0,
      "stderr": "",
      "stdout": "swt-demo-main-feature-pi-report\n"
    },
    {
      "command": "podman ps -a --filter label=sandbox-worktree.repo=/tmp/swt-m03-test-2qvld9t9/srv/demo --format '{{.Names}}'",
      "returncode": 0,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "kill -TERM 461554",
      "returncode": 0,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "pgrep -af 'git( daemon|-daemon).*/tmp/swt\\-m03\\-test\\-2qvld9t9/srv'",
      "returncode": 1,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "pgrep -af 'git( daemon|-daemon).*/tmp/swt\\-m03\\-test\\-2qvld9t9/srv'",
      "returncode": 1,
      "stderr": "",
      "stdout": ""
    },
    {
      "command": "git -C /tmp/swt-m03-test-2qvld9t9/srv/demo show-ref --verify refs/heads/demo-main-feature-pi-report",
      "returncode": 0,
      "stderr": "",
      "stdout": "c29101ef74be54622eea0acaf53a5117190d2f91 refs/heads/demo-main-feature-pi-report\n"
    }
  ],
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
      "decision": "未请求; 默认阻塞脏容器",
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
    "basis": "clean cleanup; no override",
    "decision": "not applicable",
    "fixture_path": "/tmp/swt-m03-test-2qvld9t9",
    "recorded_at": "2026-09-05T01:47:08Z",
    "status": "not requested",
    "status_summary": "",
    "uncommitted_changes": 0,
    "unpushed_commits": 0
  },
  "network": {
    "daemon_address": "0.0.0.0",
    "daemon_port": 44651,
    "mode": "full-network-intermediate"
  },
  "stage_log_history": [
    {
      "status": "ok",
      "summary": "create mother demo-main-feature-pi-report"
    },
    {
      "status": "ok",
      "summary": "export marker and D008 config"
    },
    {
      "status": "ok",
      "summary": "daemon 0.0.0.0:44651"
    },
    {
      "status": "ok",
      "summary": "audit NB-002 minimal Containerfile"
    },
    {
      "status": "ok",
      "summary": "container ssh BatchMode swt-demo-main-feature-pi-report:42329"
    },
    {
      "status": "ok",
      "summary": "container clone -b demo-main-feature-pi-report, daemon-only read face"
    },
    {
      "status": "ok",
      "summary": "container pi --help exit=0"
    },
    {
      "status": "ok",
      "summary": "birth complete"
    },
    {
      "status": "ok",
      "summary": "container push landed demo-main-feature-pi-report"
    },
    {
      "status": "ok",
      "summary": "container push rejected with dirty mother tree: Warning: Permanently added '[127.0.0.1]:42329' (ED25519) to the list of known hosts. To git://host.containers.internal:44651/demo  ! [remote rejected] HEAD -> demo-main-feature-pi-report (Working directory has unstaged changes) error: failed to push some refs to 'git://host.containers.internal:44651/demo'"
    },
    {
      "status": "ok",
      "summary": "container reject matrix: new branch/tag/non-ff/delete"
    },
    {
      "status": "ok",
      "summary": "host clone -b demo-main-feature-pi-report"
    },
    {
      "status": "ok",
      "summary": "host push landed demo-main-feature-pi-report: "
    },
    {
      "status": "ok",
      "summary": "reject matrix: new branch/tag/non-ff/delete"
    },
    {
      "status": "ok",
      "summary": "audit NB-001 hooks unchanged"
    },
    {
      "status": "ok",
      "summary": "audit NB-003 daemon command line"
    },
    {
      "status": "ok",
      "summary": "cleanup container removed swt-demo-main-feature-pi-report"
    },
    {
      "status": "ok",
      "summary": "cleanup daemon stopped"
    },
    {
      "status": "ok",
      "summary": "mother retained demo-main-feature-pi-report"
    },
    {
      "status": "ok",
      "summary": "cleanup ssh directory removed /tmp/swt-m03-test-2qvld9t9/ssh"
    },
    {
      "status": "ok",
      "summary": "cleanup complete"
    }
  ],
  "version": 1
}
```
