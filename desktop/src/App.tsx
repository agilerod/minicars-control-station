import { useEffect, useState } from "react";
import {
  getStatus,
  startReceiver,
  stopReceiver,
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
    refreshStatus();
  }, []);

  const handleAction = async (action: ActionName) => {
    const actionMap: Record<ActionName, () => Promise<unknown>> = {
      start_stream: startReceiver,
      stop_stream: stopReceiver,
      start_car_control: startCarControl,
      stop_car_control: stopCarControl,
    };

    setLoadingAction(action);
    setMessage(null);

    try {
      await actionMap[action]();
      setMessage("Éxito: acción ejecutada correctamente.");
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


