import { db } from "./db";
import {
  strategies, trades,
  type Strategy, type InsertStrategy, type UpdateStrategyRequest,
  type Trade, type InsertTrade, type DashboardStats
} from "@shared/schema";
import { users, type User } from "@shared/models/auth";
import { eq, desc, sql } from "drizzle-orm";

export interface IStorage {
  // Users
  getUser(id: string): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  // updateUserConfig(id: string, config: { growwApiKey?: string; growwApiSecret?: string }): Promise<User>;

  // Strategies
  createStrategy(strategy: InsertStrategy): Promise<Strategy>;
  getStrategies(): Promise<Strategy[]>;
  getStrategy(id: number): Promise<Strategy | undefined>;
  updateStrategy(id: number, update: UpdateStrategyRequest): Promise<Strategy>;
  deleteStrategy(id: number): Promise<void>;

  // Trades
  createTrade(trade: InsertTrade): Promise<Trade>;
  getTrades(limit?: number, symbol?: string): Promise<Trade[]>;
  
  // Stats
  getDashboardStats(): Promise<DashboardStats>;
}

export class DatabaseStorage implements IStorage {
  async getUser(id: string): Promise<User | undefined> {
    const [user] = await db.select().from(users).where(eq(users.id, id));
    return user;
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    // Note: auth users table might not have 'username' depending on the schema from blueprint
    // Checking shared/models/auth.ts... it has 'email', 'firstName', 'lastName', but NOT 'username'.
    // It has 'email' as unique. I'll use email for lookup if needed, or remove this method if unused.
    // For now, I'll comment it out or adapt it.
    // const [user] = await db.select().from(users).where(eq(users.email, username));
    return undefined; // Not implemented for now
  }

  // async updateUserConfig(id: string, config: { growwApiKey?: string; growwApiSecret?: string }): Promise<User> {
    // Requires schema update to users table
  //  return undefined as any;
  // }

  async createStrategy(strategy: InsertStrategy): Promise<Strategy> {
    const [newStrategy] = await db.insert(strategies).values(strategy).returning();
    return newStrategy;
  }

  async getStrategies(): Promise<Strategy[]> {
    return await db.select().from(strategies).orderBy(desc(strategies.createdAt));
  }

  async getStrategy(id: number): Promise<Strategy | undefined> {
    const [strategy] = await db.select().from(strategies).where(eq(strategies.id, id));
    return strategy;
  }

  async updateStrategy(id: number, update: UpdateStrategyRequest): Promise<Strategy> {
    const [updated] = await db.update(strategies)
      .set(update)
      .where(eq(strategies.id, id))
      .returning();
    return updated;
  }

  async deleteStrategy(id: number): Promise<void> {
    await db.delete(strategies).where(eq(strategies.id, id));
  }

  async createTrade(trade: InsertTrade): Promise<Trade> {
    const [newTrade] = await db.insert(trades).values(trade).returning();
    return newTrade;
  }

  async getTrades(limit: number = 50, symbol?: string): Promise<Trade[]> {
    if (symbol) {
       return await db.select().from(trades).where(eq(trades.symbol, symbol)).orderBy(desc(trades.timestamp)).limit(limit);
    }
    return await db.select().from(trades).orderBy(desc(trades.timestamp)).limit(limit);
  }

  async getDashboardStats(): Promise<DashboardStats> {
    const [tradeStats] = await db.select({
      count: sql<number>`count(*)`,
      volume: sql<number>`sum(${trades.quantity})`,
      pnl: sql<number>`sum(${trades.pnl})`
    }).from(trades);

    const [activeStrategies] = await db.select({
      count: sql<number>`count(*)`
    }).from(strategies).where(eq(strategies.isActive, true));

    return {
      totalTrades: Number(tradeStats?.count || 0),
      totalVolume: Number(tradeStats?.volume || 0),
      totalPnl: Number(tradeStats?.pnl || 0),
      activeStrategies: Number(activeStrategies?.count || 0),
    };
  }
}

export const storage = new DatabaseStorage();
