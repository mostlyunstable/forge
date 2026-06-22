interface SkeletonRowProps {
  lines?: number;
}

export function SkeletonRow({ lines = 1 }: SkeletonRowProps) {
  return (
    <div className="space-y-[4px]">
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="h-[32px] rounded-[4px] bg-[var(--color-bg-elevated)]"
          style={{
            opacity: 1 - i * 0.15,
          }}
        />
      ))}
    </div>
  );
}