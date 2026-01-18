import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: string | number;
  trend?: string;
  trendUp?: boolean;
  icon: ReactNode;
  className?: string;
  loading?: boolean;
}

export function StatCard({ title, value, trend, trendUp, icon, className, loading }: StatCardProps) {
  if (loading) {
    return (
      <div className="bg-card rounded-xl border border-border/50 p-6 h-[140px] animate-pulse">
        <div className="h-4 w-24 bg-muted rounded mb-4" />
        <div className="h-8 w-32 bg-muted rounded" />
      </div>
    );
  }

  return (
    <div
      className={cn(
        "relative overflow-hidden bg-card rounded-xl border border-border/50 p-6 shadow-lg transition-all hover:border-primary/20 hover:shadow-primary/5 group",
        className
      )}
    >
      <div className="flex justify-between items-start">
        <div>
          <p className="text-sm font-medium text-muted-foreground mb-1">{title}</p>
          <h3 className="text-3xl font-bold font-mono tracking-tight">{value}</h3>
        </div>
        <div className="p-3 bg-secondary/50 rounded-lg text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors duration-300">
          {icon}
        </div>
      </div>
      
      {trend && (
        <div className="mt-4 flex items-center text-xs font-medium">
          <span
            className={cn(
              "px-1.5 py-0.5 rounded mr-2",
              trendUp
                ? "bg-profit-soft text-profit"
                : "bg-loss-soft text-loss"
            )}
          >
            {trend}
          </span>
          <span className="text-muted-foreground">vs last session</span>
        </div>
      )}

      {/* Background decoration */}
      <div className="absolute -right-6 -bottom-6 w-24 h-24 bg-primary/5 rounded-full blur-2xl group-hover:bg-primary/10 transition-colors" />
    </div>
  );
}
