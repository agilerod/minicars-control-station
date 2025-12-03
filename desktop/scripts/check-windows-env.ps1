<#
    Script:  scripts/check-windows-env.ps1
    Propósito:
      - Verificar que el entorno de Windows tenga las dependencias mínimas
        para compilar la app de escritorio (Tauri + Rust) en DESARROLLO LOCAL.
      - En CI (GitHub Actions) NO debe fallar: allí confiamos en la imagen
        oficial de GitHub y dejamos que el build de Tauri falle solo si hay
        un problema real de compilación.

    Comportamiento:
      - Si detecta CI=true (GitHub Actions u otro), se limita a informar
        y termina con código 0.
      - En local, comprueba:
          * que exista cl.exe en el PATH (MSVC)
          * que el link.exe que se use no sea el de Git
#>

Write-Host "== MiniCars Windows Env Check =="

# --- 1. Saltar el check cuando corremos en CI (GitHub Actions) -----------------
if ($env:CI -eq "true") {
    Write-Host "Entorno CI detectado (CI=$($env:CI))."
    Write-Host "Saltando verificación de entorno de Windows para no bloquear la pipeline."
    exit 0
}

Write-Host "Entorno CI NO detectado. Ejecutando verificación completa para desarrollo local..."
Write-Host ""

# --- 2. Verificar cl.exe (compilador de Visual C++) ---------------------------

# Buscar cl.exe en el PATH
$clExe = Get-Command cl.exe -ErrorAction SilentlyContinue

if (-not $clExe) {
    Write-Warning "No se encontró 'cl.exe' en el PATH."
    Write-Host ""
    Write-Host "Para desarrollar y compilar Tauri/Rust en Windows necesitas:"
    Write-Host "  - Visual Studio Build Tools 2022"
    Write-Host "  - Workload: 'Desktop development with C++'"
    Write-Host "  - Windows 10/11 SDK"
    Write-Host ""
    Write-Host "Puedes instalarlos con (PowerShell):"
    Write-Host "  winget install --id Microsoft.VisualStudio.2022.BuildTools -e"
    Write-Host "y durante la instalación seleccionar:"
    Write-Host "  'Desktop development with C++' + Windows 10/11 SDK."
    Write-Host ""
    throw "No se encontró 'cl.exe' en el PATH. Configura Visual Studio Build Tools antes de continuar."
}

Write-Host "OK: cl.exe encontrado en: $($clExe.Source)"
Write-Host ""

# --- 3. Verificar que no estemos usando link.exe de Git -----------------------

$linkExe = Get-Command link.exe -ErrorAction SilentlyContinue

if ($linkExe) {
    $linkPath = $linkExe.Source
    Write-Host "link.exe detectado en: $linkPath"

    if ($linkPath -like "*\Git\usr\bin\link.exe") {
        Write-Warning "Se detectó 'link.exe' de Git (no el linker de MSVC)."
        Write-Host ""
        Write-Host "Esto suele ocurrir cuando Git agrega su propia carpeta 'usr\bin' al PATH."
        Write-Host "Recomendación:"
        Write-Host "  - Ajusta el PATH para que la ruta del linker de Visual Studio (MSVC)"
        Write-Host "    aparezca antes que la de Git, o remueve '...\Git\usr\bin' del PATH."
        Write-Host ""
        throw "link.exe de Git detectado. Ajusta el PATH para usar el linker de Visual Studio."
    }
} else {
    Write-Warning "No se encontró 'link.exe'. Normalmente se instala junto con MSVC."
}

Write-Host ""
Write-Host "✅ Verificación de entorno Windows completada correctamente para desarrollo local."
exit 0

