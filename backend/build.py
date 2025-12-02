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
    
    # Limpiar builds anteriores
    for folder in ['build', 'dist']:
        folder_path = Path(folder)
        if folder_path.exists():
            print(f"Limpiando {folder}/...")
            shutil.rmtree(folder_path)
    
    # Configuración PyInstaller
    args = [
        'main.py',  # Entrypoint
        '--name', 'backend',
        '--onefile',  # Un solo ejecutable
        '--noconfirm',
        '--clean',
        
        # Hidden imports necesarios para uvicorn
        '--hidden-import', 'uvicorn',
        '--hidden-import', 'uvicorn.logging',
        '--hidden-import', 'uvicorn.loops',
        '--hidden-import', 'uvicorn.loops.auto',
        '--hidden-import', 'uvicorn.protocols',
        '--hidden-import', 'uvicorn.protocols.http',
        '--hidden-import', 'uvicorn.protocols.http.auto',
        '--hidden-import', 'uvicorn.protocols.http.httptools_impl',
        '--hidden-import', 'uvicorn.protocols.websockets',
        '--hidden-import', 'uvicorn.protocols.websockets.auto',
        '--hidden-import', 'uvicorn.lifespan',
        '--hidden-import', 'uvicorn.lifespan.on',
        
        # Hidden imports para FastAPI
        '--hidden-import', 'fastapi',
        '--hidden-import', 'pydantic',
        '--hidden-import', 'pydantic_settings',
        
        # Hidden imports para pygame
        '--hidden-import', 'pygame',
        
        # Agregar datos necesarios (si existen)
        # '--add-data', 'config;config',  # Descomentar si config/ es necesario
        
        # Mantener console para ver logs (cambiar a --noconsole si prefieres sin ventana)
        '--console',
        
        # Optimizaciones
        '--strip',  # Reducir tamaño
        '--optimize', '2',  # Nivel de optimización Python
    ]
    
    print("\nEjecutando PyInstaller...")
    print(f"Entrypoint: main.py")
    print(f"Output: dist/backend.exe")
    print()
    
    try:
        PyInstaller.__main__.run(args)
        
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

