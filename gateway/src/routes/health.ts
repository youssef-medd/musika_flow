import { Hono } from "hono";

import type { Config } from "@/config.js";

export function healthRoute(config: Config): Hono {
  const app = new Hono();

  app.get("/health", (c) =>
    c.json({
      status: "ok",
      service: config.APP_NAME,
      env: config.NODE_ENV,
      version: "0.1.0",
    }),
  );

  return app;
}
