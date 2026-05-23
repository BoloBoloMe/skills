# cz_sdk build constraint on windows

## core rule

For this project on Windows, Maven compilation must use JDK 8.

## known working pattern

Example working Java path:

`C:\Users\L9214\.jdks\temurin-1.8.0_482\bin\java.exe`

## required validation

Before build, set `JAVA_HOME` to a JDK 8 home and verify:

```powershell
$env:JAVA_HOME='C:\path\to\jdk8'
$env:Path="$env:JAVA_HOME\bin;" + $env:Path
mvn -version
```

Proceed only if `mvn -version` shows Java 8.

## recommended compile commands

Compile paycenter and required modules:

```powershell
mvn -o "-Dmaven.repo.local=.m2-temp" -f czsdk-parent/pom.xml -pl ../czsdk-paycenter -am -DskipTests compile
```

Compile all modules under the parent project:

```powershell
mvn -o "-Dmaven.repo.local=.m2-temp" -f czsdk-parent/pom.xml -DskipTests compile
```

## strong failure signals

Common JDK mismatch symptoms include:

- `IllegalAccessError`
- `NoSuchFieldError`
- Lombok/Javac internal access failures

If these appear, switch back to JDK 8 first and re-run validation.
