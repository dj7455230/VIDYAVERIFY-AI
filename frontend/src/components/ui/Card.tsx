import { cn } from "@/lib/utils";

export function Card({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn("rounded-lg border p-5", className)}
      style={{
        background: "var(--surface)",
        borderColor: "var(--border)",
      }}
    >
      {children}
    </div>
  );
}

export function MetricCard({
  label,
  value,
  icon: Icon,
  color = "#06b6d4",
}: {
  label: string;
  value: string | number;
  icon?: any;
  color?: string;
}) {
  return (
    <div
      className="rounded-lg border p-4 flex items-center gap-4"
      style={{
        background: "var(--surface)",
        borderColor: "var(--border)",
      }}
    >
      {Icon && (
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
          style={{ background: `${color}15` }}
        >
          <Icon size={20} style={{ color }} />
        </div>
      )}
      <div className="min-w-0">
        <p
          className="text-xs font-medium truncate"
          style={{ color: "var(--muted)" }}
        >
          {label}
        </p>
        <p className="text-2xl font-bold tabular-nums">{value}</p>
      </div>
    </div>
  );
}

export function StatusBadge({
  status,
  colorMap,
}: {
  status: string;
  colorMap: Record<string, string>;
}) {
  const colors =
    colorMap[status] || "text-gray-600 bg-gray-50 border-gray-200";
  return (
    <span className={`badge border ${colors}`} title={status}>
      {status.replace(/_/g, " ")}
    </span>
  );
}
