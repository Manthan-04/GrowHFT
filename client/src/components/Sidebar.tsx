import { Link, useLocation } from "wouter";
import { LayoutDashboard, LineChart, List, Settings, Activity, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

const items = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Strategies", href: "/strategies", icon: Zap },
  { name: "Live Trades", href: "/trades", icon: List },
  { name: "Analysis", href: "/analysis", icon: LineChart },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const [location] = useLocation();

  return (
    <div className="hidden md:flex flex-col w-64 border-r border-border bg-card/50 backdrop-blur-xl h-screen sticky top-0">
      <div className="p-6 border-b border-border/50 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
          <Activity className="w-5 h-5 text-primary-foreground" />
        </div>
        <h1 className="text-xl font-bold tracking-tight font-display">
          HFT<span className="text-primary">Dash</span>
        </h1>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {items.map((item) => {
          const isActive = location === item.href;
          return (
            <Link key={item.name} href={item.href}>
              <div
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer group",
                  isActive
                    ? "bg-primary/10 text-primary shadow-sm ring-1 ring-primary/20"
                    : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
                )}
              >
                <item.icon
                  className={cn(
                    "w-5 h-5 transition-colors",
                    isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground"
                  )}
                />
                {item.name}
              </div>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-border/50">
        <div className="bg-gradient-to-br from-indigo-500/10 to-purple-500/10 rounded-lg p-4 border border-indigo-500/10">
          <div className="flex items-center gap-2 text-xs font-semibold text-indigo-400 mb-1">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            ENGINE ONLINE
          </div>
          <p className="text-[10px] text-muted-foreground">Connected to NSE Feed</p>
        </div>
      </div>
    </div>
  );
}
