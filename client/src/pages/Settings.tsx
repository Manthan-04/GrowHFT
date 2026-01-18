import { useState } from "react";
import { useUser } from "@/hooks/use-user";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Shield, Key, LogOut } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function Settings() {
  const { user, updateConfig, isUpdating } = useUser();
  const { logout } = useAuth();
  
  const [keys, setKeys] = useState({ 
    apiKey: user?.growwApiKey || "", 
    apiSecret: user?.growwApiSecret || "" 
  });

  const handleSave = () => {
    updateConfig({ 
      growwApiKey: keys.apiKey, 
      growwApiSecret: keys.apiSecret 
    });
  };

  return (
    <div className="max-w-4xl space-y-8 animate-in fade-in duration-500">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-white">Settings</h2>
        <p className="text-muted-foreground">Manage your account and API configurations</p>
      </div>

      <div className="grid gap-6">
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-primary" />
              Groww API Configuration
            </CardTitle>
            <CardDescription>
              Enter your Groww trading API credentials. These are stored securely.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>API Key</Label>
              <div className="relative">
                <Key className="absolute left-3 top-2.5 w-4 h-4 text-muted-foreground" />
                <Input 
                  value={keys.apiKey} 
                  onChange={(e) => setKeys({...keys, apiKey: e.target.value})}
                  className="pl-9 bg-background font-mono" 
                  placeholder="Your Groww API Key"
                  type="password"
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <Label>API Secret</Label>
              <div className="relative">
                <Key className="absolute left-3 top-2.5 w-4 h-4 text-muted-foreground" />
                <Input 
                  value={keys.apiSecret} 
                  onChange={(e) => setKeys({...keys, apiSecret: e.target.value})}
                  className="pl-9 bg-background font-mono" 
                  placeholder="Your Groww API Secret"
                  type="password"
                />
              </div>
            </div>

            <div className="pt-2">
              <Button onClick={handleSave} disabled={isUpdating}>
                {isUpdating ? "Saving..." : "Save Configuration"}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-destructive">Danger Zone</CardTitle>
            <CardDescription>Account actions</CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="destructive" onClick={() => logout()} className="gap-2">
              <LogOut className="w-4 h-4" /> Sign Out
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
