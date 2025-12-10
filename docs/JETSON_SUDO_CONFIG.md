# Configurar Sudo Sin Contraseña para nvargus-daemon (Opcional)

## Problema

El `stream_supervisor.py` intenta reiniciar `nvargus-daemon` antes de iniciar el pipeline GStreamer para evitar errores de captura. Sin embargo, esto requiere `sudo` con contraseña, lo cual no funciona cuando el servicio se ejecuta desde systemd.

## Solución: Configurar Sudoers

Si quieres que el supervisor pueda reiniciar `nvargus-daemon` automáticamente, puedes configurar sudoers para permitir ese comando específico sin contraseña.

### Paso 1: Editar Sudoers

```bash
# En la Jetson
sudo visudo
```

### Paso 2: Agregar Regla

Agrega esta línea al final del archivo (reemplaza `jetson-rod` con tu usuario si es diferente):

```
jetson-rod ALL=(ALL) NOPASSWD: /bin/systemctl restart nvargus-daemon
```

### Paso 3: Guardar y Salir

- En `nano`: `Ctrl+X`, luego `Y`, luego `Enter`
- En `vi`: `:wq`

### Paso 4: Verificar

```bash
# Probar que funciona sin contraseña
sudo -n systemctl restart nvargus-daemon

# Si no pide contraseña y funciona, está bien configurado
```

## Alternativa: Deshabilitar Reinicio de nvargus-daemon

Si prefieres NO reiniciar `nvargus-daemon` automáticamente, el supervisor continuará funcionando. El reinicio es opcional y solo ayuda a evitar errores de captura en algunos casos.

El código actual ya maneja el fallo del reinicio de forma elegante: si falla, simplemente continúa e intenta iniciar el pipeline de todas formas.

## Nota de Seguridad

La regla de sudoers es específica solo para ese comando (`systemctl restart nvargus-daemon`), por lo que es relativamente segura. Solo permite reiniciar ese servicio específico, no otros comandos administrativos.

