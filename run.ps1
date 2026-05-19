# =============================================================================
#  JFrog MCP Gateway — Bootstrap (Windows PowerShell)
#  Usage:  .\run.ps1
#
#  What this script does:
#    1. Detects Windows version and architecture
#    2. Installs Python 3.9+ if missing  (winget → Microsoft Store → manual)
#    3. Installs / upgrades pip
#    4. Creates an isolated virtual environment (.venv)
#    5. Activates it and runs jfrog_mcp_setup.py
# =============================================================================

#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Enable ANSI colours on Windows 10+ ───────────────────────────────────────
$null = [System.Console]::OutputEncoding
try {
    $null = [System.Runtime.InteropServices.RuntimeInformation]
    Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class ConsoleHelper {
    [DllImport("kernel32.dll")] public static extern bool SetConsoleMode(IntPtr h, uint m);
    [DllImport("kernel32.dll")] public static extern IntPtr GetStdHandle(int n);
    [DllImport("kernel32.dll")] public static extern bool GetConsoleMode(IntPtr h, out uint m);
}
"@ -ErrorAction SilentlyContinue
    $handle = [ConsoleHelper]::GetStdHandle(-11)
    $mode = 0
    [ConsoleHelper]::GetConsoleMode($handle, [ref]$mode) | Out-Null
    [ConsoleHelper]::SetConsoleMode($handle, $mode -bor 4) | Out-Null
} catch {}

# ── Helpers ───────────────────────────────────────────────────────────────────
function Write-Info    ($t) { Write-Host "  [i]  $t" -ForegroundColor Cyan }
function Write-Success ($t) { Write-Host "  OK   $t" -ForegroundColor Green }
function Write-Warn    ($t) { Write-Host "  [!]  $t" -ForegroundColor Yellow }
function Write-Err     ($t) { Write-Host "  [X]  $t" -ForegroundColor Red }
function Write-Doing   ($t) { Write-Host "  ...  $t" -NoNewline -ForegroundColor DarkCyan }
function Write-Done    ()   { Write-Host " done" -ForegroundColor Green }

function Test-Command ($cmd) {
    return [bool](Get-Command $cmd -ErrorAction SilentlyContinue)
}

function Get-PythonVersion ($cmd) {
    try {
        $v = & $cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        return $v.Trim()
    } catch { return $null }
}

function Test-PythonMinVersion ($cmd, $minMajor, $minMinor) {
    $v = Get-PythonVersion $cmd
    if (-not $v) { return $false }
    $parts = $v -split "\."
    if ($parts.Count -lt 2) { return $false }
    $major = [int]$parts[0]; $minor = [int]$parts[1]
    return ($major -gt $minMajor) -or ($major -eq $minMajor -and $minor -ge $minMinor)
}

function Find-Python ($minMajor, $minMinor) {
    foreach ($cmd in @("python", "python3", "python3.11", "python3.10", "python3.9")) {
        if (Test-Command $cmd) {
            if (Test-PythonMinVersion $cmd $minMajor $minMinor) {
                return $cmd
            }
        }
    }
    # Also check common install paths
    $paths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python39\python.exe",
        "C:\Python311\python.exe",
        "C:\Python310\python.exe"
    )
    foreach ($path in $paths) {
        if (Test-Path $path) {
            if (Test-PythonMinVersion $path $minMajor $minMinor) {
                return $path
            }
        }
    }
    return $null
}

# ── Detect OS info ────────────────────────────────────────────────────────────
$WinVer  = [System.Environment]::OSVersion.Version
$Arch    = $env:PROCESSOR_ARCHITECTURE   # AMD64 | ARM64 | x86

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║     JFrog MCP Gateway  —  Bootstrap (Windows)       ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Info "Windows $($WinVer.Major).$($WinVer.Minor)  |  Arch: $Arch"
Write-Host ""

$MIN_MAJOR = 3
$MIN_MINOR = 9

# ─────────────────────────────────────────────────────────────────────────────
#  STEP 1 — Python 3.9+
# ─────────────────────────────────────────────────────────────────────────────
Write-Host "`n[1/4]  Python 3.$MIN_MINOR+" -ForegroundColor White

$PythonCmd = Find-Python $MIN_MAJOR $MIN_MINOR

