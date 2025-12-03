use std::process::{Child, Command};
use std::thread;
use std::time::Duration;

pub struct BackendManager {
    process: Option<Child>,
    port: u16,
}

impl BackendManager {
    pub fn new(port: u16) -> Self {
        BackendManager {
            process: None,
            port,
        }
    }
    
    /// Inicia el backend usando Python + uvicorn directamente
    pub fn start(&mut self, backend_path: &str) -> Result<(), String> {
        println!("[Backend] Starting Python backend from: {}", backend_path);
        
        // Lanzar: python -m uvicorn minicars_backend.api:app --host 127.0.0.1 --port 8000
        let child = Command::new("python")
            .args(&[
                "-m",
                "uvicorn",
                "minicars_backend.api:app",
                "--host",
                "127.0.0.1",
                "--port",
                &self.port.to_string(),
            ])
            .current_dir(backend_path)  // Working dir = backend/
            .env("MINICARS_ENV", "production")
            .spawn()
            .map_err(|e| format!("Failed to spawn backend: {}. Ensure Python is installed.", e))?;
        
        self.process = Some(child);
        
        // Esperar a que el backend esté listo (health check)
        println!("[Backend] Waiting for backend to be ready...");
        for attempt in 1..=15 {
            thread::sleep(Duration::from_millis(500));
            
            if self.health_check() {
                println!("[Backend] Ready after {}ms", attempt * 500);
                return Ok(());
            }
        }
        
        // Si llegamos aquí, el backend no respondió
        self.stop();
        Err("Backend failed to start (health check timeout after 7.5s)".to_string())
    }
    
    /// Health check HTTP al backend
    fn health_check(&self) -> bool {
        let url = format!("http://localhost:{}/health", self.port);
        
        match reqwest::blocking::Client::builder()
            .timeout(Duration::from_millis(500))
            .build()
        {
            Ok(client) => {
                match client.get(&url).send() {
                    Ok(response) => {
                        let success = response.status().is_success();
                        if success {
                            println!("[Backend] Health check OK");
                        }
                        success
                    },
                    Err(_) => false,
                }
            },
            Err(_) => false,
        }
    }
    
    /// Detiene el backend de forma limpia
    pub fn stop(&mut self) {
        if let Some(mut child) = self.process.take() {
            println!("[Backend] Stopping...");
            
            // Intentar shutdown graceful
            let shutdown_url = format!("http://localhost:{}/shutdown", self.port);
            let _ = reqwest::blocking::Client::builder()
                .timeout(Duration::from_secs(2))
                .build()
                .and_then(|client| client.post(&shutdown_url).send());
            
            // Esperar a que termine
            thread::sleep(Duration::from_secs(2));
            
            // Si no terminó, forzar
            let _ = child.kill();
            let _ = child.wait();
            
            println!("[Backend] Stopped");
        }
    }
}

impl Drop for BackendManager {
    fn drop(&mut self) {
        self.stop();
    }
}

