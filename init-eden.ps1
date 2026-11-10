#!/usr/bin/env pwsh
<#
.SYNOPSIS
    E.D.E.N. Protocol bootstrapper (PowerShell 5.1+ / PowerShell 7+). Needs Python 3.

.DESCRIPTION
    Installs AGENTS.md, the per-tool instruction and hook files, the scripts, the shared
    .agents/skills, the .eden/ control plane, and the pre-commit hook into the target
    repository. The work is done by scripts/eden-install.py; this wrapper finds Python
    (python3, then python, then py -3) and passes the options through.

    New mode writes full files. Adopt mode merges an <!-- EDEN:BEGIN v1 --> ... <!-- EDEN:END -->
    block into an existing AGENTS.md, CLAUDE.md, GEMINI.md, or .github/copilot-instructions.md
    (text outside the markers is kept) and detects the Setup/Build/Test/Lint commands.
    Re-running is safe. Existing .eden/ state files are always kept, even with -Force.

    GNU-style options (--adopt, --tools cursor,grok, ...) are accepted too.
    This file is intentionally ASCII-only so Windows PowerShell 5.1 reads it correctly.
    EDEN_RAW_BASE downloads are a trust boundary; set EDEN_SHA256 to verify
    scripts/eden-install.py (64 hex digits) or a sha256sum-format file.

.PARAMETER TargetDir
    Repository to initialize. Defaults to the current directory.
.PARAMETER New
    Brand-new project: write full files. Default when the target has no commits and no source files.
.PARAMETER Adopt
    Existing project: merge EDEN blocks and detect commands. Default otherwise.
.PARAMETER Tools
    Comma-separated: antigravity,cursor,grok,vscode,claude. Default: antigravity,cursor,grok,vscode.
.PARAMETER Legacy
    Also write .cursorrules and .windsurfrules.
.PARAMETER Force
    Replace E.D.E.N.-managed files wholesale (each backed up as <file>.eden-bak).
.PARAMETER Detect
    Detect commands in new mode too. -NoDetect turns detection off.
.PARAMETER Reindex
    Regenerate section 2 of an existing .eden/REGISTRY.md.
.PARAMETER SourceDir
    Protocol checkout to copy from. Defaults to the folder holding this script.
.PARAMETER ProjectName
    Name used in .eden/ARCHITECTURE.md. Defaults to the target folder name.

.EXAMPLE
    C:\src\E.D.E.N.-Protocol\init-eden.ps1                      # run from inside your repo
    C:\src\E.D.E.N.-Protocol\init-eden.ps1 C:\src\app -Adopt -Tools cursor,vscode
#>
param(
    [Parameter(Position = 0)][string]$TargetDir = (Get-Location).Path,
    [switch]$New,
    [switch]$Adopt,
    [string]$Tools = "",
    [switch]$Legacy,
    [switch]$Force,
    [switch]$Detect,
    [switch]$NoDetect,
    [switch]$Reindex,
    [string]$SourceDir = "",
    [string]$ProjectName = "",
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$Rest = @()
)

$ErrorActionPreference = "Stop"
if (-not $SourceDir) {
    $SourceDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Definition }
}

# Files the installer reads from the protocol checkout (keep in sync with scripts/eden-install.py).
$SourceFiles = @(
    "AGENTS.md", "CLAUDE.md", "GEMINI.md", ".cursorrules", ".windsurfrules",
    ".cursor/rules/eden.mdc", ".github/copilot-instructions.md",
    "scripts/eden-audit.py", "scripts/eden-index.py", "scripts/eden-hook.py",
    "scripts/eden_common.py", "scripts/eden-install.py",
    ".cursor/hooks.json", ".github/hooks/eden.json", ".agents/hooks.json",
    ".agents/skills/eden-normalize/SKILL.md", ".agents/skills/eden-architect/SKILL.md",
    ".agents/skills/eden-adopt/SKILL.md",
    "templates/eden/ARCHITECTURE.md", "templates/eden/PLAN.md", "templates/eden/REGISTRY.md",
    "templates/eden/LEARNINGS.md", "templates/hooks/pre-commit"
)

# Options for the installer. GNU-style arguments (--adopt, --tools x) are passed through as-is.
$InstallArgs = @()
if ($New) { $InstallArgs += "--new" }
if ($Adopt) { $InstallArgs += "--adopt" }
if ($Tools) { $InstallArgs += @("--tools", $Tools) }
if ($Legacy) { $InstallArgs += "--legacy" }
if ($Force) { $InstallArgs += "--force" }
if ($Detect) { $InstallArgs += "--detect" }
if ($NoDetect) { $InstallArgs += "--no-detect" }
if ($Reindex) { $InstallArgs += "--reindex" }
if ($ProjectName) { $InstallArgs += @("--name", $ProjectName) }
if ($TargetDir.StartsWith("--")) {
    # A GNU-style option landed in the positional slot.
    $Rest = @($TargetDir) + $Rest
    $TargetDir = (Get-Location).Path
}
for ($i = 0; $i -lt $Rest.Count; $i++) {
    $a = $Rest[$i]
    if ($a -eq "--source") { $SourceDir = $Rest[$i + 1]; $i++ }
    elseif ($a -in @("--tools", "--name")) { $InstallArgs += @($a, $Rest[$i + 1]); $i++ }
    elseif ($a.StartsWith("--")) { $InstallArgs += $a }
    else { $TargetDir = $a }
}

