# Verificar Versión de Python en Jetson

## Problema

Si ves el error:
```
ModuleNotFoundError: No module named 'dataclasses'
```

Significa que la Jetson está usando Python 3.6 o anterior. El código ahora es compatible con Python 3.6+, pero es mejor verificar.

## Verificar Versión

```bash
# Ver versión de Python 3
python3 --version

# O más detallado
python3 -c "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
```

**Requisito:** Python 3.6 o superior (recomendado: 3.8+)

## Verificar que stream_config.py Funciona

```bash
cd ~/minicars-control-station/jetson
python3 stream_config.py
```

**Deberías ver:**
```
[STREAM-CONFIG] ✓ Configuration valid
[STREAM-CONFIG]   Host: SKLNx.local
[STREAM-CONFIG]   Video Port: 5000
[STREAM-CONFIG]   Backend Port: 8000
...
```

## Si Python es Muy Antiguo (< 3.6)

Actualiza Python en la Jetson o usa un entorno virtual con Python más reciente:

```bash
# Opción 1: Instalar Python 3.8+ (si está disponible)
sudo apt update
sudo apt install python3.8 python3.8-venv

# Opción 2: Usar pyenv (avanzado)
# Ver: https://github.com/pyenv/pyenv
```

## Verificar en el Servicio systemd

El servicio `minicars-streamer.service` usa `/usr/bin/python3`. Verifica qué versión es:

```bash
/usr/bin/python3 --version
```

Si es muy antigua, puedes modificar el servicio para usar una versión específica:

```bash
# Editar servicio
sudo nano /etc/systemd/system/minicars-streamer.service

# Cambiar:
# ExecStart=/usr/bin/python3 ...
# Por:
# ExecStart=/usr/bin/python3.8 ...  (o la versión que tengas)
```

