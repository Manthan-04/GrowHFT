import { useState } from "react";
import { useStrategies } from "@/hooks/use-strategies";
import { Plus, Play, Pause, Edit2, Check, X } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

export default function Strategies() {
  const { strategies, isLoading, createStrategy, updateStrategy, toggleStrategy } = useStrategies();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  // Form states
  const [formData, setFormData] = useState({ name: "", description: "", parameters: "{}" });

  const handleCreate = () => {
    try {
      const params = JSON.parse(formData.parameters);
      createStrategy({
        name: formData.name,
        description: formData.description,
        parameters: params,
        isActive: false
      }, {
        onSuccess: () => {
          setIsCreateOpen(false);
          setFormData({ name: "", description: "", parameters: "{}" });
        }
      });
    } catch (e) {
      alert("Invalid JSON parameters");
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Strategies</h2>
          <p className="text-muted-foreground">Manage your algorithmic trading bots</p>
        </div>
        
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90">
              <Plus className="w-4 h-4" /> New Strategy
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-card border-border">
            <DialogHeader>
              <DialogTitle>Create New Strategy</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 pt-4">
              <div className="space-y-2">
                <Label>Name</Label>
                <Input 
                  value={formData.name} 
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  placeholder="e.g. Nifty Scalper v1"
                  className="bg-background"
                />
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <Textarea 
                  value={formData.description} 
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  placeholder="Strategy logic description..."
                  className="bg-background"
                />
              </div>
              <div className="space-y-2">
                <Label>Parameters (JSON)</Label>
                <Textarea 
                  value={formData.parameters} 
                  onChange={(e) => setFormData({...formData, parameters: e.target.value})}
                  className="font-mono text-xs bg-background min-h-[100px]"
                />
              </div>
              <Button onClick={handleCreate} className="w-full">Create Strategy</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {isLoading && [1, 2, 3].map(i => (
          <div key={i} className="h-48 bg-card border border-border/50 rounded-xl animate-pulse" />
        ))}
        
        {strategies?.map((strategy) => (
          <div 
            key={strategy.id} 
            className={cn(
              "group relative overflow-hidden rounded-xl border p-6 transition-all hover:shadow-lg",
              strategy.isActive 
                ? "bg-card border-primary/30 shadow-primary/5" 
                : "bg-card/50 border-border/50 opacity-80 hover:opacity-100"
            )}
          >
            <div className="flex justify-between items-start mb-4">
              <div className="flex-1 mr-4">
                <h3 className="font-bold text-lg">{strategy.name}</h3>
                <div className={cn(
                  "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase mt-2",
                  strategy.isActive ? "bg-profit-soft text-profit" : "bg-muted text-muted-foreground"
                )}>
                  <span className={cn("w-1.5 h-1.5 rounded-full", strategy.isActive ? "bg-profit animate-pulse" : "bg-muted-foreground")} />
                  {strategy.isActive ? "Running" : "Stopped"}
                </div>
              </div>
              <Button
                size="icon"
                variant="outline"
                className={cn(
                  "rounded-full transition-all duration-300", 
                  strategy.isActive 
                    ? "bg-destructive/10 text-destructive border-destructive/20 hover:bg-destructive hover:text-white" 
                    : "bg-profit/10 text-profit border-profit/20 hover:bg-profit hover:text-white"
                )}
                onClick={() => toggleStrategy({ id: strategy.id, isActive: !strategy.isActive })}
              >
                {strategy.isActive ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 pl-0.5" />}
              </Button>
            </div>

            <p className="text-sm text-muted-foreground mb-6 line-clamp-2 h-10">
              {strategy.description || "No description provided."}
            </p>

            <div className="space-y-3">
              <div className="bg-background/50 rounded p-3 font-mono text-xs border border-border/50">
                <p className="text-muted-foreground mb-1 text-[10px] uppercase">Parameters:</p>
                <pre className="overflow-x-auto">
                  {JSON.stringify(strategy.parameters, null, 2)}
                </pre>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-border/30 flex justify-end">
              <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-primary">
                <Edit2 className="w-3 h-3 mr-2" /> Configure
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
