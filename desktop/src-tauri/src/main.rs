#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use std::process::{Child, Command};
use std::sync::Mutex;
use std::path::{Path, PathBuf};
use std::io::ErrorKind;
use tauri::{AppHandle, Manager, State, WindowEvent};

/// Estructura para gestionar el proceso del backend Python
/// 
/// Este gestor lanza el backend FastAPI como un proceso hijo usando Python/uvicorn.
/// Actualmente usa Python directamente, pero está preparado para cambiar a un binario
/// sidecar en una segunda etapa si es necesario.
struct BackendProcess(Mutex<Option<Child>>);

/// Errores específicos del backend
#[derive(Debug)]
enum BackendError {
    PythonNotFound,
    BackendDirNotFound { tried: Vec<PathBuf> },
    SpawnFailed { source: std::io::Error, cmd: String },
}

impl std::fmt::Display for BackendError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            BackendError::PythonNotFound => {
                write!(f, "PYTHON_NOT_FOUND: Python interpreter not found (tried 'python' and 'py'). Please install Python 3.10+ and ensure it's in PATH.")
            }
            BackendError::BackendDirNotFound { tried } => {
                write!(f, "BACKEND_DIR_NOT_FOUND: Backend directory not found. Tried paths: {:?}", tried)
            }
            BackendError::SpawnFailed { source, cmd } => {
                write!(f, "SPAWN_FAILED: Failed to start backend with command '{}': {}", cmd, source)
            }
        }
    }
}

/// Detecta si estamos en modo desarrollo
fn is_dev_mode() -> bool {
    cfg!(debug_assertions)
}

/// Resuelve la ruta de la carpeta backend/ usando el orden de prioridades especificado.
/// 
/// Prioridad 1: Variable de entorno MINICARS_BACKEND_PATH (modo avanzado/debugging)
/// Prioridad 2: Recursos empaquetados de Tauri (modo producción) via path_resolver
/// Prioridad 3: Rutas de desarrollo (solo en modo desarrollo)
/// 
/// Args:
///   app: AppHandle de Tauri para acceder a path_resolver
/// 
/// Returns:
///   PathBuf del directorio backend/ o BackendError
fn resolve_backend_dir(app: &AppHandle) -> Result<PathBuf, BackendError> {
    let mut tried_paths = Vec::new();
    let is_dev = is_dev_mode();
    
    if is_dev {
        println!("[Tauri] Development mode detected");
    } else {
        println!("[Tauri] Production mode detected");
    }
    
    // Prioridad 1: Variable de entorno MINICARS_BACKEND_PATH
    if let Ok(env_path) = std::env::var("MINICARS_BACKEND_PATH") {
        let path = PathBuf::from(env_path);
        tried_paths.push(path.clone());
        if path.exists() && path.is_dir() && path.join("main.py").exists() {
            println!("[Tauri] Using backend from MINICARS_BACKEND_PATH: {:?}", path);
            return Ok(path);
        }
    }
    
    // Prioridad 2: Recursos empaquetados de Tauri (modo producción)
    if let Some(resource_path) = app.path_resolver().resolve_resource("backend") {
        tried_paths.push(resource_path.clone());
        if resource_path.exists() && resource_path.is_dir() && resource_path.join("main.py").exists() {
            println!("[Tauri] Using backend from Tauri resources: {:?}", resource_path);
            return Ok(resource_path);
        }
    }
    
    // Prioridad 3: Rutas de desarrollo (solo en modo desarrollo)
    if is_dev {
        // Intento 1: Workspace root desde CARGO_MANIFEST_DIR
        let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
        // manifest_dir = desktop/src-tauri
        // workspace_root = desktop/src-tauri/../.. = minicars-control-station/
        if let Some(workspace_root) = manifest_dir.parent().and_then(|p| p.parent()) {
            let dev_backend = workspace_root.join("backend");
            tried_paths.push(dev_backend.clone());
            if dev_backend.exists() && dev_backend.is_dir() && dev_backend.join("main.py").exists() {
                println!("[Tauri] Using backend from workspace root (dev): {:?}", dev_backend);
                return Ok(dev_backend);
            }
        }
        
        // Intento 2: Desde current_dir
        if let Ok(current_dir) = std::env::current_dir() {
            let backend_dir = if current_dir.ends_with("desktop") {
                current_dir.parent().map(|p| p.join("backend"))
            } else {
                Some(current_dir.join("backend"))
            };
            
            if let Some(dir) = backend_dir {
                tried_paths.push(dir.clone());
                if dir.exists() && dir.is_dir() && dir.join("main.py").exists() {
                    println!("[Tauri] Using backend from current_dir (dev fallback): {:?}", dir);
                    return Ok(dir);
                }
            }
        }
    }
    
    Err(BackendError::BackendDirNotFound { tried: tried_paths })
}

/// Encuentra el comando Python disponible en el sistema
/// 
/// Prueba primero `python`, luego `py` (común en Windows).
/// Retorna un error específico si no se encuentra Python.
fn find_python_command() -> Result<String, BackendError> {
    // Probar "python" primero
    match Command::new("python").arg("--version").output() {
        Ok(_) => {
            println!("[Tauri] Found Python command: python");
            return Ok("python".to_string());
        }
        Err(e) if e.kind() == ErrorKind::NotFound => {
            // python no encontrado, continuar
        }
        Err(e) => {
            // Otro error (permisos, etc.)
            eprintln!("[Tauri] Warning: Error checking 'python': {}", e);
        }
    }
    
    // Probar "py" (launcher de Python en Windows)
    match Command::new("py").arg("--version").output() {
        Ok(_) => {
            println!("[Tauri] Found Python command: py");
            return Ok("py".to_string());
        }
        Err(e) if e.kind() == ErrorKind::NotFound => {
            // py tampoco encontrado
        }
        Err(e) => {
            eprintln!("[Tauri] Warning: Error checking 'py': {}", e);
        }
    }
    
    Err(BackendError::PythonNotFound)
}

