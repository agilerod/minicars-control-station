#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

mod backend;

use backend::BackendManager;
use std::sync::Mutex;
use tauri::{Manager, State};

struct AppState {
    backend: Mutex<Option<BackendManager>>,
}

#[tauri::command]
fn backend_status() -> Result<String, String> {
    Ok("Backend managed by Tauri".to_string())
}

fn main() {
    let mut backend_manager = BackendManager::new(8000);
    
    // En modo producción, buscar carpeta backend/ y lanzar con Python
    #[cfg(not(debug_assertions))]
    {
        if let Some(backend_dir) = find_backend_dir() {
            println!("[Tauri] Found backend directory at: {:?}", backend_dir);
            
            match backend_manager.start(&backend_dir.to_string_lossy()) {
                Ok(_) => println!("[Tauri] Backend started successfully"),
                Err(e) => {
                    eprintln!("[Tauri] Failed to start backend: {}", e);
                    eprintln!("[Tauri] Make sure Python 3.10+ is installed and in PATH");
                    // Mostrar error al usuario (opcional)
                }
            }
        } else {
            eprintln!("[Tauri] backend/ directory not found in bundle!");
        }
    }
    
    // En modo desarrollo, asumir que backend corre externamente
    #[cfg(debug_assertions)]
    {
        println!("[Tauri] Development mode - assuming backend running externally");
        println!("[Tauri] Expected backend at: http://localhost:8000");
    }
    
    tauri::Builder::default()
        .manage(AppState {
            backend: Mutex::new(Some(backend_manager)),
        })
        .invoke_handler(tauri::generate_handler![backend_status])
        .on_window_event(|event| {
            // Cleanup cuando se cierra la ventana
            if let tauri::WindowEvent::Destroyed = event.event() {
                println!("[Tauri] Window closing, cleaning up...");
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

/// Busca el directorio backend/ en el bundle de Tauri (modo producción)
#[cfg(not(debug_assertions))]
fn find_backend_dir() -> Option<std::path::PathBuf> {
    use std::path::PathBuf;
    
    // Obtener el directorio del ejecutable
    let exe_dir = std::env::current_exe()
        .ok()?
        .parent()?
        .to_path_buf();
    
    // Buscar backend/ en recursos o directorios relativos
    let candidates = vec![
        exe_dir.join("backend"),
        exe_dir.join("resources").join("backend"),
        exe_dir.join("..").join("backend"),
        exe_dir.join("..").join("..").join("backend"),  // Para instaladores
    ];
    
    for candidate in candidates {
        if candidate.join("minicars_backend").exists() {
            return Some(candidate);
        }
    }
    
    None
}

#[cfg(debug_assertions)]
fn find_backend_dir() -> Option<std::path::PathBuf> {
    None  // No buscar en desarrollo
}
