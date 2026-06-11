import { Hono } from "hono";
import { cors } from "hono/cors";
import { logger } from "hono/logger";

import { loadConfig, type Config } from "@/config.js";
import { healthRoute } from "@/routes/health.js";

export function createApp(config: Config = loadConfig()): Hono {
  const app = new Hono();

  app.use("*", logger());
  app.use(
    "*",
    cors({
      origin: config.CORS_ORIGINS,
      allowMethods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
      credentials: true,
    }),
  );

  app.route(config.API_V1_PREFIX, healthRoute(config));

  app.notFound((c) => c.json({ error: "not_found" }, 404));
  app.onError((err, c) => {
    console.error("[gateway] unhandled", err);
    return c.json({ error: "internal_error" }, 500);
  });

  return app;
}
