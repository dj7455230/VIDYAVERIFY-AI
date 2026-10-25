import { cn } from "@/lib/utils";

export function Card({
  children,
  className,
  hover = false,
}: {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
}) {
  return (
    <div
      className={cn(
        "rounded-xl border p-5 transition-all duration-200",
        hover && "hover:border-cyan-500/30 hover:shadow-lg hover:shadow-cyan-950/20",
        className
      )}
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
  trend,
  href,
}: {
  label: string;
  value: string | number;
  icon?: any;
  color?: string;
  trend?: string;
  href?: string;
}) {
  const content = (
    <div
      className={cn(
        "rounded-xl border p-4.5 flex items-start justify-between transition-all duration-200",
        href && "hover:border-cyan-500/40 hover:bg-slate-800/40 cursor-pointer shadow-sm"
      )}
      style={{
        background: "var(--surface)",
        borderColor: "var(--border)",
      }}
    >
      <div className="min-w-0 pr-2">
        <p
          className="text-xs font-medium uppercase tracking-wider mb-1 truncate"
          style={{ color: "var(--muted)" }}
        >
          {label}
        </p>
        <p className="text-2xl font-bold tracking-tight tabular-nums text-slate-100">{value}</p>
        {trend && (
          <p className="text-xs mt-1.5 font-medium flex items-center gap-1 text-emerald-400">
            <span>●</span> {trend}
          </p>
        )}
      </div>
      {Icon && (
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0 border"
          style={{
            background: `${color}15`,
            borderColor: `${color}30`,
          }}
        >
          <Icon size={20} style={{ color }} />
        </div>
      )}
    </div>
  );

  if (href) {
    return (
      <a href={href} className="block no-underline">
        {content}
      </a>
    );
  }

  return content;
}

export function StatusBadge({
  status,
  colorMap,
}: {
  status: string;
  colorMap?: Record<string, string>;
}) {
  const defaultColors: Record<string, string> = {
    open: "text-amber-400 bg-amber-500/10 border-amber-500/20",
    under_review: "text-blue-400 bg-blue-500/10 border-blue-500/20",
    resolved: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    accepted_justified: "text-indigo-400 bg-indigo-500/10 border-indigo-500/20",
    closed: "text-slate-400 bg-slate-500/10 border-slate-500/20",
    exceeds_intake: "text-rose-400 bg-rose-500/10 border-rose-500/20",
    within_intake: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    low: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    medium: "text-amber-400 bg-amber-500/10 border-amber-500/20",
    high: "text-orange-400 bg-orange-500/10 border-orange-500/20",
    critical: "text-rose-400 bg-rose-500/10 border-rose-500/20",
  };

  const styleClass = (colorMap && colorMap[status]) || defaultColors[status.toLowerCase()] || "text-slate-300 bg-slate-800 border-slate-700";

  return (
    <span className={`badge border ${styleClass}`} title={status}>
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-70" />
      {status.replace(/_/g, " ")}
    </span>
  );
}
