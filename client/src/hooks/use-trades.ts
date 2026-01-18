import { useQuery } from "@tanstack/react-query";
import { api } from "@shared/routes";

export function useTrades(limit?: number, symbol?: string) {
  return useQuery({
    queryKey: [api.trades.list.path, limit, symbol],
    queryFn: async () => {
      // Build query params
      const params = new URLSearchParams();
      if (limit) params.append("limit", limit.toString());
      if (symbol) params.append("symbol", symbol);
      
      const url = `${api.trades.list.path}?${params.toString()}`;
      
      const res = await fetch(url, { credentials: "include" });
      if (!res.ok) throw new Error("Failed to fetch trades");
      return api.trades.list.responses[200].parse(await res.json());
    },
    refetchInterval: 5000, // Poll every 5s for live trades
  });
}

export function useTradeStats() {
  return useQuery({
    queryKey: [api.trades.stats.path],
    queryFn: async () => {
      const res = await fetch(api.trades.stats.path, { credentials: "include" });
      if (!res.ok) throw new Error("Failed to fetch stats");
      return api.trades.stats.responses[200].parse(await res.json());
    },
    refetchInterval: 10000, // Poll every 10s for dashboard stats
  });
}
