# Deployment Tools

Este directorio contiene herramientas y plantillas para el deployment a la Jetson Nano.

## Archivos

- `deploy_to_jetson_template.sh` - Plantilla del script de deployment que debe copiarse a la Jetson

## Uso

### Primera vez: Copiar script a Jetson

Desde tu laptop (Windows PowerShell):

```powershell
scp deploy_to_jetson.sh jetson-rod@<JETSON_IP>:/home/jetson-rod/
```

O si prefieres usar la plantilla:

```powershell
scp tools/deploy/deploy_to_jetson_template.sh jetson-rod@<JETSON_IP>:/home/jetson-rod/deploy_to_jetson.sh
```

### En la Jetson: Hacer ejecutable

```bash
chmod +x ~/deploy_to_jetson.sh
```

### Ejecutar deployment

Desde la laptop:

```powershell
ssh jetson-rod@<JETSON_IP> "~/deploy_to_jetson.sh"
```

O desde la Jetson directamente:

```bash
~/deploy_to_jetson.sh
```

## Notas

- El script principal `deploy_to_jetson.sh` está en la raíz del repositorio
- Esta plantilla es una copia portable que puede usarse si el script principal no está disponible
- Ver `jetson/README.md` para instrucciones completas de deployment

