import "dotenv/config";
import { z } from "zod";

const csv = z
  .string()
  .transform((s) => s.split(",").map((v) => v.trim()).filter(Boolean));

const ConfigSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  PORT: z.coerce.number().int().positive().default(8080),
  APP_NAME: z.string().default("HummingID"),
  API_V1_PREFIX: z.string().startsWith("/").default("/api/v1"),
  ML_SERVICE_URL: z.url().default("http://127.0.0.1:8000"),
  CORS_ORIGINS: csv.default("http://localhost:3000"),
  MAX_UPLOAD_BYTES: z.coerce.number().int().positive().default(5 * 1024 * 1024),
  MAX_AUDIO_SECONDS: z.coerce.number().int().positive().default(30),
});

export type Config = z.infer<typeof ConfigSchema>;

let cached: Config | undefined;

export function loadConfig(env: NodeJS.ProcessEnv = process.env): Config {
  if (cached) return cached;
  const parsed = ConfigSchema.safeParse(env);
  if (!parsed.success) {
    const issues = parsed.error.issues
      .map((i) => `  - ${i.path.join(".") || "<root>"}: ${i.message}`)
      .join("\n");
    throw new Error(`Invalid environment configuration:\n${issues}`);
  }
  cached = parsed.data;
  return cached;
}

export function resetConfigForTests(): void {
  cached = undefined;
}
