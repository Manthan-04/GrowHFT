import { pgTable, text, serial, integer, boolean, timestamp, jsonb, decimal, varchar } from "drizzle-orm/pg-core";
import { relations } from "drizzle-orm";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";
import { users } from "./models/auth";

// Re-export users for convenience if needed, but better to import from models/auth
export { users } from "./models/auth";

// === TABLE DEFINITIONS ===

export const strategies = pgTable("strategies", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  description: text("description"),
  isActive: boolean("is_active").default(false),
  parameters: jsonb("parameters").$type<Record<string, any>>(),
  createdAt: timestamp("created_at").defaultNow(),
});

export const trades = pgTable("trades", {
  id: serial("id").primaryKey(),
  // User ID is now a UUID string referencing the auth users table
  userId: varchar("user_id").references(() => users.id),
  symbol: text("symbol").notNull(),
  side: text("side").notNull(), // 'BUY' or 'SELL'
  quantity: integer("quantity").notNull(),
  price: decimal("price").notNull(),
  status: text("status").notNull(), // 'PENDING', 'EXECUTED', 'FAILED'
  timestamp: timestamp("timestamp").defaultNow(),
  strategyId: integer("strategy_id").references(() => strategies.id),
  pnl: decimal("pnl"),
});

// === RELATIONS ===
export const usersRelations = relations(users, ({ many }) => ({
  trades: many(trades),
}));

export const tradesRelations = relations(trades, ({ one }) => ({
  user: one(users, {
    fields: [trades.userId],
    references: [users.id],
  }),
  strategy: one(strategies, {
    fields: [trades.strategyId],
    references: [strategies.id],
  }),
}));

// === BASE SCHEMAS ===
export const insertStrategySchema = createInsertSchema(strategies).omit({ id: true, createdAt: true });
export const insertTradeSchema = createInsertSchema(trades).omit({ id: true, timestamp: true });

// === EXPLICIT API CONTRACT TYPES ===
// User type comes from auth.ts
export type { User, InsertUser } from "./models/auth";

export type Strategy = typeof strategies.$inferSelect;
export type InsertStrategy = z.infer<typeof insertStrategySchema>;

export type Trade = typeof trades.$inferSelect;
export type InsertTrade = z.infer<typeof insertTradeSchema>;

export type TradeResponse = Trade;
export type StrategyResponse = Strategy;

export type CreateStrategyRequest = InsertStrategy;
export type UpdateStrategyRequest = Partial<InsertStrategy>;

// Dashboard Stats
export interface DashboardStats {
  totalTrades: number;
  totalVolume: number;
  totalPnl: number;
  activeStrategies: number;
}
