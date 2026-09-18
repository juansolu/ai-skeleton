// 301: the agent reads its own history and proposes how to get better.
//
//   npm run improve
//
// Reads every trace in runs/, summarizes them, and asks the model for concrete edits
// to system.md, criteria.md, and tool descriptions, grounded in patterns across runs.
// Writes runs/improvements-<ts>.md. You read it and apply what you agree with.
// The human stays on the loop. Measure approval rate before and after.
import fs from "node:fs";
import path from "node:path";
import Anthropic from "@anthropic-ai/sdk";
import { MODEL, RUNS_DIR, here } from "./env";
import { stamp, type Trace } from "./loop";
import { SCHEMAS } from "./tools";

const client = new Anthropic();

export function loadTraces(): Trace[] {
  if (!fs.existsSync(RUNS_DIR)) return [];
  return fs
    .readdirSync(RUNS_DIR)
    .filter((f) => f.endsWith(".json") && f !== "memory.json")
    .sort()
    .map((f) => JSON.parse(fs.readFileSync(path.join(RUNS_DIR, f), "utf8")));
}

function summarize(t: Trace) {
  const v = (t.verdict ?? {}) as Record<string, unknown>;
  return {
    id: t.id,
    task: t.task.slice(0, 300),
    tools: t.steps.map((s) => s.tool),
    tool_errors: t.steps.filter((s) => s.output.startsWith("error:")).map((s) => s.output.slice(0, 200)),
    stop_reason: t.stop_reason,
    approved: v.approved,
    score: v.score,
    feedback: v.feedback,
    output: (t.output ?? "").slice(0, 500),
  };
}

export async function improve(): Promise<string> {
  const traces = loadTraces();
  if (traces.length === 0) throw new Error(`no traces in ${RUNS_DIR}. run the loop a few times first.`);
  const context = {
    system_prompt: fs.readFileSync(path.join(here, "system.md"), "utf8"),
    criteria: fs.readFileSync(path.join(here, "criteria.md"), "utf8"),
    tool_schemas: SCHEMAS,
    runs: traces.map(summarize),
  };
  const response = await client.messages.create({
    model: MODEL,
    max_tokens: 16000,
    system:
      "You improve an agent by reading its run history. Find patterns across runs, not one-offs. " +
      "Propose concrete edits to the system prompt, the criteria, or tool descriptions as exact " +
      "replacement text. For each edit, cite the run ids that motivate it. If the runs do not " +
      "support a change, say so.",
    messages: [{ role: "user", content: JSON.stringify(context, null, 2) }],
  });
  const report = response.content.filter((b) => b.type === "text").map((b) => b.text).join("");
  const out = path.join(RUNS_DIR, `improvements-${stamp()}.md`);
  fs.writeFileSync(out, report);
  return out;
}

if (process.argv[1]?.endsWith("improve.ts")) {
  const out = await improve();
  console.log(fs.readFileSync(out, "utf8"));
  console.error(`\n[saved ${out}]`);
}
