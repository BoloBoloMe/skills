param()

Write-Host 'No usable JDK 8 was found automatically.'
Write-Host ''
Write-Host 'Please provide a JDK 8 home path. A JDK home path should look like one of these:'
Write-Host '  C:\Users\<user>\.jdks\temurin-1.8.0_482'
Write-Host '  C:\Program Files\Java\jdk1.8.0_XXX'
Write-Host '  C:\Program Files\Eclipse Adoptium\jdk-8*'
Write-Host '  C:\Program Files\Temurin\jdk-8*'
Write-Host ''
Write-Host 'Notes:'
Write-Host '  - Provide the JDK home directory, not the bin directory.'
Write-Host '  - A JRE path is not enough; Maven compile needs a JDK.'
Write-Host '  - If you are unsure, ask which candidate path should be used.'
