#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use std::process::{Child, Command};
use std::sync::Mutex;
use std::path::{Path, PathBuf};
use std::io::ErrorKind;
use tauri::{Manager, State, WindowEvent};

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
                write!(f, "PYTHON_NOT_FOUND: Python not found. Please install Python 3.10+ and ensure it's in PATH.")
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

/// Resuelve la ruta de la carpeta backend/
/// 
/// En modo desarrollo:
/// 1. Variable de entorno MINICARS_BACKEND_PATH
/// 2. Workspace root calculado desde CARGO_MANIFEST_DIR (../backend desde desktop/src-tauri)
/// 
/// En modo producción:
/// 1. Variable de entorno MINICARS_BACKEND_PATH
/// 2. Carpeta backend/ al lado del ejecutable
/// 3. Carpeta ../backend/ desde el ejecutable
fn resolve_backend_dir() -> Result<PathBuf, BackendError> {
    let mut tried_paths = Vec::new();
    let is_dev = is_dev_mode();
    
    if is_dev {
        println!("[Tauri] Development mode detected");
    } else {
        println!("[Tauri] Production mode detected");
    }
    
    // Prioridad 1: Variable de entorno MINICARS_BACKEND_PATH (tanto dev como prod)
    if let Ok(env_path) = std::env::var("MINICARS_BACKEND_PATH") {
        let path = PathBuf::from(env_path);
        tried_paths.push(path.clone());
        if path.exists() && path.join("main.py").exists() {
            println!("[Tauri] Using backend from MINICARS_BACKEND_PATH: {:?}", path);
            return Ok(path);
        }
    }
    
    if is_dev {
        // En desarrollo: usar CARGO_MANIFEST_DIR para encontrar el workspace root
        let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
        // manifest_dir = desktop/src-tauri
        // workspace_root = desktop/src-tauri/../.. = minicars-control-station/
        if let Some(workspace_root) = manifest_dir.parent().and_then(|p| p.parent()) {
            let dev_backend = workspace_root.join("backend");
            tried_paths.push(dev_backend.clone());
            if dev_backend.exists() && dev_backend.join("main.py").exists() {
                println!("[Tauri] Using backend from workspace root (dev): {:?}", dev_backend);
                return Ok(dev_backend);
            }
        }
        
        // Fallback: intentar desde current_dir (por si acaso)
        if let Ok(current_dir) = std::env::current_dir() {
            let backend_dir = if current_dir.ends_with("desktop") {
                current_dir.parent().map(|p| p.join("backend"))
            } else {
                Some(current_dir.join("backend"))
            };
            
            if let Some(dir) = backend_dir {
                tried_paths.push(dir.clone());
                if dir.exists() && dir.join("main.py").exists() {
                    println!("[Tauri] Using backend from current_dir (dev fallback): {:?}", dir);
                    return Ok(dir);
                }
            }
        }
    } else {
        // En producción: buscar junto al ejecutable
        if let Ok(exe_path) = std::env::current_exe() {
            if let Some(exe_dir) = exe_path.parent() {
                // Prioridad 2: backend/ al lado del ejecutable
                let backend_dir = exe_dir.join("backend");
                tried_paths.push(backend_dir.clone());
                if backend_dir.exists() && backend_dir.join("main.py").exists() {
                    println!("[Tauri] Using backend from exe directory: {:?}", backend_dir);
                    return Ok(backend_dir);
                }
                
                // Prioridad 3: ../backend desde el ejecutable
                if let Some(parent_dir) = exe_dir.parent() {
                    let backend_dir = parent_dir.join("backend");
                    tried_paths.push(backend_dir.clone());
                    if backend_dir.exists() && backend_dir.join("main.py").exists() {
                        println!("[Tauri] Using backend from parent directory: {:?}", backend_dir);
                        return Ok(backend_dir);
                    }
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
/// Ejecuta: python -m uvicorn main:app --host 127.0.0.1 --port 8000
fn start_backend(backend_dir: &Path, python_cmd: &str) -> Result<Child, BackendError> {
    println!("[Tauri] Starting backend from: {:?} using {}", backend_dir, python_cmd);
    
    let cmd_str = format!("{} -m uvicorn main:app --host 127.0.0.1 --port 8000", python_cmd);
    
    Command::new(python_cmd)
        .current_dir(backend_dir)
        .arg("-m")
        .arg("uvicorn")
        .arg("main:app")
        .arg("--host")
        .arg("127.0.0.1")
        .arg("--port")
        .arg("8000")
        .spawn()
        .map_err(|e| BackendError::SpawnFailed {
            source: e,
            cmd: cmd_str,
        })
}

/// Comando Tauri para asegurar que el backend esté corriendo
/// 
/// Si el backend ya está corriendo, retorna Ok(()).
/// Si no está corriendo o murió, intenta iniciarlo.
/// 
/// Retorna un string con formato "ERROR_CODE: mensaje" para que el frontend pueda
/// diferenciar entre tipos de error.
#[tauri::command]
async fn ensure_backend_running(state: State<'_, BackendProcess>) -> Result<(), String> {
    let mut process_guard = state.0.lock().map_err(|e| format!("LOCK_ERROR: Failed to lock backend state: {}", e))?;
    
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
                println!("[Tauri] Backend process exited with status: {:?}", status);
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
    let backend_dir = resolve_backend_dir().map_err(|e| {
        eprintln!("[Tauri] ERROR: {}", e);
        e.to_string()
    })?;
    
    let python_cmd = find_python_command().map_err(|e| {
        eprintln!("[Tauri] ERROR: {}", e);
        e.to_string()
    })?;
    
    match start_backend(&backend_dir, &python_cmd) {
        Ok(child) => {
            println!("[Tauri] Backend started successfully (PID: {:?})", child.id());
            *process_guard = Some(child);
            Ok(())
        }
        Err(e) => {
            eprintln!("[Tauri] ERROR: {}", e);
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
