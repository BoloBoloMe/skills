# cz_sdk Windows 构建约束

## 核心规则

在 Windows 上构建本项目时, Maven 编译必须使用 JDK 8.

## 已知可用模式

可用 Java 路径示例:

`C:\Users\L9214\.jdks\temurin-1.8.0_482\bin\java.exe`

## 必需校验

构建前, 将 `JAVA_HOME` 设置为 JDK 8 home, 并执行校验:

```powershell
$env:JAVA_HOME='C:\path\to\jdk8'
$env:Path="$env:JAVA_HOME\bin;" + $env:Path
mvn -version
```

只有 `mvn -version` 显示 Java 8 时才继续.

## 推荐编译命令

编译 paycenter 及其必需模块:

```powershell
mvn -o "-Dmaven.repo.local=.m2-temp" -f czsdk-parent/pom.xml -pl ../czsdk-paycenter -am -DskipTests compile
```

编译 parent 项目下的所有模块:

```powershell
mvn -o "-Dmaven.repo.local=.m2-temp" -f czsdk-parent/pom.xml -DskipTests compile
```

## 强失败信号

常见 JDK 不匹配症状包括:

- `IllegalAccessError`
- `NoSuchFieldError`
- Lombok/Javac 内部访问失败

如果出现这些信号, 先切回 JDK 8 并重新运行校验.
