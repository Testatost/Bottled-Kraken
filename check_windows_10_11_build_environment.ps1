$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host "Bottled Kraken – Windows-10/11-Buildumgebung prüfen"
Write-Host ""

function Test-PythonCandidate {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [string[]]$Arguments = @()
    )
    $probe = "import platform, struct, sys; print(sys.executable); print(platform.platform()); print(sys.version); print(str(struct.calcsize('P') * 8) + '-bit'); sys.exit(0 if struct.calcsize('P') == 8 else 1)"
    try {
        & $Executable @($Arguments + @("-c", $probe))
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

$pythonOk = $false
if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonOk = (Test-PythonCandidate "py" @("-3.13")) -or (Test-PythonCandidate "py" @("-3.12"))
}
if (-not $pythonOk -and (Get-Command python -ErrorAction SilentlyContinue)) {
    $pythonOk = Test-PythonCandidate "python"
}
if (-not $pythonOk) {
    throw "Keine verwendbare 64-Bit-Installation von Python 3.13 oder Python 3.12 gefunden."
}

Write-Host ""
Write-Host "Projektpfad: $Root"
if ($Root.Length -gt 80) {
    Write-Warning "Der Projektpfad ist lang. Für PyInstaller-Builds ist ein kurzer Pfad wie C:\bk robuster."
}

$longPathKey = "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem"
try {
    $longPathsEnabled = (Get-ItemProperty -Path $longPathKey -Name LongPathsEnabled -ErrorAction Stop).LongPathsEnabled
} catch {
    $longPathsEnabled = 0
}
if ($longPathsEnabled -ne 1) {
    Write-Warning "Windows-Langpfade sind nicht aktiviert. Bei sehr tiefen PyInstaller-Zwischenpfaden kann die 260-Zeichen-Grenze greifen."
} else {
    Write-Host "Windows-Langpfade: aktiviert"
}

$iconPath = Join-Path $Root "icon.ico"
if (Test-Path $iconPath) {
    Write-Host "icon.ico: vorhanden"
} else {
    Write-Warning "icon.ico fehlt. main.spec baut trotzdem, die fertige EXE erhält dann aber kein eigenes Programmsymbol."
}

$vswherePath = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Installer\vswhere.exe"
if (Test-Path $vswherePath) {
    $vcInstall = & $vswherePath -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath 2>$null
    if ($LASTEXITCODE -eq 0 -and $vcInstall) {
        Write-Host "Visual C++ Build Tools: gefunden ($vcInstall)"
    } else {
        Write-Warning "Visual C++ Build Tools wurden nicht gefunden. Pakete ohne passende Wheels koennen dann nicht aus Quellcode gebaut werden."
    }
} else {
    Write-Warning "vswhere.exe wurde nicht gefunden. Installiere bei Bedarf die Visual C++ Build Tools."
}

Write-Host ""
Write-Host "WSL-Status:"
$wsl = Get-Command wsl.exe -ErrorAction SilentlyContinue
if ($wsl) {
    wsl.exe --status
} else {
    Write-Warning "wsl.exe wurde nicht gefunden. eScriptorium kann erst nach Aktivierung von WSL2 installiert werden."
    Write-Host "Installation als Administrator: wsl --install; danach Windows neu starten."
}

Write-Host ""
Write-Host "PyInstaller-Hinweis: Die Windows-EXE muss unter Windows gebaut werden; ein Linux-Build erzeugt keine Windows-EXE."
