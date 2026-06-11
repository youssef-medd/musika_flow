import { serve } from "@hono/node-server";

import { createApp } from "@/app.js";
import { loadConfig } from "@/config.js";

const config = loadConfig();
const app = createApp(config);

serve(
  {
    fetch: app.fetch,
    port: config.PORT,
  },
  ({ port }) => {
    console.log(`[gateway] ${config.APP_NAME} listening on http://127.0.0.1:${port}`);
    console.log(`[gateway] health: http://127.0.0.1:${port}${config.API_V1_PREFIX}/health`);
  },
);
