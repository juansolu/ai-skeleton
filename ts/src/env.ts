import path from "node:path";
import { fileURLToPath } from "node:url";

export const here = path.dirname(fileURLToPath(import.meta.url));

// .env lives at the repo root, one level above ts/. On Vercel it does not exist; env comes from the deployment.
try {
  process.loadEnvFile(path.join(here, "..", "..", ".env"));
} catch {}

// vercel's filesystem is read-only except /tmp, and /tmp is wiped between invocations
export const RUNS_DIR =
  process.env.RUNS_DIR ?? (process.env.VERCEL ? "/tmp/runs" : path.join(here, "..", "runs"));
export const MODEL = process.env.MODEL ?? "claude-opus-5";
