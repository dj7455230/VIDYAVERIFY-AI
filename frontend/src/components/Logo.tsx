import { cn } from "@/lib/utils";

export function Logo({ className }: { className?: string }) {
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <svg
        width="36"
        height="36"
        viewBox="0 0 36 36"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="shrink-0"
      >
        <rect width="36" height="36" rx="8" fill="#06b6d4" />
        <path
          d="M8 12L12 8L16 12L12 16Z"
          stroke="white"
          strokeWidth="1.5"
          fill="none"
        />
        <path
          d="M18 12L22 8L26 12L22 16Z"
          stroke="white"
          strokeWidth="1.5"
          fill="none"
        />
        <path
          d="M13 17L17 21L13 25L9 21Z"
          stroke="white"
          strokeWidth="1.5"
          fill="none"
        />
        <path
          d="M23 17L27 21L23 25L19 21Z"
          stroke="white"
          strokeWidth="1.5"
          fill="none"
        />
        <circle cx="18" cy="21" r="1.5" fill="white" />
      </svg>
      <div className="flex flex-col leading-none">
        <span className="text-sm font-bold tracking-wide">VIDYAVERIFY</span>
        <span className="text-xs font-medium" style={{ color: "#06b6d4" }}>
          AI
        </span>
      </div>
    </div>
  );
}
