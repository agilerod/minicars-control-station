#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use std::process::{Child, Command};
use std::sync::Mutex;
use std::path::{Path, PathBuf};
use tauri::{Manager, State};

/// Estructura para gestionar el proceso del backend Python
struct BackendProcess(Mutex<Option<Child>>);

/// Resuelve la ruta de la carpeta backend/
fn resolve_backend_dir() -> Option<PathBuf> {
    // Prioridad 1: Variable de entorno MINICARS_BACKEND_PATH
    if let Ok(env_path) = std::env::var("MINICARS_BACKEND_PATH") {
        let path = PathBuf::from(env_path);
        if path.exists() && path.join("minicars_backend").exists() {
            println!("[Tauri] Using backend from MINICARS_BACKEND_PATH: {:?}", path);
            return Some(path);
        }
    }
    
    // Prioridad 2: Carpeta backend/ al lado del ejecutable
    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            let backend_dir = exe_dir.join("backend");
            if backend_dir.exists() && backend_dir.join("minicars_backend").exists() {
                println!("[Tauri] Using backend from exe directory: {:?}", backend_dir);
                return Some(backend_dir);
            }
            
            // Prioridad 3: ../backend (para estructura de dev/instalador)
            let backend_dir_parent = exe_dir.parent().and_then(|p| Some(p.join("backend")));
            if let Some(dir) = backend_dir_parent {
                if dir.exists() && dir.join("minicars_backend").exists() {
                    println!("[Tauri] Using backend from parent directory: {:?}", dir);
                    return Some(dir);
                }
            }
        }
    }
    
    None
}

/// Inicia el backend usando Python + uvicorn
fn start_backend(backend_dir: &Path) -> std::io::Result<Child> {
    println!("[Tauri] Starting backend from: {:?}", backend_dir);
    
    Command::new("python")
        .current_dir(backend_dir)
        .args(&[
            "-m",
            "uvicorn",
            "minicars_backend.api:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ])
        .spawn()
}

fn main() {
    let mut backend_child: Option<Child> = None;
    
    // Solo en modo producción, intentar lanzar el backend
    #[cfg(not(debug_assertions))]
    {
        println!("[Tauri] Production mode - attempting to start backend...");
        
        match resolve_backend_dir() {
            Some(backend_dir) => {
                match start_backend(&backend_dir) {
                    Ok(child) => {
                        println!("[Tauri] Backend started successfully (PID: {:?})", child.id());
                        backend_child = Some(child);
                    }
                    Err(e) => {
                        eprintln!("[Tauri] ERROR: Failed to start backend: {}", e);
                        eprintln!("[Tauri] Make sure Python 3.10+ is installed and in PATH.");
                        eprintln!("[Tauri] The app will start but backend features won't work.");
                    }
                }
            }
            None => {
                eprintln!("[Tauri] ERROR: backend/ directory not found!");
                eprintln!("[Tauri] Searched in:");
                eprintln!("[Tauri]   - MINICARS_BACKEND_PATH environment variable");
                eprintln!("[Tauri]   - backend/ next to executable");
                eprintln!("[Tauri]   - ../backend/ from executable");
                eprintln!("[Tauri] The app will start but backend features won't work.");
            }
        }
    }
    
    // En modo desarrollo, asumir backend externo
    #[cfg(debug_assertions)]
    {
        println!("[Tauri] Development mode - assuming backend running externally at http://localhost:8000");
    }
    
    tauri::Builder::default()
        .manage(BackendProcess(Mutex::new(backend_child)))
        .on_window_event(|event| {
            // Cleanup cuando se cierra la ventana
            if let tauri::WindowEvent::Destroyed = event.event() {
                if let Some(state) = event.window().try_state::<BackendProcess>() {
                    if let Ok(mut process) = state.0.lock() {
                        if let Some(mut child) = process.take() {
                            println!("[Tauri] Stopping backend process...");
                            let _ = child.kill();
                            let _ = child.wait();
                            println!("[Tauri] Backend stopped");
                        }
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
