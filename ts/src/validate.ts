// 201: a second agent judges the first.
//
//   npm run validate -- "task"
//
// Runs the loop, hands the trace and criteria.md to a reviewer, gets a structured
// verdict. Rejected runs go back to the loop with the feedback, up to MAX_ATTEMPTS.
// After that a human decides. That is the point: you review verdicts, not runs.
import fs from "node:fs";
import path from "node:path";
import Anthropic from "@anthropic-ai/sdk";
import { zodOutputFormat } from "@anthropic-ai/sdk/helpers/zod";
import { z } from "zod";
import { MODEL, here } from "./env";
import * as loop from "./loop";

const CRITERIA = fs.readFileSync(path.join(here, "criteria.md"), "utf8");
const MAX_ATTEMPTS = 3;
const client = new Anthropic();

const Verdict = z.object({
  approved: z.boolean(),
  score: z.number().int(),
  feedback: z.string(),
});
export type Verdict = z.infer<typeof Verdict>;

export async function validate(trace: loop.Trace): Promise<Verdict> {
  const response = await client.messages.parse({
    model: MODEL,
    max_tokens: 16000,
    system: "You are a strict reviewer. Judge the run against the criteria. Never fix the work yourself.",
    messages: [{ role: "user", content: `# Criteria\n${CRITERIA}\n\n# Run\n${JSON.stringify(trace, null, 2)}` }],
    output_config: { format: zodOutputFormat(Verdict) },
  });
  if (!response.parsed_output) throw new Error(`reviewer returned no verdict (stop_reason=${response.stop_reason})`);
  return response.parsed_output;
}

export async function runValidated(task: string): Promise<loop.Trace> {
  let feedback = "";
  let trace!: loop.Trace;
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    const prompt = feedback ? `${task}\n\nA reviewer rejected your last attempt. Their feedback:\n${feedback}` : task;
    trace = await loop.run(prompt);
    const verdict = await validate(trace);
    trace.verdict = { ...verdict, attempt };
    loop.save(trace);
    if (verdict.approved) return trace;
    feedback = verdict.feedback;
  }
  return trace;
}

if (process.argv[1]?.endsWith("validate.ts")) {
  const task = process.argv.slice(2).join(" ") || "What time is it? Remember it under last_run.";
  const t = await runValidated(task);
  console.log(t.output);
  console.error(`\nverdict: ${JSON.stringify(t.verdict, null, 2)}`);
}
