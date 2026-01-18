import { z } from 'zod';
import { insertStrategySchema, insertTradeSchema, strategies, trades } from './schema';
import { users } from './models/auth';

export const errorSchemas = {
  validation: z.object({
    message: z.string(),
    field: z.string().optional(),
  }),
  notFound: z.object({
    message: z.string(),
  }),
  internal: z.object({
    message: z.string(),
  }),
};

export const api = {
  // User Management
  users: {
    me: {
      method: 'GET' as const,
      path: '/api/users/me',
      responses: {
        200: z.custom<typeof users.$inferSelect>(),
        401: errorSchemas.internal, // Not authenticated
      },
    },
    updateConfig: {
      method: 'PATCH' as const,
      path: '/api/users/config',
      input: z.object({
        growwApiKey: z.string().optional(),
        growwApiSecret: z.string().optional(),
      }),
      responses: {
        200: z.custom<typeof users.$inferSelect>(),
        400: errorSchemas.validation,
      },
    },
  },

  // Strategy Management
  strategies: {
    list: {
      method: 'GET' as const,
      path: '/api/strategies',
      responses: {
        200: z.array(z.custom<typeof strategies.$inferSelect>()),
      },
    },
    create: {
      method: 'POST' as const,
      path: '/api/strategies',
      input: insertStrategySchema,
      responses: {
        201: z.custom<typeof strategies.$inferSelect>(),
        400: errorSchemas.validation,
      },
    },
    update: {
      method: 'PUT' as const,
      path: '/api/strategies/:id',
      input: insertStrategySchema.partial(),
      responses: {
        200: z.custom<typeof strategies.$inferSelect>(),
        404: errorSchemas.notFound,
      },
    },
    toggle: {
      method: 'PATCH' as const,
      path: '/api/strategies/:id/toggle',
      input: z.object({ isActive: z.boolean() }),
      responses: {
        200: z.custom<typeof strategies.$inferSelect>(),
        404: errorSchemas.notFound,
      },
    },
  },

  // Trade Monitoring
  trades: {
    list: {
      method: 'GET' as const,
      path: '/api/trades',
      input: z.object({
        limit: z.coerce.number().optional(),
        symbol: z.string().optional(),
      }).optional(),
      responses: {
        200: z.array(z.custom<typeof trades.$inferSelect>()),
      },
    },
    stats: {
      method: 'GET' as const,
      path: '/api/stats',
      responses: {
        200: z.object({
          totalTrades: z.number(),
          totalVolume: z.number(),
          totalPnl: z.number(),
          activeStrategies: z.number(),
        }),
      },
    },
  },
};

export function buildUrl(path: string, params?: Record<string, string | number>): string {
  let url = path;
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (url.includes(`:${key}`)) {
        url = url.replace(`:${key}`, String(value));
      }
    });
  }
  return url;
}
