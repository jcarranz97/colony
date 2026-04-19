interface EmptyStateProps {
  message: string;
  icon?: React.ReactNode;
}

export function EmptyState({ message, icon }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-default-400 gap-3">
      {icon && <span className="text-4xl">{icon}</span>}
      <p className="text-sm">{message}</p>
    </div>
  );
}
