"""
Build script para empaquetar el backend de MiniCars con PyInstaller.

Uso:
    python build.py

Output:
    dist/backend.exe - Backend standalone con todas las dependencias
"""
import sys
import PyInstaller.__main__
import shutil
from pathlib import Path

def build_backend():
    """Construye backend.exe con PyInstaller."""
    
    print("=" * 60)
    print("MiniCars Backend - PyInstaller Build")
    print("=" * 60)
    
    # Verificar que estamos en el directorio correcto
    if not Path('main.py').exists():
        print("ERROR: main.py no encontrado. Ejecuta desde backend/")
        sys.exit(1)
    
    # Limpiar builds anteriores
    for folder in ['build', 'dist']:
        folder_path = Path(folder)
        if folder_path.exists():
            print(f"Limpiando {folder}/...")
            shutil.rmtree(folder_path)
    
    # Verificar que config/ existe, si no, crear vacío
    config_dir = Path('config')
    if not config_dir.exists():
        print("Creando config/ con control_profile.json por defecto...")
        config_dir.mkdir(exist_ok=True)
        # Crear control_profile.json mínimo
        import json
        default_profile = {"active_mode": "normal"}
        (config_dir / 'control_profile.json').write_text(json.dumps(default_profile, indent=2))
    
    # Configuración PyInstaller - versión simplificada y robusta
    args = [
        'main.py',
        '--name', 'backend',
        '--onefile',
        '--noconfirm',
        '--clean',
        '--console',  # Mantener console para logs
        
        # Collect all submodules automáticamente
        '--collect-all', 'uvicorn',
        '--collect-all', 'fastapi',
        '--collect-all', 'pydantic',
        '--collect-all', 'pydantic_settings',
        
        # Hidden imports críticos
        '--hidden-import', 'pygame',
        
        # Agregar config/
        '--add-data', 'config' + (';config' if sys.platform == 'win32' else ':config'),
    ]
    
    print("\nEjecutando PyInstaller...")
    print(f"Usando: backend.spec")
    print(f"Output: dist/backend.exe")
    print()
    
    # Usar el spec file es más confiable que argumentos en línea
    try:
        PyInstaller.__main__.run(['backend.spec', '--noconfirm', '--clean'])
        
        print("\n" + "=" * 60)
        print("✓ Build completado exitosamente")
        print("=" * 60)
        
        # Mostrar info del archivo generado
        exe_path = Path("dist/backend.exe")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\nArchivo generado: {exe_path}")
            print(f"Tamaño: {size_mb:.1f} MB")
            print(f"\nPara probar:")
            print(f"  .\\dist\\backend.exe")
            print(f"  Debería iniciar en http://localhost:8000")
        
    except Exception as e:
        print(f"\n✗ Error durante el build: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    build_backend()

