import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, buildUrl, type InsertStrategy } from "@shared/routes";
import { useToast } from "@/hooks/use-toast";

export function useStrategies() {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const strategiesQuery = useQuery({
    queryKey: [api.strategies.list.path],
    queryFn: async () => {
      const res = await fetch(api.strategies.list.path, { credentials: "include" });
      if (!res.ok) throw new Error("Failed to fetch strategies");
      return api.strategies.list.responses[200].parse(await res.json());
    },
  });

  const createStrategyMutation = useMutation({
    mutationFn: async (data: InsertStrategy) => {
      const res = await fetch(api.strategies.create.path, {
        method: api.strategies.create.method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to create strategy");
      return api.strategies.create.responses[201].parse(await res.json());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [api.strategies.list.path] });
      toast({ title: "Strategy Created", description: "New trading strategy added." });
    },
    onError: () => toast({ title: "Error", description: "Failed to create strategy", variant: "destructive" }),
  });

  const updateStrategyMutation = useMutation({
    mutationFn: async ({ id, ...updates }: { id: number } & Partial<InsertStrategy>) => {
      const url = buildUrl(api.strategies.update.path, { id });
      const res = await fetch(url, {
        method: api.strategies.update.method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updates),
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to update strategy");
      return api.strategies.update.responses[200].parse(await res.json());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [api.strategies.list.path] });
      toast({ title: "Strategy Updated", description: "Configuration saved." });
    },
  });

  const toggleStrategyMutation = useMutation({
    mutationFn: async ({ id, isActive }: { id: number; isActive: boolean }) => {
      const url = buildUrl(api.strategies.toggle.path, { id });
      const res = await fetch(url, {
        method: api.strategies.toggle.method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ isActive }),
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to toggle strategy");
      return api.strategies.toggle.responses[200].parse(await res.json());
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [api.strategies.list.path] });
      toast({ 
        title: data.isActive ? "Strategy Activated" : "Strategy Paused",
        description: `${data.name} is now ${data.isActive ? 'active' : 'inactive'}.`,
        variant: data.isActive ? "default" : "destructive",
      });
    },
  });

  return {
    strategies: strategiesQuery.data,
    isLoading: strategiesQuery.isLoading,
    createStrategy: createStrategyMutation.mutate,
    updateStrategy: updateStrategyMutation.mutate,
    toggleStrategy: toggleStrategyMutation.mutate,
  };
}