if ($PythonCmd) {
    $pyVer = Get-PythonVersion $PythonCmd
    Write-Success "Python found: $PythonCmd  ($pyVer)"
} else {
    Write-Warn "Python 3.$MIN_MINOR+ not found — installing now..."

    $installed = $false

    # Try winget first (Windows 10 1709+ / Windows 11)
    if (Test-Command "winget") {
        Write-Doing "winget install Python 3.11"
        try {
            winget install -e --id Python.Python.3.11 `
                --accept-source-agreements `
                --accept-package-agreements `
                --silent 2>&1 | Out-Null
            Write-Done
            $installed = $true
        } catch {
            Write-Done
            Write-Warn "winget install failed: $_"
        }
    }

    # Try Chocolatey
    if (-not $installed -and (Test-Command "choco")) {
        Write-Doing "choco install python311"
        try {
            choco install python311 -y --no-progress 2>&1 | Out-Null
            Write-Done
            $installed = $true
        } catch {
            Write-Done
            Write-Warn "choco install failed: $_"
        }
    }

    # Try Microsoft Store (opens store page, user must confirm)
    if (-not $installed) {
        Write-Warn "Automatic install not available. Opening Python download page..."
        Start-Process "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
        Write-Host ""
        Write-Host "  Please install Python 3.11 from the page that just opened." -ForegroundColor Yellow
        Write-Host "  IMPORTANT: check the box  'Add Python to PATH'  during install." -ForegroundColor Yellow
        Write-Host ""
        Read-Host "  Press Enter after Python is installed"
    }

    # Refresh PATH so the newly installed python is visible
    $env:PATH = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path", "User")

    $PythonCmd = Find-Python $MIN_MAJOR $MIN_MINOR
    if (-not $PythonCmd) {
        Write-Err "Python still not found after installation."
        Write-Err "Please restart PowerShell and re-run:  .\run.ps1"
        exit 1
    }
    $pyVer = Get-PythonVersion $PythonCmd
    Write-Success "Python installed: $PythonCmd  ($pyVer)"
}

# ─────────────────────────────────────────────────────────────────────────────
#  STEP 2 — pip
# ─────────────────────────────────────────────────────────────────────────────
Write-Host "`n[2/4]  pip" -ForegroundColor White

$pipCheck = & $PythonCmd -m pip --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Success "pip available  ($($pipCheck -split "`n" | Select-Object -First 1))"
} else {
    Write-Warn "pip not found — installing via ensurepip..."
    try {
        & $PythonCmd -m ensurepip --upgrade 2>&1 | Out-Null
        Write-Success "pip installed via ensurepip"
    } catch {
        Write-Doing "Downloading get-pip.py"
        $getpip = "$env:TEMP\get-pip.py"
        Invoke-WebRequest "https://bootstrap.pypa.io/get-pip.py" -OutFile $getpip -UseBasicParsing
        Write-Done
        Write-Doing "Running get-pip.py"
        & $PythonCmd $getpip --quiet
        Write-Done
        Write-Success "pip installed via get-pip.py"
    }
}

# Upgrade pip
Write-Doing "Upgrading pip to latest"
& $PythonCmd -m pip install --upgrade pip --quiet 2>&1 | Out-Null
Write-Done

# ─────────────────────────────────────────────────────────────────────────────
#  STEP 3 — Virtual environment
# ─────────────────────────────────────────────────────────────────────────────
Write-Host "`n[3/4]  Virtual environment (.venv)" -ForegroundColor White

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir   = Join-Path $ScriptDir ".venv"
$VenvPy    = Join-Path $VenvDir "Scripts\python.exe"

function Test-VenvValid ($venvPy, $minMajor, $minMinor) {
    if (-not (Test-Path $venvPy)) { return $false }
    return Test-PythonMinVersion $venvPy $minMajor $minMinor
}

if (Test-Path $VenvDir) {
    if (Test-VenvValid $VenvPy $MIN_MAJOR $MIN_MINOR) {
        $vVer = Get-PythonVersion $VenvPy
        Write-Success "Existing .venv is valid  (Python $vVer)"
    } else {
        Write-Warn "Existing .venv is outdated or broken — recreating..."
        Remove-Item -Recurse -Force $VenvDir
        Write-Doing "Creating new .venv"
        & $PythonCmd -m venv $VenvDir
        Write-Done
        Write-Success ".venv recreated"
    }
} else {
    Write-Doing "Creating .venv with $PythonCmd"
    & $PythonCmd -m venv $VenvDir
    Write-Done
    Write-Success ".venv created at $VenvDir"
}

# Activate
$ActivateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
if (-not (Test-Path $ActivateScript)) {
    Write-Err "Could not find .venv activation script at $ActivateScript"
    exit 1
}

# Allow running local scripts for this session
$oldPolicy = Get-ExecutionPolicy -Scope Process
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
. $ActivateScript
Write-Info "Virtual environment activated: $env:VIRTUAL_ENV"

# Upgrade pip inside venv
Write-Doing "Upgrading pip inside .venv"
python -m pip install --upgrade pip --quiet 2>&1 | Out-Null
Write-Done

# ─────────────────────────────────────────────────────────────────────────────
#  STEP 4 — Run the setup script
# ─────────────────────────────────────────────────────────────────────────────
Write-Host "`n[4/4]  Launching JFrog MCP Gateway setup" -ForegroundColor White
Write-Host ""

$SetupScript = Join-Path $ScriptDir "jfrog_mcp_setup.py"
if (-not (Test-Path $SetupScript)) {
    Write-Err "jfrog_mcp_setup.py not found in $ScriptDir"
    Write-Err "Make sure both files are in the same folder."
    exit 1
}

python $SetupScript

# Restore execution policy
Set-ExecutionPolicy -ExecutionPolicy $oldPolicy -Scope Process -Force
