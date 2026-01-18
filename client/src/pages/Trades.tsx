import { useTrades } from "@/hooks/use-trades";
import { TradeTable } from "@/components/TradeTable";

export default function Trades() {
  const { data: trades, isLoading } = useTrades(50);

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Live Trades</h2>
          <p className="text-muted-foreground">Real-time execution feed</p>
        </div>
        
        <div className="flex gap-2">
          {/* Filters could go here */}
        </div>
      </div>

      <div className="bg-card border border-border/50 rounded-xl shadow-sm overflow-hidden">
        <TradeTable trades={trades ?? []} loading={isLoading} />
      </div>
    </div>
  );
}
