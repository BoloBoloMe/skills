---
name: cz-sdk-windows-build
description: 当你要在 Windows 环境下对 `cz_sdk` 项目进行 Maven 构建时使用.
---

# cz-sdk Windows 构建

仅将此 skill 用于 Windows 环境下的 `cz_sdk` Maven 构建和构建失败诊断.

## 目录结构

```text
cz-sdk-windows-build/
|-- SKILL.md
|-- references/
|   `-- jdk8-constraint.md
`-- scripts/
    |-- check_env.ps1
    |-- diagnose_build_failure.ps1
    |-- find_jdk8_candidates.ps1
    |-- help_find_jdk8.ps1
    `-- run_build.ps1
```

## 必需行为

1. 使用 PowerShell.
2. 编译前检测候选 JDK 8 安装.
3. 如果未能自动找到 JDK 8, 告知用户未检测到可用 JDK 8, 并要求提供 JDK 8 home 目录路径.
4. 在 `mvn -version` 确认 Java 8 之前, 不继续执行 Maven 编译.
5. 使用统一入口脚本 `scripts/run_build.ps1`.
6. 如果构建失败, 对捕获的构建日志运行 `scripts/diagnose_build_failure.ps1`, 并清晰解释诊断结果.
7. 如果失败明显由环境引起, 不要先进入代码级调试.

## 默认执行流程

### 步骤 1: 发现 JDK 8

运行:

- `scripts/find_jdk8_candidates.ps1`

如果返回一个或多个候选项, 按以下优先级选择:

- 用户显式提供的路径.
- 否则选择第一个有效的 Temurin/Adoptium JDK 8 候选项.
- 否则选择第一个有效的 JDK 8 候选项.

如果不存在有效 JDK 8 候选项:

- 停止编译.
- 告知用户未找到 JDK 8.
- 要求用户提供 JDK 8 home 路径.
- 主动说明可以从哪些位置查找.

### 步骤 2: 校验环境

运行:

- `scripts/check_env.ps1 -Jdk8Home <path>`

只有满足以下条件时才继续:

- 提供的 home 目录下存在 `java.exe`.
- `mvn -version` 报告 Java 8.

如果校验失败:

- 停止.
- 解释原因.
- 不继续编译.

### 步骤 3: 运行构建

运行统一构建入口:

- paycenter 构建:
  `scripts/run_build.ps1 -Mode paycenter -Jdk8Home <path> -RepoRoot <repoRoot>`
- 全量构建:
  `scripts/run_build.ps1 -Mode all -Jdk8Home <path> -RepoRoot <repoRoot>`

### 步骤 4: 诊断构建失败

如果编译失败, 运行:

- `scripts/diagnose_build_failure.ps1 -LogPath <captured log path>`

使用其结果将失败分类为以下之一:

- `jdk_version_mismatch`: JDK 版本不匹配.
- `lombok_javac_compatibility`: Lombok 与 Javac 兼容性问题.
- `offline_dependency_missing`: 离线依赖缺失.
- `pom_or_relative_path_error`: POM 或相对路径错误.
- `source_compile_error`: 源码编译错误.
- `unknown`: 未知原因.

然后解释:

- 检测到的类别.
- 证据模式.
- 下一步动作.

## 用户交互规则

未找到 JDK 8 时, 使用引导式措辞. 告知用户:

- 未自动检测到可用 JDK 8.
- 必须提供 JDK 8 home 目录后才能继续构建.
- 可能的位置示例包括:
  - `C:\Users\<user>\.jdks\temurin-1.8.0_xxx`
  - `C:\Program Files\Java\jdk1.8.*`
  - `C:\Program Files\Eclipse Adoptium\*`
  - `C:\Program Files\Temurin\*`

同时明确邀请用户继续提问, 例如:

- 如何在这台机器上查找 JDK 8.
- 如何验证某个路径是否是 JDK 8.
- JRE 路径是否可接受.
- 应该选择哪个候选路径.

## 备注

- 优先使用仓库本地 Maven 缓存:
  `-Dmaven.repo.local=.m2-temp`
- 当请求的工作流已经假定存在本地缓存时, 优先离线编译:
  `-o`
- 除非用户明确要求运行测试, 否则优先使用 `-DskipTests`.
- 不要假设 JDK 21 或更高版本适用于本项目.
- 如果 `IllegalAccessError` 或 `NoSuchFieldError` 引用了 Lombok/Javac 内部实现, 优先按环境/JDK 兼容性问题处理.
