import { useTradeStats, useTrades } from "@/hooks/use-trades";
import { useStrategies } from "@/hooks/use-strategies";
import { StatCard } from "@/components/StatCard";
import { TradeTable } from "@/components/TradeTable";
import { DollarSign, Activity, Zap, BarChart3, TrendingUp } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

// Mock data for the chart since we don't have historical PnL endpoint yet
const chartData = [
  { time: '09:30', pnl: 1200 },
  { time: '10:00', pnl: 2100 },
  { time: '10:30', pnl: 1800 },
  { time: '11:00', pnl: 2400 },
  { time: '11:30', pnl: 3200 },
  { time: '12:00', pnl: 3100 },
  { time: '12:30', pnl: 4500 },
];

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useTradeStats();
  const { data: recentTrades, isLoading: tradesLoading } = useTrades(5);
  const { strategies } = useStrategies();

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Market Overview</h2>
          <p className="text-muted-foreground">Real-time performance metrics</p>
        </div>
        <div className="flex items-center gap-2 bg-card border border-border rounded-lg p-1.5">
          <span className="px-3 py-1 rounded-md bg-primary/10 text-primary text-xs font-bold uppercase">Live Market</span>
          <span className="text-xs text-muted-foreground px-2 font-mono">NSE: OPEN</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total PnL"
          value={`₹${stats?.totalPnl?.toLocaleString() ?? '0'}`}
          icon={<DollarSign className="w-5 h-5" />}
          trend="+12.5%"
          trendUp={true}
          loading={statsLoading}
        />
        <StatCard
          title="Total Volume"
          value={`₹${(stats?.totalVolume ?? 0).toLocaleString()}`}
          icon={<BarChart3 className="w-5 h-5" />}
          loading={statsLoading}
        />
        <StatCard
          title="Active Strategies"
          value={stats?.activeStrategies ?? 0}
          icon={<Zap className="w-5 h-5" />}
          loading={statsLoading}
        />
        <StatCard
          title="Total Trades"
          value={stats?.totalTrades ?? 0}
          icon={<Activity className="w-5 h-5" />}
          loading={statsLoading}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-card border border-border/50 rounded-xl p-6 shadow-sm">
            <h3 className="text-lg font-bold mb-6 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-primary" />
              Intraday Performance
            </h3>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorPnl" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis 
                    dataKey="time" 
                    stroke="#525252" 
                    fontSize={12} 
                    tickLine={false} 
                    axisLine={false} 
                  />
                  <YAxis 
                    stroke="#525252" 
                    fontSize={12} 
                    tickLine={false} 
                    axisLine={false} 
                    tickFormatter={(value) => `₹${value}`} 
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'hsl(var(--card))', 
                      borderColor: 'hsl(var(--border))',
                      borderRadius: '8px' 
                    }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="pnl" 
                    stroke="hsl(var(--primary))" 
                    strokeWidth={2}
                    fillOpacity={1} 
                    fill="url(#colorPnl)" 
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold">Recent Trades</h3>
            </div>
            <TradeTable trades={recentTrades ?? []} loading={tradesLoading} compact />
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-card border border-border/50 rounded-xl p-6">
            <h3 className="text-lg font-bold mb-4">Active Strategies</h3>
            <div className="space-y-4">
              {strategies?.filter(s => s.isActive).length === 0 && (
                <p className="text-sm text-muted-foreground">No active strategies running.</p>
              )}
              {strategies?.filter(s => s.isActive).map(strategy => (
                <div key={strategy.id} className="p-4 rounded-lg bg-background border border-border hover:border-primary/30 transition-colors">
                  <div className="flex justify-between items-start mb-2">
                    <span className="font-bold text-sm">{strategy.name}</span>
                    <span className="w-2 h-2 rounded-full bg-profit animate-pulse" />
                  </div>
                  <p className="text-xs text-muted-foreground line-clamp-2 mb-3">
                    {strategy.description || "No description provided"}
                  </p>
                  <div className="flex gap-2">
                    <span className="px-2 py-1 bg-secondary rounded text-[10px] font-mono text-secondary-foreground">RSI</span>
                    <span className="px-2 py-1 bg-secondary rounded text-[10px] font-mono text-secondary-foreground">MACD</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/20 rounded-xl p-6">
            <h3 className="font-bold text-primary mb-2">Groww API Status</h3>
            <p className="text-sm text-muted-foreground mb-4">Connection to trading gateway is stable. Latency: 45ms</p>
            <div className="h-1.5 w-full bg-primary/20 rounded-full overflow-hidden">
              <div className="h-full bg-primary w-full animate-pulse" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
