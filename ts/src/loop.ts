// 101: the agentic loop.
//
//   npm run loop -- "What time is it? Remember it under last_run."
//
// One call to the model, run whatever tools it asked for, feed results back, repeat
// until it stops asking. Everything that happened lands in runs/<id>.json.
//
// The SDK ships a helper that does this loop for you (client.beta.messages.toolRunner).
// It is written out here because the loop is the point of 101.
import fs from "node:fs";
import path from "node:path";
import Anthropic from "@anthropic-ai/sdk";
import { MODEL, RUNS_DIR, here } from "./env";
import * as tools from "./tools";

const SYSTEM = fs.readFileSync(path.join(here, "system.md"), "utf8");
const MAX_TURNS = 10;

export let client = new Anthropic();
export function setClient(c: Anthropic) {
  client = c;
}

export type Trace = {
  id: string;
  task: string;
  model: string;
  steps: { tool: string; input: unknown; output: string }[];
  usage: { input: number; output: number };
  stop_reason?: string | null;
  output?: string;
  verdict?: Record<string, unknown>;
};

export async function run(task: string): Promise<Trace> {
  const id = stamp() + "-" + Math.random().toString(16).slice(2, 8);
  const messages: Anthropic.MessageParam[] = [{ role: "user", content: task }];
  const trace: Trace = { id, task, model: MODEL, steps: [], usage: { input: 0, output: 0 } };

  let response!: Anthropic.Message;
  for (let turn = 0; turn < MAX_TURNS; turn++) {
    response = await client.messages.create({
      model: MODEL,
      max_tokens: 16000,
      system: SYSTEM,
      tools: tools.SCHEMAS,
      messages,
    });
    trace.usage.input += response.usage.input_tokens;
    trace.usage.output += response.usage.output_tokens;
    messages.push({ role: "assistant", content: response.content });

    if (response.stop_reason !== "tool_use") break;

    const results: Anthropic.ToolResultBlockParam[] = [];
    for (const block of response.content) {
      if (block.type !== "tool_use") continue;
      const out = await tools.dispatch(block.name, block.input);
      trace.steps.push({ tool: block.name, input: block.input, output: out.slice(0, 2000) });
      results.push({ type: "tool_result", tool_use_id: block.id, content: out, is_error: out.startsWith("error:") });
    }
    messages.push({ role: "user", content: results });
  }

  // stop_reason still "tool_use" here means MAX_TURNS was hit
  trace.stop_reason = response.stop_reason;
  trace.output = response.content.filter((b) => b.type === "text").map((b) => b.text).join("");
  save(trace);
  return trace;
}

export function stamp(): string {
  const d = new Date().toISOString().replace(/[-:T]/g, "").slice(0, 14);
  return `${d.slice(0, 8)}-${d.slice(8)}`;
}

export function save(trace: Trace): string {
  fs.mkdirSync(RUNS_DIR, { recursive: true });
  const file = path.join(RUNS_DIR, `${trace.id}.json`);
  fs.writeFileSync(file, JSON.stringify(trace, null, 2));
  return file;
}

if (process.argv[1]?.endsWith("loop.ts")) {
  const task = process.argv.slice(2).join(" ") || "What time is it? Remember it under last_run.";
  const t = await run(task);
  console.log(t.output);
  console.error(
    `\n[${t.steps.length} tool calls, stop=${t.stop_reason}, tokens in/out=${t.usage.input}/${t.usage.output}, trace=${RUNS_DIR}/${t.id}.json]`,
  );
}
