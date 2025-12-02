param()

Write-Host "Verificando entorno de compilación para Tauri/Rust en Windows..." -ForegroundColor Cyan

# Compatible con PowerShell 5.1+ (sin operador ?.)
$clCmd = Get-Command cl.exe -ErrorAction SilentlyContinue
$clPath = if ($clCmd) { $clCmd.Source } else { $null }

$linkCmd = Get-Command link.exe -ErrorAction SilentlyContinue
$linkPath = if ($linkCmd) { $linkCmd.Source } else { $null }

$hasError = $false

if (-not $clPath) {
    Write-Host "No se encontró 'cl.exe' en el PATH." -ForegroundColor Red
    $hasError = $true
} else {
    Write-Host "cl.exe encontrado en: $clPath" -ForegroundColor Green
}

if (-not $linkPath) {
    Write-Host "No se encontró 'link.exe' en el PATH." -ForegroundColor Red
    $hasError = $true
} else {
    Write-Host "link.exe encontrado en: $linkPath" -ForegroundColor Green
}

if ($hasError) {
    Write-Host ""
    Write-Host "Para instalar los build tools mínimos de Visual Studio ejecuta:" -ForegroundColor Yellow
    Write-Host "  winget install --id Microsoft.VisualStudio.2022.BuildTools -e" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Asegúrate de seleccionar el workload 'Desktop development with C++' y el Windows 10/11 SDK." -ForegroundColor Yellow
    exit 1
}

Write-Host "Entorno de compilación MSVC detectado correctamente." -ForegroundColor Green
