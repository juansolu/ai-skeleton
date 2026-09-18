// Tools the agent can call. Add yours here (or ask Claude Code: /add-tool).
// Three edits per tool: the function, an entry in HANDLERS, a schema in SCHEMAS.
import fs from "node:fs";
import path from "node:path";
import type Anthropic from "@anthropic-ai/sdk";
import { RUNS_DIR } from "./env";

const MEMORY = path.join(RUNS_DIR, "memory.json");

export function getTime(): string {
  return new Date().toISOString();
}

export async function fetchUrl({ url }: { url: string }): Promise<string> {
  const res = await fetch(url, { signal: AbortSignal.timeout(10_000) });
  return (await res.text()).slice(0, 20_000);
}

export function remember({ key, value }: { key: string; value: string }): string {
  const data = load();
  data[key] = value;
  fs.mkdirSync(RUNS_DIR, { recursive: true });
  fs.writeFileSync(MEMORY, JSON.stringify(data, null, 2));
  return `stored ${key}`;
}

export function recall({ key }: { key: string }): string {
  return load()[key] ?? `nothing stored under ${key}`;
}

function load(): Record<string, string> {
  return fs.existsSync(MEMORY) ? JSON.parse(fs.readFileSync(MEMORY, "utf8")) : {};
}

type Handler = (args: any) => string | Promise<string>;

export const HANDLERS: Record<string, Handler> = {
  get_time: getTime,
  fetch_url: fetchUrl,
  remember,
  recall,
};

// the description is the only thing the model reads when deciding to call a tool. write it for the model.
export const SCHEMAS: Anthropic.Tool[] = [
  {
    name: "get_time",
    description: "Current UTC time as ISO 8601.",
    input_schema: { type: "object", properties: {} },
  },
  {
    name: "fetch_url",
    description: "HTTP GET a public URL. Returns the first 20KB of the body as text.",
    input_schema: {
      type: "object",
      properties: { url: { type: "string", description: "Absolute http(s) URL." } },
      required: ["url"],
    },
  },
  {
    name: "remember",
    description: "Persist a key/value so a future run can read it with recall.",
    input_schema: {
      type: "object",
      properties: { key: { type: "string" }, value: { type: "string" } },
      required: ["key", "value"],
    },
  },
  {
    name: "recall",
    description: "Read a value stored by remember in this or an earlier run.",
    input_schema: {
      type: "object",
      properties: { key: { type: "string" } },
      required: ["key"],
    },
  },
];

export async function dispatch(name: string, args: unknown): Promise<string> {
  const fn = HANDLERS[name];
  if (!fn) return `error: unknown tool ${name}`;
  try {
    return String(await fn(args));
  } catch (e) {
    // errors go back to the model as text so it can recover
    return `error: ${e instanceof Error ? `${e.name}: ${e.message}` : String(e)}`;
  }
}
