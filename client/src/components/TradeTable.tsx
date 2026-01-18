import { ArrowDown, ArrowUp } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Trade } from "@shared/schema";

interface TradeTableProps {
  trades: Trade[];
  loading?: boolean;
  compact?: boolean;
}

export function TradeTable({ trades, loading, compact }: TradeTableProps) {
  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-12 bg-muted/20 rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  if (trades.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        No trades recorded yet.
      </div>
    );
  }

  return (
    <div className="w-full overflow-hidden rounded-xl border border-border/50 bg-card/30">
      <table className="w-full text-sm text-left">
        <thead className="bg-muted/30 text-xs uppercase font-medium text-muted-foreground">
          <tr>
            <th className="px-6 py-4">Symbol</th>
            <th className="px-6 py-4">Type</th>
            <th className="px-6 py-4 text-right">Qty</th>
            <th className="px-6 py-4 text-right">Price</th>
            <th className="px-6 py-4 text-right">PnL</th>
            {!compact && <th className="px-6 py-4 text-right">Time</th>}
            <th className="px-6 py-4 text-center">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border/30">
          {trades.map((trade) => {
            const isBuy = trade.side === "BUY";
            const isProfit = trade.pnl ? Number(trade.pnl) >= 0 : false;
            
            return (
              <tr key={trade.id} className="hover:bg-white/5 transition-colors font-mono">
                <td className="px-6 py-4 font-bold text-foreground">{trade.symbol}</td>
                <td className="px-6 py-4">
                  <span
                    className={cn(
                      "inline-flex items-center px-2 py-1 rounded text-xs font-bold",
                      isBuy ? "text-blue-400 bg-blue-400/10" : "text-orange-400 bg-orange-400/10"
                    )}
                  >
                    {trade.side}
                  </span>
                </td>
                <td className="px-6 py-4 text-right text-muted-foreground">{trade.quantity}</td>
                <td className="px-6 py-4 text-right">₹{Number(trade.price).toFixed(2)}</td>
                <td className="px-6 py-4 text-right">
                  {trade.pnl ? (
                    <span className={cn("flex items-center justify-end gap-1", isProfit ? "text-profit" : "text-loss")}>
                      {isProfit ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />}
                      ₹{Math.abs(Number(trade.pnl)).toFixed(2)}
                    </span>
                  ) : (
                    <span className="text-muted-foreground">-</span>
                  )}
                </td>
                {!compact && (
                  <td className="px-6 py-4 text-right text-muted-foreground text-xs">
                    {new Date(trade.timestamp!).toLocaleTimeString()}
                  </td>
                )}
                <td className="px-6 py-4 text-center">
                  <div className="flex justify-center">
                    <span
                      className={cn(
                        "w-2 h-2 rounded-full",
                        trade.status === "EXECUTED" && "bg-profit shadow-[0_0_8px_hsl(var(--profit))]",
                        trade.status === "PENDING" && "bg-warning",
                        trade.status === "FAILED" && "bg-loss"
                      )}
                    />
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
