import { cn } from "@/lib/utils";
export function Badge({ children, tone = "neutral", className }: { children: React.ReactNode; tone?: "neutral" | "positive" | "warning" | "risk"; className?: string }) {
  const tones = { neutral: "border-ink/25 text-ink/70", positive: "border-accent/40 bg-accent/10 text-accent", warning: "border-[#90752b]/40 bg-[#90752b]/10 text-[#65521d]", risk: "border-risk/40 bg-risk/10 text-risk" };
  return <span className={cn("inline-flex rounded-[2px] border px-2 py-1 font-mono text-[10px] font-semibold uppercase tracking-[.08em]", tones[tone], className)}>{children}</span>;
}
