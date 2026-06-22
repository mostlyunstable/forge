interface ErrorStateProps {
  message: string;
  code?: string;
  retry?: () => void;
}

export function ErrorState({ message, code, retry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-start gap-2 p-6">
      {code && (
        <div className="font-mono text-[14px] text-[var(--color-accent-red)]">
          {code}
        </div>
      )}
      <div className="text-[13px] text-[var(--color-text-secondary)]">
        {message}
      </div>
      {retry && (
        <button onClick={retry} className="btn mt-2">
          Try again
        </button>
      )}
    </div>
  );
}