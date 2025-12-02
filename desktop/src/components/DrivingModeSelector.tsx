import React, { useEffect, useState } from "react";
import {
  DrivingModeId,
  ControlProfile,
  fetchControlProfile,
  updateControlProfile,
} from "../api/controlProfile";
import "./DrivingModeSelector.css";

type ModeConfig = {
  id: DrivingModeId;
  label: string;
  subtitle: string;
  description: string;
  color: string;
};

const MODES: ModeConfig[] = [
  {
    id: "kid",
    label: "Kid",
    subtitle: "Seguro",
    description: "Aceleración limitada y respuesta muy suave.",
    color: "#10b981", // green
  },
  {
    id: "normal",
    label: "Normal",
    subtitle: "Equilibrado",
    description: "Buen balance entre control y respuesta.",
    color: "#3b82f6", // blue
  },
  {
    id: "sport",
    label: "Sport",
    subtitle: "Rápido",
    description: "Respuesta más agresiva y máxima aceleración.",
    color: "#f59e0b", // amber
  },
];

interface DrivingModeSelectorProps {
  className?: string;
  onModeChange?: (mode: DrivingModeId) => void;
}

export const DrivingModeSelector: React.FC<DrivingModeSelectorProps> = ({
  className = "",
  onModeChange,
}) => {
  const [profile, setProfile] = useState<ControlProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setLoading(true);
        setError(null);
        const data = await fetchControlProfile();
        if (!cancelled) {
          setProfile(data);
          if (onModeChange) onModeChange(data.active_mode);
        }
      } catch (err) {
        if (!cancelled) {
          console.error(err);
          setError("No se pudo cargar el modo de conducción.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [onModeChange]);

  async function handleSelect(mode: DrivingModeId) {
    if (!profile || profile.active_mode === mode || updating) return;
    try {
      setUpdating(true);
      setError(null);
      const updated = await updateControlProfile(mode);
      setProfile(updated);
      if (onModeChange) onModeChange(updated.active_mode);
    } catch (err) {
      console.error(err);
      setError("No se pudo actualizar el modo. Revisa el backend.");
    } finally {
      setUpdating(false);
    }
  }

  const activeMode = profile?.active_mode;

  return (
    <section className={`card driving-mode-selector ${className}`}>
      <div className="driving-mode-header">
        <div>
          <h2>Modo de conducción</h2>
          <p className="driving-mode-subtitle">
            Elige cómo responde el acelerador del MiniCar.
          </p>
        </div>
        {loading ? (
          <span className="driving-mode-badge loading">Cargando…</span>
        ) : activeMode ? (
          <span
            className="driving-mode-badge active"
            style={{
              backgroundColor: MODES.find((m) => m.id === activeMode)?.color + "20",
              color: MODES.find((m) => m.id === activeMode)?.color,
              borderColor: MODES.find((m) => m.id === activeMode)?.color + "40",
            }}
          >
            {activeMode.toUpperCase()}
          </span>
        ) : null}
      </div>

      <div className="driving-mode-grid">
        {MODES.map((mode) => {
          const isActive = activeMode === mode.id;
          return (
            <button
              key={mode.id}
              type="button"
              onClick={() => handleSelect(mode.id)}
              disabled={loading || updating}
              className={`driving-mode-button ${isActive ? "active" : ""} ${
                updating ? "updating" : ""
              }`}
              style={
                isActive
                  ? {
                      borderColor: mode.color,
                      backgroundColor: mode.color + "15",
                    }
                  : undefined
              }
            >
              <div className="driving-mode-button-header">
                <div>
                  <span className="driving-mode-label">{mode.label}</span>
                  <span className="driving-mode-subtitle-small">{mode.subtitle}</span>
                </div>
                <div
                  className={`driving-mode-indicator ${isActive ? "active" : ""}`}
                  style={
                    isActive
                      ? {
                          borderColor: mode.color,
                          backgroundColor: mode.color + "30",
                          color: mode.color,
                        }
                      : undefined
                  }
                >
                  {isActive ? "ON" : "OFF"}
                </div>
              </div>
              <p className="driving-mode-description">{mode.description}</p>
            </button>
          );
        })}
      </div>

      {error && (
        <p className="driving-mode-error">
          ⚠ {error}
        </p>
      )}
    </section>
  );
};

