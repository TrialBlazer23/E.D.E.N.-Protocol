#!/usr/bin/env pwsh
<#
.SYNOPSIS
    E.D.E.N. Protocol bootstrapper (PowerShell 5.1+ / PowerShell 7+).

.DESCRIPTION
    Copies AGENTS.md, the agent pointer files, scripts/eden-audit.py, scripts/eden-index.py,
    the .eden/ templates, and the pre-commit hook from this protocol checkout into the target
    repository. Existing files are never overwritten unless -Force is given; with -Force each
    replaced file is backed up as <file>.eden-bak. Existing .eden/ state files (ARCHITECTURE,
    PLAN, REGISTRY, LEARNINGS, CHANGELOG_AGENT.jsonl) are always kept, even with -Force.

    This file is intentionally ASCII-only so Windows PowerShell 5.1 reads it correctly.
    Files are copied byte-for-byte; generated files are written as UTF-8 without BOM.

.PARAMETER TargetDir
    Repository to initialize. Defaults to the current directory.
.PARAMETER SourceDir
    Protocol checkout to copy from. Defaults to the folder holding this script.
.PARAMETER ProjectName
    Name used in .eden/ARCHITECTURE.md. Defaults to the target folder name.
.PARAMETER Force
    Overwrite existing files (with backups).

.EXAMPLE
    C:\src\E.D.E.N-Protocol\init-eden.ps1            # run from inside your repo
    C:\src\E.D.E.N-Protocol\init-eden.ps1 C:\src\app
#>
param(
    [Parameter(Position = 0)][string]$TargetDir = (Get-Location).Path,
    [string]$SourceDir = $PSScriptRoot,
    [string]$ProjectName = "",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$Utf8NoBom = New-Object System.Text.UTF8Encoding $false
$IsWindowsHost = ($env:OS -eq "Windows_NT")

$CopyFiles = @(
    "AGENTS.md", "CLAUDE.md", "GEMINI.md", ".cursorrules", ".windsurfrules",
    ".cursor/rules/eden.mdc", ".github/copilot-instructions.md",
    "scripts/eden-audit.py", "scripts/eden-index.py"
)
$TemplateFiles = @(
    "templates/eden/ARCHITECTURE.md", "templates/eden/PLAN.md", "templates/eden/REGISTRY.md",
    "templates/eden/LEARNINGS.md", "templates/hooks/pre-commit"
)

if (-not (Test-Path $TargetDir)) { New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null }
$TargetDir = (Resolve-Path $TargetDir).Path
if (-not $ProjectName) { $ProjectName = Split-Path -Leaf $TargetDir }

# Fetch the protocol files if the source folder does not have them.
$TempSource = $null
if (-not $SourceDir -or -not (Test-Path (Join-Path $SourceDir "scripts/eden-audit.py")) -or
    -not (Test-Path (Join-Path $SourceDir "templates/hooks/pre-commit"))) {
    if (-not $env:EDEN_RAW_BASE) {
        Write-Error ("'$SourceDir' is not an E.D.E.N.-Protocol checkout (scripts/ or templates/ missing). " +
            "Run this script from a clone of the protocol repo, pass -SourceDir, or set EDEN_RAW_BASE.")
    }
    $TempSource = Join-Path ([System.IO.Path]::GetTempPath()) ("eden-" + [guid]::NewGuid())
    Write-Host "Downloading protocol files from $($env:EDEN_RAW_BASE)"
    foreach ($f in $CopyFiles + $TemplateFiles) {
        $dest = Join-Path $TempSource $f
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest) | Out-Null
        Invoke-WebRequest -UseBasicParsing -Uri "$($env:EDEN_RAW_BASE)/$f" -OutFile $dest
    }
    $SourceDir = $TempSource
}
$SourceDir = (Resolve-Path $SourceDir).Path

if ($SourceDir -eq $TargetDir) {
    Write-Error "Target is the protocol repo itself. Run this from (or point it at) the repo you want to initialize."
}

Set-Location $TargetDir
Write-Host "Initializing E.D.E.N. Protocol in $TargetDir (project: $ProjectName)" -ForegroundColor Cyan

$script:Skipped = $false
$script:Backups = $false

function Test-SameContent([string]$A, [string]$B) {
    $ba = [System.IO.File]::ReadAllBytes($A)
    $bb = [System.IO.File]::ReadAllBytes($B)
    if ($ba.Length -ne $bb.Length) { return $false }
    for ($i = 0; $i -lt $ba.Length; $i++) { if ($ba[$i] -ne $bb[$i]) { return $false } }
    return $true
}

