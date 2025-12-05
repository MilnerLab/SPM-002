$ErrorActionPreference = "Stop"

# Always work relative to the location of this script
$repoRoot = $PSScriptRoot
Set-Location $repoRoot

# -------------------------------------------------------------------
# Paths and files
# -------------------------------------------------------------------
# 32-bit acquisition venv (lives inside acquisition/)
$acqVenvPath          = Join-Path $repoRoot "acquisition\.venv32"
$acqRequirementsFile  = Join-Path $repoRoot "acquisition\_requirements_acquisition.txt"
$acqPythonSpec        = "-3.13-32"   # 32-bit Python, adjust if needed

# 64-bit phase_control / analysis venv (lives inside phase_control/)
$phaseVenvPath        = Join-Path $repoRoot "phase_control\.venv64"
$phaseRequirementsFile = Join-Path $repoRoot "phase_control\_requirements_phase_control.txt"  # main project reqs
$phasePythonSpec      = "-3.13"     # 64-bit Python, adjust if needed (e.g. "-3.11")

# VS Code extensions file (same as before)
$extensionsFile       = Join-Path $repoRoot "_extensions.txt"


function Setup-Venv {
    param(
        [Parameter(Mandatory = $true)]
        [string] $VenvPath,

        [Parameter(Mandatory = $true)]
        [string] $PythonSpec,

        [Parameter(Mandatory = $true)]
        [string] $RequirementsFile
    )

    Write-Host "=== Creating/checking virtual environment '$VenvPath' ==="

    if (-not (Test-Path $VenvPath)) {
        Write-Host "Creating virtual environment with 'py $PythonSpec -m venv'..."
        & py $PythonSpec -m venv $VenvPath
    } else {
        Write-Host "Virtual environment already exists, skipping creation."
    }

    # Activate
    $activateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
    if (-not (Test-Path $activateScript)) {
        throw "Activate script not found at '$activateScript'."
    }

    Write-Host "=== Activating virtual environment '$VenvPath' ==="
    & $activateScript
    Write-Host "Virtual env: $env:VIRTUAL_ENV"

    # Upgrade pip
    Write-Host "=== Upgrading pip in '$VenvPath' ==="
    python -m pip install --upgrade pip

    # Install requirements
    if (Test-Path $RequirementsFile) {
        Write-Host "=== Installing Python packages from '$RequirementsFile' ==="
        python -m pip install -r $RequirementsFile
    } else {
        Write-Warning "Requirements file '$RequirementsFile' not found. Skipping package install."
    }
}

# -------------------------------------------------------------------
# 1) Setup acquisition (32-bit) environment
# -------------------------------------------------------------------
Write-Host "##############################"
Write-Host " Setting up 32-bit acquisition"
Write-Host "##############################"

Setup-Venv -VenvPath $acqVenvPath -PythonSpec $acqPythonSpec -RequirementsFile $acqRequirementsFile

# Expose PYTHON32_PATH for the analysis client (current session)
$python32Exe = Join-Path $acqVenvPath "Scripts\python.exe"
$python32Exe = (Resolve-Path $python32Exe).Path
$env:PYTHON32_PATH = $python32Exe
Write-Host "PYTHON32_PATH set to '$python32Exe'."

# -------------------------------------------------------------------
# 2) Setup phase_control / analysis (64-bit) environment
# -------------------------------------------------------------------
Write-Host ""
Write-Host "#########################################"
Write-Host " Setting up 64-bit phase_control/analysis"
Write-Host "#########################################"

Setup-Venv -VenvPath $phaseVenvPath -PythonSpec $phasePythonSpec -RequirementsFile $phaseRequirementsFile

# At this point, the *last* activated venv is the 64-bit one.

# -------------------------------------------------------------------
# 3) Install VS Code extensions (once, independent of venv)
# -------------------------------------------------------------------
Write-Host ""
Write-Host "=== Installing VS Code extensions (if any) ==="

if (Test-Path $extensionsFile) {
    if (-not (Get-Command code -ErrorAction SilentlyContinue)) {
        Write-Warning "'code' CLI (VS Code) not found in PATH. Skipping extension install."
    } else {
        Get-Content $extensionsFile | ForEach-Object {
            $ext = $_.Trim()
            if ($ext -and -not $ext.StartsWith("#")) {
                Write-Host "Installing VS Code extension '$ext'..."
                code --install-extension $ext
            }
        }
    }
} else {
    Write-Warning "Extensions file '$extensionsFile' not found. Skipping VS Code extension install."
}

Write-Host ""
Write-Host "=== Setup finished. 64-bit venv '$phaseVenvPath' is active in this PowerShell session. ==="
Write-Host "You can now run 'python -m analysis.plot' to start the live spectrum plot."
