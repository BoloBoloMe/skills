---
name: cz-sdk-windows-build
description: compile and diagnose cz_sdk on windows with a strict jdk 8 workflow. use when the user wants to build, compile, validate maven compilation, or troubleshoot build failures for cz_sdk, czsdk-parent, czsdk-paycenter, or related modules on a windows machine. always detect an available jdk 8 first, enforce jdk 8 before maven compile, stop if the environment is not on jdk 8, and run standardized failure diagnosis when compilation fails.
---

# cz-sdk windows build

Use this skill only for Windows-based `cz_sdk` Maven build and build-failure diagnosis.

## Required behavior

1. Use PowerShell.
2. Detect candidate JDK 8 installations before compile.
3. If no JDK 8 is found automatically, tell the user that no usable JDK 8 was detected and ask for a path to a JDK 8 home directory.
4. Do not continue to Maven compile until `mvn -version` confirms Java 8.
5. Use the unified entry script `scripts/run_build.ps1`.
6. If build fails, run `scripts/diagnose_build_failure.ps1` on the captured build log and explain the diagnosis clearly.
7. If the failure is clearly environment-related, do not jump into code-level debugging first.

## Default execution flow

### Step 1: discover JDK 8

Run:

- `scripts/find_jdk8_candidates.ps1`

If one or more candidates are returned, prefer:

- the explicitly user-provided path
- otherwise the first valid Temurin/Adoptium JDK 8 candidate
- otherwise the first valid JDK 8 candidate

If no valid JDK 8 candidate exists:

- stop compile
- tell the user no JDK 8 was found
- ask them to provide a JDK 8 home path
- offer help on where to look

### Step 2: validate environment

Run:

- `scripts/check_env.ps1 -Jdk8Home <path>`

Proceed only if:

- `java.exe` exists under the provided home
- `mvn -version` reports Java 8

If validation fails:

- stop
- explain the reason
- do not continue to compile

### Step 3: run build

Run the unified build entry:

- paycenter build:
  `scripts/run_build.ps1 -Mode paycenter -Jdk8Home <path> -RepoRoot <repoRoot>`
- full build:
  `scripts/run_build.ps1 -Mode all -Jdk8Home <path> -RepoRoot <repoRoot>`

### Step 4: diagnose build failure

If compile fails, run:

- `scripts/diagnose_build_failure.ps1 -LogPath <captured log path>`

Use its result to classify the failure into one of:

- jdk_version_mismatch
- lombok_javac_compatibility
- offline_dependency_missing
- pom_or_relative_path_error
- source_compile_error
- unknown

Then explain:

- what category was detected
- the evidence pattern
- the next action to take

## User interaction rules

When no JDK 8 is found, use guided wording. Tell the user:

- no usable JDK 8 was detected automatically
- a JDK 8 home directory is required before build can continue
- examples of possible locations include:
  - `C:\Users\<user>\.jdks\temurin-1.8.0_xxx`
  - `C:\Program Files\Java\jdk1.8.*`
  - `C:\Program Files\Eclipse Adoptium\*`
  - `C:\Program Files\Temurin\*`

Also explicitly invite follow-up questions such as:

- how to find JDK 8 on this machine
- how to verify whether a path is JDK 8
- whether a JRE path is acceptable
- which candidate path should be chosen

## Notes

- Prefer repository-local Maven cache:
  `-Dmaven.repo.local=.m2-temp`
- Prefer offline compile when requested workflow already assumes local cache:
  `-o`
- Prefer `-DskipTests` unless the user explicitly asks to run tests.
- Do not assume JDK 21 or newer is acceptable for this project.
- If `IllegalAccessError` or `NoSuchFieldError` references Lombok/Javac internals, treat it as environment/JDK compatibility first.