if (-not (Test-Path $TargetDir)) { New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null }
$TargetDir = (Resolve-Path $TargetDir).Path

# Fetch the protocol files if the source folder does not have them.
$TempSource = $null
if (-not $SourceDir -or -not (Test-Path (Join-Path $SourceDir "scripts/eden-install.py")) -or
    -not (Test-Path (Join-Path $SourceDir "templates/hooks/pre-commit"))) {
    if (-not $env:EDEN_RAW_BASE) {
        Write-Error ("'$SourceDir' is not an E.D.E.N.-Protocol checkout (scripts/ or templates/ missing). " +
            "Run this script from a clone of the protocol repo, pass -SourceDir, or set EDEN_RAW_BASE.")
    }
    $TempSource = Join-Path ([System.IO.Path]::GetTempPath()) ("eden-" + [guid]::NewGuid())
    Write-Host "Downloading protocol files from $($env:EDEN_RAW_BASE)"
    foreach ($f in $SourceFiles) {
        $dest = Join-Path $TempSource $f
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest) | Out-Null
        Invoke-WebRequest -UseBasicParsing -Uri "$($env:EDEN_RAW_BASE)/$f" -OutFile $dest
    }
    $SourceDir = $TempSource
}
$SourceDir = (Resolve-Path $SourceDir).Path

# Optional integrity check (no-op unless EDEN_SHA256 is set).
if ($env:EDEN_SHA256) {
    function Get-EdenSha256([string]$FilePath) {
        return (Get-FileHash -Algorithm SHA256 -Path $FilePath).Hash.ToLowerInvariant()
    }
    $spec = $env:EDEN_SHA256
    if (Test-Path -LiteralPath $spec -PathType Leaf) {
        Get-Content -LiteralPath $spec | ForEach-Object {
            $line = $_.Trim()
            if (-not $line -or $line.StartsWith("#")) { return }
            $parts = $line -split '\s+', 2
            if ($parts.Count -lt 2) {
                Write-Error "EDEN_SHA256 checksums file has a line without a path."
            }
            $rel = $parts[1].Trim().TrimStart([char]'*')
            $actual = Get-EdenSha256 (Join-Path $SourceDir $rel)
            if ($actual -ne $parts[0].ToLowerInvariant()) {
                Write-Error "sha256 mismatch for $rel (EDEN_SHA256 checksums file)."
            }
        }
        Write-Host "EDEN_SHA256: checksums file verified."
    }
    elseif ($spec -match '^[0-9A-Fa-f]{64}$') {
        $actual = Get-EdenSha256 (Join-Path $SourceDir "scripts/eden-install.py")
        if ($actual -ne $spec.ToLowerInvariant()) {
            Write-Error "sha256 mismatch for scripts/eden-install.py."
        }
        Write-Host "EDEN_SHA256: scripts/eden-install.py verified."
    }
    else {
        Write-Error ("EDEN_SHA256 must be a 64-digit hex digest of scripts/eden-install.py " +
            "or a path to a sha256sum-format file.")
    }
}

if ($SourceDir -eq $TargetDir) {
    Write-Error "Target is the protocol repo itself. Run this from (or point it at) the repo you want to initialize."
}

# Python 3 discovery: python3, then python, then the py -3 launcher. Each candidate is probed,
# which skips the Windows Store "python" stub that only opens the Store.
$PyExe = $null
$PyArgs = @()
foreach ($cand in @(@("python3"), @("python"), @("py", "-3"))) {
    if (-not (Get-Command $cand[0] -ErrorAction SilentlyContinue)) { continue }
    $probeArgs = @($cand | Select-Object -Skip 1) + @("-c", "import sys; sys.exit(sys.version_info[0] != 3)")
    try {
        & $cand[0] @probeArgs *> $null
        if ($LASTEXITCODE -eq 0) { $PyExe = $cand[0]; $PyArgs = @($cand | Select-Object -Skip 1); break }
    } catch { }
}
if (-not $PyExe) {
    Write-Error "Python 3 not found (tried python3, python, py -3). Install Python 3 and re-run."
}

try {
    & $PyExe @PyArgs (Join-Path $SourceDir "scripts/eden-install.py") --source $SourceDir --target $TargetDir @InstallArgs
    $code = $LASTEXITCODE
} finally {
    if ($TempSource) { Remove-Item -Recurse -Force $TempSource -ErrorAction SilentlyContinue }
}
exit $code
