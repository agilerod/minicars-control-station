# PowerShell script para iniciar el receptor GStreamer en Windows
# Este script puede ser llamado desde Tauri o ejecutado manualmente

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("start", "stop")]
    [string]$Action = "start"
)

$ErrorActionPreference = "Stop"

# Ruta al ejecutable de GStreamer
$GstLaunch = "C:\Program Files\gstreamer\1.0\mingw_x86_64\bin\gst-launch-1.0.exe"

# Verificar que GStreamer está instalado
if (-not (Test-Path $GstLaunch)) {
    Write-Error "GStreamer no encontrado en: $GstLaunch"
    Write-Host "Por favor, instala GStreamer desde https://gstreamer.freedesktop.org/download/"
    exit 1
}

if ($Action -eq "start") {
    Write-Host "[minicars-receiver] Iniciando receptor GStreamer..."
    
    # Pipeline GStreamer para recibir video RTP/H264
    $pipeline = @"
"$GstLaunch" -v udpsrc port=5000 caps="application/x-rtp,media=video,encoding-name=H264,payload=96,clock-rate=90000" ! rtpjitterbuffer latency=20 ! rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! autovideosink sync=false
"@
    
    try {
        # Ejecutar en background
        Start-Process powershell -ArgumentList "-NoExit", "-Command", $pipeline
        Write-Host "[minicars-receiver] Receptor GStreamer iniciado"
        exit 0
    }
    catch {
        Write-Error "Error al iniciar receptor GStreamer: $_"
        exit 1
    }
}
elseif ($Action -eq "stop") {
    Write-Host "[minicars-receiver] Deteniendo procesos de GStreamer..."
    
    try {
        # Buscar y terminar procesos de gst-launch relacionados con el receptor
        $processes = Get-Process | Where-Object {
            $_.ProcessName -like "*gst-launch*" -or
            $_.CommandLine -like "*udpsrc port=5000*"
        }
        
        if ($processes) {
            $processes | Stop-Process -Force
            Write-Host "[minicars-receiver] Procesos de GStreamer detenidos"
        }
        else {
            Write-Host "[minicars-receiver] No se encontraron procesos de receiver corriendo"
        }
        exit 0
    }
    catch {
        Write-Error "Error al detener receptor GStreamer: $_"
        exit 1
    }
}

