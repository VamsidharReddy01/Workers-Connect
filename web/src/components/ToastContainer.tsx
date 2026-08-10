export type ToastNotice = {
  id: number;
  text: string;
  type: 'info' | 'error';
};

interface ToastContainerProps {
  notifications: ToastNotice[];
}

export function ToastContainer({ notifications }: ToastContainerProps) {
  if (!notifications.length) return null;

  return (
    <div className="toast-stack">
      {notifications.map((n) => (
        <div key={n.id} className={`toast toast-${n.type}`}>
          {n.text}
        </div>
      ))}
    </div>
  );
}