# Writes $Bytes to $Dest unless it exists (then skip, or back up and replace with -Force).
# -NeverReplace keeps existing project state files even with -Force.
function Install-Bytes([byte[]]$Bytes, [string]$Dest, [switch]$NeverReplace, [switch]$Executable) {
    $full = Join-Path $TargetDir $Dest
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $full) | Out-Null
    if (Test-Path $full) {
        $tmp = [System.IO.Path]::GetTempFileName()
        [System.IO.File]::WriteAllBytes($tmp, $Bytes)
        $same = Test-SameContent $tmp $full
        Remove-Item $tmp
        if ($same) { Write-Host "  [=] $Dest (already up to date)"; return }
        if ($NeverReplace) { Write-Host "  [=] $Dest exists (project state; kept)"; return }
        if (-not $Force) {
            Write-Host "  [~] $Dest exists; skipped (re-run with -Force to replace it; a backup is kept)" -ForegroundColor Yellow
            $script:Skipped = $true
            return
        }
        Copy-Item -Force $full "$full.eden-bak"
        $script:Backups = $true
        Write-Host "  [!] $Dest replaced (backup: $Dest.eden-bak)" -ForegroundColor Yellow
    } else {
        Write-Host "  [+] $Dest" -ForegroundColor Green
    }
    [System.IO.File]::WriteAllBytes($full, $Bytes)
    if ($Executable -and -not $IsWindowsHost -and (Get-Command chmod -ErrorAction SilentlyContinue)) {
        & chmod 755 $full
    }
}

function Get-SourceBytes([string]$Rel) {
    return [System.IO.File]::ReadAllBytes((Join-Path $SourceDir $Rel))
}

# Normalizes to LF and encodes as UTF-8 without BOM (needed for the sh hook on Windows checkouts).
function ConvertTo-LfBytes([byte[]]$Bytes) {
    $text = $Utf8NoBom.GetString($Bytes).TrimStart([char]0xFEFF) -replace "`r`n", "`n"
    return $Utf8NoBom.GetBytes($text)
}

# 1. Agent instructions, pointer files, and tooling
foreach ($f in $CopyFiles) {
    if ($f -like "scripts/*") { Install-Bytes (Get-SourceBytes $f) $f -Executable }
    else { Install-Bytes (Get-SourceBytes $f) $f }
}

# 2. Control plane templates
$arch = $Utf8NoBom.GetString((Get-SourceBytes "templates/eden/ARCHITECTURE.md")).Replace("{{PROJECT_NAME}}", $ProjectName)
Install-Bytes ($Utf8NoBom.GetBytes($arch)) ".eden/ARCHITECTURE.md" -NeverReplace
foreach ($f in @("PLAN.md", "REGISTRY.md", "LEARNINGS.md")) {
    Install-Bytes (Get-SourceBytes "templates/eden/$f") ".eden/$f" -NeverReplace
}

$changelog = Join-Path $TargetDir ".eden/CHANGELOG_AGENT.jsonl"
if (-not (Test-Path $changelog) -or (Get-Item $changelog).Length -eq 0) {
    $ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $line = '{"timestamp":"' + $ts + '","phase":"Normalize","task_id":"TASK-00","action":"CREATED","files":["AGENTS.md",".eden/ARCHITECTURE.md",".eden/PLAN.md",".eden/REGISTRY.md",".eden/LEARNINGS.md"],"reused_modules":[],"summary":"Initialized the E.D.E.N. control plane."}' + "`n"
    [System.IO.File]::WriteAllText($changelog, $line, $Utf8NoBom)
    Write-Host "  [+] .eden/CHANGELOG_AGENT.jsonl" -ForegroundColor Green
} else {
    Write-Host "  [=] .eden/CHANGELOG_AGENT.jsonl (kept; append-only)"
}

# 3. Git pre-commit hook (respects core.hooksPath and worktrees)
$hooksDir = $null
if (Get-Command git -ErrorAction SilentlyContinue) {
    $hooksDir = (& git rev-parse --git-path hooks 2>$null)
    if ($LASTEXITCODE -ne 0) { $hooksDir = $null }
}
if ($hooksDir) {
    $hookRel = (Join-Path $hooksDir "pre-commit")
    if ([System.IO.Path]::IsPathRooted($hookRel)) {
        $hookRel = $hookRel.Substring($TargetDir.Length).TrimStart('\', '/')
    }
    Install-Bytes (ConvertTo-LfBytes (Get-SourceBytes "templates/hooks/pre-commit")) $hookRel -Executable
    $hookText = Get-Content -Raw (Join-Path $TargetDir $hookRel)
    if ($hookText -notmatch "eden-audit\.py") {
        Write-Host "      Your existing hook does not run the audit. Add this line to it:"
        Write-Host "      python3 scripts/eden-audit.py --staged || exit 1"
    } elseif ($hookText -notmatch "--staged") {
        Write-Host "      Your hook runs the audit without --staged; re-run with -Force to install the current hook."
    }
} else {
    Write-Host "  [-] Not a git repository; pre-commit hook not installed (run 'git init' and re-run)."
}

# 4. Index existing source files into .eden/REGISTRY.md
$py = $null
foreach ($candidate in @("python3", "python", "py")) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) { $py = $candidate; break }
}
if ($py) {
    & $py (Join-Path $TargetDir "scripts/eden-index.py") $TargetDir
} else {
    Write-Host "  [-] Python 3 not found; skipped indexing. Install Python 3 to use the audit."
}

if ($TempSource) { Remove-Item -Recurse -Force $TempSource }

Write-Host "Done. Next: fill in the Commands section of AGENTS.md and .eden/ARCHITECTURE.md, then run:" -ForegroundColor Green
Write-Host "  python3 scripts/eden-audit.py"
if ($script:Backups) {
    Write-Host "Review and delete the *.eden-bak backups before committing." -ForegroundColor Yellow
}
if ($script:Skipped) {
    Write-Host "Some files already existed and were left unchanged (see [~] above). Use -Force to replace them." -ForegroundColor Yellow
}
