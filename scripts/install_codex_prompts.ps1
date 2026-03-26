param(
    [string]$SourceDir = (Join-Path $PSScriptRoot "..\\codex-prompts"),
    [string]$TargetDir = (Join-Path $HOME ".codex\\prompts")
)

$resolvedSource = (Resolve-Path $SourceDir).Path
New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null

$installed = @()
Get-ChildItem -Path $resolvedSource -File -Filter *.md | ForEach-Object {
    $targetPath = Join-Path $TargetDir $_.Name
    Copy-Item -Path $_.FullName -Destination $targetPath -Force
    $installed += $targetPath
}

Write-Output "Installed Codex prompt wrappers:"
$installed | ForEach-Object { Write-Output $_ }
