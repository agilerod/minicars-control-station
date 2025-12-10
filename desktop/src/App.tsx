import { useEffect, useState } from "react";
import { invoke } from "@tauri-apps/api/tauri";
import {
  getStatus,
  startStream,
  stopStream,
  startCarControl,
  stopCarControl,
} from "./api/client";
import { StatusCard } from "./components/StatusCard";
import { ActionButtons } from "./components/ActionButtons";
import { DrivingModeSelector } from "./components/DrivingModeSelector";
import type { DrivingModeId } from "./api/controlProfile";

type StatusState = {
  stream: string;
  car_control: string;
};

const INITIAL_STATUS: StatusState = {
  stream: "unknown",
  car_control: "unknown",
};

type ActionName =
  | "start_stream"
  | "stop_stream"
  | "start_car_control"
  | "stop_car_control";

function App() {
  const [status, setStatus] = useState<StatusState>(INITIAL_STATUS);
  const [loadingAction, setLoadingAction] = useState<ActionName | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [activeMode, setActiveMode] = useState<DrivingModeId | null>(null);

  const refreshStatus = async () => {
    try {
      const data = await getStatus();
      setStatus({
        stream: data?.stream ?? "unknown",
        car_control: data?.car_control ?? "unknown",
      });
    } catch (error) {
      setMessage(
        `Error: ${
          error instanceof Error ? error.message : "No se pudo obtener el estado."
        }`
      );
    }
  };

  useEffect(() => {
    // Asegurar que el backend esté corriendo antes de hacer peticiones
    const initializeBackend = async () => {
      try {
        await invoke("ensure_backend_running");
        // Esperar un momento para que el backend esté listo
        await new Promise((resolve) => setTimeout(resolve, 1000));
        // Ahora sí, refrescar el estado
        await refreshStatus();
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        
        // Log detallado en consola para debugging (desarrollo)
        console.error("[App] Failed to start backend:", error);
        console.error("[App] Error details:", errorMessage);
        
        // Diferenciar tipos de error basándose en el prefijo del mensaje
        let userMessage: string;
        
        if (errorMessage.includes("PYTHON_NOT_FOUND") || errorMessage.includes("Python interpreter not found")) {
          userMessage = "Error: Python no está instalado o no está en PATH. Por favor instala Python 3.10+ y asegúrate de que esté disponible en la línea de comandos.";
        } else if (errorMessage.includes("BACKEND_DIR_NOT_FOUND") || errorMessage.includes("Backend folder not found")) {
          userMessage = "Error: No se encontró el directorio del backend. Revisa los logs de la consola para ver las rutas probadas.";
        } else if (errorMessage.includes("SPAWN_FAILED") || errorMessage.includes("Failed to start backend")) {
          userMessage = "Error: No se pudo iniciar el backend. Revisa los logs de la consola para más detalles.";
        } else {
          // Mostrar el mensaje de error tal cual si contiene información útil
          userMessage = `Error: No se pudo iniciar el backend. ${errorMessage}`;
        }
        
        setMessage(userMessage);
      }
    };

    initializeBackend();
  }, []);

  const handleAction = async (action: ActionName) => {
    const actionMap: Record<ActionName, () => Promise<unknown>> = {
      start_stream: startStream,    // Calls /actions/start_stream endpoint
      stop_stream: stopStream,      // Calls /actions/stop_stream endpoint
      start_car_control: startCarControl,
      stop_car_control: stopCarControl,
    };

    setLoadingAction(action);
    setMessage(null);

    try {
      const result = await actionMap[action]() as { status?: string; message?: string; details?: string };
      
      // Handle different status responses from backend
      if (result?.status === "already_running") {
        setMessage(`Info: ${result.message || "Ya estaba iniciado."}`);
      } else if (result?.status === "ok") {
        setMessage(`Éxito: ${result.message || "Acción ejecutada correctamente."}`);
      } else if (result?.status === "error") {
        setMessage(`Error: ${result.message || "No se pudo completar la acción."}`);
      } else {
        // Fallback for old format
        setMessage("Éxito: acción ejecutada correctamente.");
      }
      
      await refreshStatus();
    } catch (error) {
      setMessage(
        `Error: ${
          error instanceof Error ? error.message : "No se pudo completar la acción."
        }`
      );
    } finally {
      setLoadingAction(null);
    }
  };

  const isError = message?.startsWith("Error");

  return (
    <div className="app-container">
      <header className="header">
        <div>
          <p className="eyebrow">MiniCars Control Station</p>
          <h1>Dashboard local</h1>
          <p className="subtitle">
            Controla el stream de la Jetson y el auto RC desde una sola vista.
          </p>
        </div>
      </header>

      {message && (
        <div className={`message ${isError ? "error" : "success"}`}>{message}</div>
      )}

      <StatusCard status={status} activeMode={activeMode} />
      <DrivingModeSelector onModeChange={setActiveMode} />
      <ActionButtons onAction={handleAction} loadingAction={loadingAction} />
    </div>
  );
}

export default App;


