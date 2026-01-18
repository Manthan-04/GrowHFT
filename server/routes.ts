import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { api } from "@shared/routes";
import { z } from "zod";
import { setupAuth, registerAuthRoutes } from "./replit_integrations/auth";
import { spawn } from "child_process";
import path from "path";

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  
  // Auth Setup
  await setupAuth(app);
  registerAuthRoutes(app);

  // === USERS ===
  app.get(api.users.me.path, async (req, res) => {
    // Auth middleware usually handles this, but for explicit route
    if (!req.isAuthenticated()) return res.sendStatus(401);
    // In Replit Auth, req.user is populated. 
    res.json(req.user);
  });

  app.patch(api.users.updateConfig.path, async (req, res) => {
    if (!req.isAuthenticated()) return res.sendStatus(401);
    
    try {
      const input = api.users.updateConfig.input.parse(req.body);
      // req.user has claims, but we need the actual user ID from our DB (which matches sub)
      const userId = (req.user as any).claims.sub; // or req.user.id if passport deserialized it that way. Replit Auth storage uses 'id' which IS the sub.
      
      const updatedUser = await storage.updateUserConfig(userId, input);
      res.json(updatedUser);
    } catch (err) {
      if (err instanceof z.ZodError) {
        return res.status(400).json({ message: err.errors[0].message });
      }
      res.status(500).json({ message: "Failed to update config" });
    }
  });


  // === STRATEGIES ===
  app.get(api.strategies.list.path, async (req, res) => {
    const strategies = await storage.getStrategies();
    res.json(strategies);
  });

  app.post(api.strategies.create.path, async (req, res) => {
    try {
      const input = api.strategies.create.input.parse(req.body);
      const strategy = await storage.createStrategy(input);
      res.status(201).json(strategy);
    } catch (err) {
      if (err instanceof z.ZodError) {
        return res.status(400).json({ message: err.errors[0].message });
      }
      throw err;
    }
  });

  app.put(api.strategies.update.path, async (req, res) => {
    const id = Number(req.params.id);
    const strategy = await storage.updateStrategy(id, req.body);
    res.json(strategy);
  });
  
  app.patch(api.strategies.toggle.path, async (req, res) => {
    const id = Number(req.params.id);
    const strategy = await storage.updateStrategy(id, { isActive: req.body.isActive });
    res.json(strategy);
  });


  // === TRADES ===
  app.get(api.trades.list.path, async (req, res) => {
    const limit = req.query.limit ? Number(req.query.limit) : 50;
    const symbol = req.query.symbol as string;
    const trades = await storage.getTrades(limit, symbol);
    res.json(trades);
  });

  app.get(api.trades.stats.path, async (req, res) => {
    const stats = await storage.getDashboardStats();
    res.json(stats);
  });


  // === PYTHON ENGINE CONTROL (Optional) ===
  // We can add an endpoint to start/stop the python engine
  app.post("/api/engine/start", (req, res) => {
    // This is just a placeholder. In a real app, we'd manage the process better.
    // const pythonProcess = spawn('python3', [path.join(process.cwd(), 'server/python/engine.py')]);
    res.json({ message: "Engine start signal sent" });
  });

  return httpServer;
}

// Seed function
async function seed() {
  const strategies = await storage.getStrategies();
  if (strategies.length === 0) {
    await storage.createStrategy({
      name: "Moving Average Crossover",
      description: "Simple SMA 50/200 crossover strategy",
      isActive: true,
      parameters: { shortWindow: 50, longWindow: 200 }
    });
    await storage.createStrategy({
      name: "RSI Mean Reversion",
      description: "Buy when RSI < 30, Sell when RSI > 70",
      isActive: false,
      parameters: { rsiPeriod: 14, overbought: 70, oversold: 30 }
    });
  }
}

// Call seed on startup (async)
seed().catch(console.error);