/// Inicia el backend usando Python + uvicorn
/// 
/// Ejecuta: python -m uvicorn main:app --host 0.0.0.0 --port 8000
/// (0.0.0.0 permite acceso desde la red, necesario para que Jetson se conecte)
/// 
/// Args:
///   backend_dir: Directorio del backend (debe contener main.py)
///   python_cmd: Comando Python a usar ("python" o "py")
/// 
/// Returns:
///   Child process del backend o BackendError con detalles completos
fn start_backend(backend_dir: &Path, python_cmd: &str) -> Result<Child, BackendError> {
    // Use 0.0.0.0 to listen on all interfaces, making it accessible from network (Jetson)
    let cmd_str = format!("{} -m uvicorn main:app --host 0.0.0.0 --port 8000", python_cmd);
    
    println!("[Tauri] Starting backend:");
    println!("  Backend path: {:?}", backend_dir);
    println!("  Command: {}", cmd_str);
    
    match Command::new(python_cmd)
        .current_dir(backend_dir)
        .arg("-m")
        .arg("uvicorn")
        .arg("main:app")
        .arg("--host")
        .arg("0.0.0.0")
        .arg("--port")
        .arg("8000")
        .spawn()
    {
        Ok(child) => {
            println!("[Tauri] Backend process started successfully (PID: {:?})", child.id());
            Ok(child)
        }
        Err(e) => {
            eprintln!("[Tauri] Failed to spawn backend process:");
            eprintln!("  Backend path: {:?}", backend_dir);
            eprintln!("  Command: {}", cmd_str);
            eprintln!("  Error: {} (kind: {:?})", e, e.kind());
            Err(BackendError::SpawnFailed {
                source: e,
                cmd: cmd_str,
            })
        }
    }
}

/// Comando Tauri para asegurar que el backend esté corriendo
/// 
/// Si el backend ya está corriendo, retorna Ok(()).
/// Si no está corriendo o murió, intenta iniciarlo.
/// 
/// Retorna un string con formato "ERROR_CODE: mensaje" para que el frontend pueda
/// diferenciar entre tipos de error.
#[tauri::command]
async fn ensure_backend_running(
    app: AppHandle,
    state: State<'_, BackendProcess>
) -> Result<(), String> {
    let mut process_guard = state.0.lock().map_err(|e| {
        format!("LOCK_ERROR: Failed to lock backend state: {}", e)
    })?;
    
    // Verificar si el proceso ya está corriendo
    if let Some(ref mut child) = *process_guard {
        match child.try_wait() {
            Ok(None) => {
                // Proceso todavía corriendo
                println!("[Tauri] Backend already running (PID: {:?})", child.id());
                return Ok(());
            }
            Ok(Some(status)) => {
                // Proceso terminó
                if let Some(code) = status.code() {
                    println!("[Tauri] Backend process exited with code: {}", code);
                } else {
                    println!("[Tauri] Backend process exited (no exit code available)");
                }
                *process_guard = None;
            }
            Err(e) => {
                // Error al verificar
                println!("[Tauri] Error checking backend process: {}", e);
                *process_guard = None;
            }
        }
    }
    
    // Necesitamos iniciar el backend
    // Resolver ruta usando AppHandle para acceder a path_resolver
    let backend_dir = resolve_backend_dir(&app).map_err(|e| {
        eprintln!("[Tauri] ERROR resolving backend directory: {}", e);
        e.to_string()
    })?;
    
    let python_cmd = find_python_command().map_err(|e| {
        eprintln!("[Tauri] ERROR finding Python: {}", e);
        e.to_string()
    })?;
    
    match start_backend(&backend_dir, &python_cmd) {
        Ok(child) => {
            println!("[Tauri] Backend started successfully (PID: {:?})", child.id());
            *process_guard = Some(child);
            Ok(())
        }
        Err(e) => {
            eprintln!("[Tauri] ERROR starting backend: {}", e);
            Err(e.to_string())
        }
    }
}

fn main() {
    tauri::Builder::default()
        .manage(BackendProcess(Mutex::new(None)))
        .invoke_handler(tauri::generate_handler![ensure_backend_running])
        .on_window_event(|event| {
            // Cleanup cuando se solicita cerrar la ventana
            if let WindowEvent::CloseRequested { .. } = event.event() {
                let app_handle = event.window().app_handle();
                
                // Mover el kill a un spawn para no bloquear el hilo principal
                tauri::async_runtime::spawn(async move {
                    if let Some(state) = app_handle.try_state::<BackendProcess>() {
                        if let Ok(mut process_guard) = state.0.lock() {
                            if let Some(mut child) = process_guard.take() {
                                println!("[Tauri] Stopping backend process...");
                                
                                // Intentar kill graceful
                                if let Err(e) = child.kill() {
                                    eprintln!("[Tauri] Error killing backend process: {}", e);
                                } else {
                                    // Esperar a que termine
                                    if let Err(e) = child.wait() {
                                        eprintln!("[Tauri] Error waiting for backend process: {}", e);
                                    } else {
                                        println!("[Tauri] Backend stopped successfully");
                                    }
                                }
                            }
                        }
                    }
                });
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
