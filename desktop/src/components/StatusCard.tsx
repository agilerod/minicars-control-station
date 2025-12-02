type StatusState = {
  stream: string;
  car_control: string;
};

type StatusCardProps = {
  status: StatusState;
  activeMode?: string | null;
};

const STATUS_COLOR: Record<string, string> = {
  running: "#4CAF50",
  stopped: "#E53935",
  unknown: "#9E9E9E",
};

const MODE_COLOR: Record<string, string> = {
  kid: "#10b981",
  normal: "#3b82f6",
  sport: "#f59e0b",
  unknown: "#9E9E9E",
};

function StatusItem({
  label,
  state,
}: {
  label: string;
  state: keyof typeof STATUS_COLOR | string;
}) {
  const normalizedState =
    state === "running" || state === "stopped" ? state : "unknown";

  return (
    <div className="status-card">
      <p className="status-label">{label}</p>
      <span
        className="status-pill"
        style={{ backgroundColor: STATUS_COLOR[normalizedState] }}
      >
        {normalizedState}
      </span>
    </div>
  );
}

function ModeItem({ label, mode }: { label: string; mode: string | null }) {
  const normalizedMode = mode && ["kid", "normal", "sport"].includes(mode) ? mode : "unknown";
  const color = MODE_COLOR[normalizedMode] || MODE_COLOR.unknown;

  return (
    <div className="status-card">
      <p className="status-label">{label}</p>
      <span
        className="status-pill"
        style={{ backgroundColor: color }}
      >
        {normalizedMode.toUpperCase()}
      </span>
    </div>
  );
}

export function StatusCard({ status, activeMode }: StatusCardProps) {
  return (
    <section className="card status-wrapper">
      <h2>Estado actual</h2>
      <div className="status-grid">
        <StatusItem label="Stream" state={status.stream} />
        <StatusItem label="Car Control" state={status.car_control} />
        <ModeItem label="Modo de conducción" mode={activeMode} />
      </div>
    </section>
  );
}


