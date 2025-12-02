type ActionName =
  | "start_stream"
  | "stop_stream"
  | "start_car_control"
  | "stop_car_control";

type ActionButtonsProps = {
  onAction: (actionName: ActionName) => void;
  loadingAction: ActionName | null;
};

const ACTIONS: { label: string; action: ActionName; variant: "primary" | "danger" }[] =
  [
    { label: "Start Stream", action: "start_stream", variant: "primary" },
    { label: "Stop Stream", action: "stop_stream", variant: "danger" },
    { label: "Start Car Control", action: "start_car_control", variant: "primary" },
    { label: "Stop Car Control", action: "stop_car_control", variant: "danger" },
  ];

export function ActionButtons({ onAction, loadingAction }: ActionButtonsProps) {
  return (
    <section className="card">
      <h2>Acciones</h2>
      <div className="button-grid">
        {ACTIONS.map(({ label, action, variant }) => {
          const isLoading = loadingAction === action;
          return (
            <button
              key={action}
              className={`action-button ${variant}`}
              onClick={() => onAction(action)}
              disabled={isLoading}
            >
              {isLoading ? "Procesando..." : label}
            </button>
          );
        })}
      </div>
    </section>
  );
}


