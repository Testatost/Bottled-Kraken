param(
    [switch]$SkipTests,
    [switch]$RegenerateLock
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (-not $IsWindows -and $PSVersionTable.PSEdition -eq "Core") {
    throw "Dieser Release-Build muss unter Windows 10/11 ausgeführt werden."
}

$env:PYTHONUTF8 = "1"
Remove-Item Env:PYTHONHOME -ErrorAction SilentlyContinue
Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue

function Find-Python {
    $candidates = @(
        @{ exe = "py"; args = @("-3.13") },
        @{ exe = "py"; args = @("-3.12") },
        @{ exe = "python"; args = @() }
    )
    foreach ($candidate in $candidates) {
        $cmd = Get-Command $candidate.exe -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        try {
            $version = & $candidate.exe @($candidate.args + @("-c", "import struct, sys; print(sys.version_info[:3]); sys.exit(0 if struct.calcsize('P') == 8 else 1)")) 2>$null
            if ($LASTEXITCODE -eq 0 -and $version) {
                return @{ exe = $candidate.exe; args = $candidate.args }
            }
        } catch {}
    }
    throw "Python 3.13 oder 3.12 x64 wurde nicht gefunden. Installiere zuerst eine 64-Bit-Python-Version für Windows."
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [string]$FailureMessage
    )
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        if ($FailureMessage) { throw $FailureMessage }
        throw "Befehl fehlgeschlagen: $FilePath $($Arguments -join ' ')"
    }
}

function Test-KrakenRuntimeDependencies {
    $failureMessage = "Kraken-Abhaengigkeiten unvollstaendig - requirements.txt gegen kraken==7.0.3 abgleichen."

    # Kraken wird unter Windows weiterhin ohne automatische Abhaengigkeiten installiert,
    # aber coremltools ist im Lockfile explizit enthalten. Kraken braucht coremltools
    # nicht fuer Apple-CoreML-Inferenz, aber zum Lesen klassischer .mlmodel-Dateien.
    $pipCheckOutput = & $VenvPython -m pip check 2>&1
    $pipCheckExit = $LASTEXITCODE
    if ($pipCheckExit -ne 0) {
        $pipCheckOutput | ForEach-Object { Write-Error $_ }
        throw $failureMessage
    }
    if ($pipCheckOutput) {
        $pipCheckOutput | ForEach-Object { Write-Host $_ }
    }

    Invoke-Checked $VenvPython @("-c", "import kraken; print('kraken OK')") $failureMessage
    Invoke-Checked $VenvPython @("-c", "import coremltools; from coremltools.models import MLModel; from coremltools.proto import NeuralNetwork_pb2; print('coremltools OK')") $failureMessage
    Invoke-Checked $VenvPython @("-c", "import pkg_resources, backports.tarfile, faster_whisper; print('windows runtime imports OK')") $failureMessage
}

$PythonLauncher = Find-Python
$Venv = Join-Path $Root ".venv-win"
$VenvPython = Join-Path $Venv "Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Invoke-Checked $PythonLauncher.exe @($PythonLauncher.args + @("-m", "venv", $Venv)) "Virtuelle Windows-Buildumgebung konnte nicht erstellt werden."
}

Invoke-Checked $VenvPython @("-m", "pip", "install", "--upgrade", "pip", "wheel") "pip/wheel konnten nicht aktualisiert werden."
Invoke-Checked $VenvPython @("-m", "pip", "install", "setuptools==80.10.2", "backports.tarfile==1.2.0") "setuptools/backports konnten nicht installiert werden."

if ($RegenerateLock -or -not (Test-Path "requirements-lock-windows.txt")) {
    Invoke-Checked $VenvPython @("-m", "pip", "install", "-r", "requirements.txt") "requirements.txt konnte nicht installiert werden."
    Invoke-Checked $VenvPython @("-m", "pip", "install", "--no-deps", "kraken==7.0.3") "kraken==7.0.3 konnte nicht installiert werden."
    Invoke-Checked $VenvPython @("-m", "pip", "install", "pyinstaller", "pytest") "PyInstaller/pytest konnten nicht installiert werden."
    Test-KrakenRuntimeDependencies
    & $VenvPython -m pip freeze | Set-Content -Encoding UTF8 requirements-lock-windows.generated.txt
    if ($LASTEXITCODE -ne 0) { throw "requirements-lock-windows.generated.txt konnte nicht erzeugt werden." }
    Write-Host "Hinweis: requirements-lock-windows.generated.txt wurde erzeugt. Vor einem Release manuell prüfen und nach requirements-lock-windows.txt übernehmen."
} else {
    Invoke-Checked $VenvPython @("-m", "pip", "install", "-r", "requirements-lock-windows.txt") "requirements-lock-windows.txt konnte nicht installiert werden."
    Invoke-Checked $VenvPython @("-m", "pip", "install", "--no-deps", "kraken==7.0.3") "kraken==7.0.3 konnte nicht installiert werden."
    Test-KrakenRuntimeDependencies
}

if (-not $SkipTests) {
    $hadQtQpaPlatform = Test-Path Env:QT_QPA_PLATFORM
    $previousQtQpaPlatform = $env:QT_QPA_PLATFORM
    try {
        $env:QT_QPA_PLATFORM = "offscreen"
        Invoke-Checked $VenvPython @("-m", "pytest", "-v", "-rs") "pytest ist fehlgeschlagen."
    } finally {
        if ($hadQtQpaPlatform) {
            $env:QT_QPA_PLATFORM = $previousQtQpaPlatform
        } else {
            Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
        }
    }
}

Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
Invoke-Checked $VenvPython @("-m", "PyInstaller", "--clean", "--noconfirm", "main.spec") "PyInstaller-Build fehlgeschlagen."

Write-Host ""
Write-Host "Build abgeschlossen: $Root\dist\Bottled Kraken.exe"
