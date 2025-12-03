<#
    Script: scripts/check-windows-env.ps1
    Propósito:
      - Verificar que el entorno de Windows tenga las dependencias mínimas para compilar Tauri/Rust en DESARROLLO LOCAL.
      - En CI (GitHub Actions) saltar la verificación y salir con código 0 para no bloquear el pipeline.
#>
Write-Host "== MiniCars Windows Env Check =="

# --- 1. Saltar el check cuando corremos en CI (GitHub Actions) -----------------
if ($env:CI -eq "true") {
    Write-Host "CI detectado (CI=$($env:CI))."
    Write-Host "Saltando verificación de entorno de Windows para no bloquear la pipeline."
    exit 0
}

Write-Host "Entorno CI NO detectado. Ejecutando verificación completa para desarrollo local..."
Write-Host ""

# --- 2. Verificar cl.exe (compilador de Visual C++) ---------------------------
$clCmd = Get-Command cl.exe -ErrorAction SilentlyContinue
$clPath = if ($clCmd) { $clCmd.Source } else { $null }
$hasError = $false
if (-not $clPath) {
    Write-Warning "No se encontró 'cl.exe' en el PATH."
    $hasError = $true
} else {
    Write-Host "cl.exe encontrado en: $clPath" -ForegroundColor Green
}

# --- 3. Verificar que no estemos usando link.exe de Git -----------------------
$linkCmd = Get-Command link.exe -ErrorAction SilentlyContinue
$linkPath = if ($linkCmd) { $linkCmd.Source } else { $null }
if (-not $linkPath) {
    Write-Warning "No se encontró 'link.exe' en el PATH."
    $hasError = $true
} else {
    Write-Host "link.exe encontrado en: $linkPath"
    if ($linkPath -like "*\Git\usr\bin\link.exe") {
        Write-Warning "Se detectó 'link.exe' de Git (no el linker de MSVC)."
        Write-Host ""
        Write-Host "Esto suele ocurrir cuando Git agrega su propia carpeta 'usr\bin' al PATH."
        Write-Host "Recomendación:"
        Write-Host "  - Ajusta el PATH para que la ruta del linker de Visual Studio (MSVC) aparezca antes que la de Git,"
        Write-Host "    o remueve '...\Git\usr\bin' del PATH."
        $hasError = $true
    }
}

if ($hasError) {
    Write-Host ""
    Write-Host "Para instalar los build tools mínimos de Visual Studio ejecuta:" -ForegroundColor Yellow
    Write-Host "  winget install --id Microsoft.VisualStudio.2022.BuildTools -e" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Asegúrate de seleccionar el workload 'Desktop development with C++' y el Windows 10/11 SDK." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "✅ Verificación de entorno Windows completada correctamente para desarrollo local."
exit 0
