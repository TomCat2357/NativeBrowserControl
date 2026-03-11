# ==========================================
# Scoop / uv / Python 3.13 / venv / ensurepip
# Python is managed by uv (NOT Scoop)
# Always run in USER HOME
# PowerShell-safe / PATH-independent
# ==========================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "=== Install Scoop, uv, Python 3.13, venv, and ensurepip ==="

# -------------------------------------------------
# [PRE] Always move to user home directory
# -------------------------------------------------
Write-Host "[PRE] Switching to user home directory..."
Set-Location $HOME
Write-Host "Current directory: $(Get-Location)"

# -------------------------------------------------
# Session-only environment: uv native TLS
# -------------------------------------------------
Write-Host "[0/6] Enabling UV_NATIVE_TLS=1 (session only)..."
$env:UV_NATIVE_TLS = "1"

# ----------------
# Scoop install
# ----------------
if (-not (Get-Command scoop -ErrorAction SilentlyContinue)) {
    Write-Host "[1/6] Installing Scoop..."
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force
    Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
} else {
    Write-Host "[1/6] Scoop already installed. Skipping."
}

scoop update
scoop install git

# ----------------
# uv install (via Scoop)
# ----------------
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "[2/6] Installing uv via Scoop..."
    scoop install uv
} else {
    Write-Host "[2/6] uv already installed. Skipping."
}

# ----------------
# Python 3.13 install (via uv)
# ----------------
Write-Host "[3/6] Installing Python 3.13 via uv..."
uv python install 3.13
uv python pin 3.13

# ----------------
# Create virtual environment (Python 3.13)
# Always under USER HOME
# ----------------
$VenvPath = Join-Path $HOME ".venv"

Write-Host "[4/6] Creating virtual environment at $VenvPath ..."
uv venv $VenvPath --python 3.13

# ----------------
# Activate virtual environment
# ----------------
Write-Host "[5/6] Activating virtual environment..."
. "$VenvPath\Scripts\Activate.ps1"

# ----------------
# ensurepip (INSIDE venv, PATH-independent)
# ----------------
Write-Host "[6/6] Running ensurepip in virtual environment..."
python -m ensurepip --upgrade

# ----------------
# Install NativeBrowserControl (from GitHub)
# ----------------
Write-Host "[EXTRA] Installing NativeBrowserControl from GitHub..."
python -m pip install git+https://github.com/TomCat2357/NativeBrowserControl.git

# ----------------
# Verification (SAFE)
# ----------------
Write-Host ""
Write-Host "=== Verification ==="
python --version
python -m pip --version
uv python list
uv --version

Write-Host ""
Write-Host "UV_NATIVE_TLS=$env:UV_NATIVE_TLS (session only)"
Write-Host "VIRTUAL_ENV=$env:VIRTUAL_ENV"
Write-Host "Current directory: $(Get-Location)"
Write-Host "All done."
