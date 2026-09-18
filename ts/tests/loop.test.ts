// Runs without an API key: npm test
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { test } from "node:test";

process.env.ANTHROPIC_API_KEY = "test-key";
process.env.RUNS_DIR = fs.mkdtempSync(path.join(os.tmpdir(), "runs-"));

const loop = await import("../src/loop");
const tools = await import("../src/tools");

test("loop dispatches the tool and stops", async () => {
  let calls = 0;
  const usage = { input_tokens: 10, output_tokens: 5 };
  const fake = {
    messages: {
      async create(params: any) {
        calls++;
        if (calls === 1) {
          return { stop_reason: "tool_use", usage, content: [{ type: "tool_use", id: "t1", name: "get_time", input: {} }] };
        }
        // second request must carry the tool result back
        const last = params.messages.at(-1);
        assert.equal(last.role, "user");
        assert.equal(last.content[0].tool_use_id, "t1");
        assert.equal(last.content[0].is_error, false);
        return { stop_reason: "end_turn", usage, content: [{ type: "text", text: "done" }] };
      },
    },
  };
  loop.setClient(fake as any);
  const t = await loop.run("what time is it");
  assert.equal(calls, 2);
  assert.equal(t.steps[0].tool, "get_time");
  assert.equal(t.output, "done");
  assert.equal(t.stop_reason, "end_turn");
  assert.deepEqual(t.usage, { input: 20, output: 10 });
  assert.ok(fs.existsSync(path.join(process.env.RUNS_DIR!, `${t.id}.json`)));
});

test("unknown tool is error text, not a crash", async () => {
  assert.ok((await tools.dispatch("nope", {})).startsWith("error:"));
  assert.ok((await tools.dispatch("fetch_url", { url: "not a url" })).startsWith("error:"));
});

test("remember/recall roundtrip", () => {
  tools.remember({ key: "k", value: "v" });
  assert.equal(tools.recall({ key: "k" }), "v");
  assert.ok(tools.recall({ key: "missing" }).startsWith("nothing stored"));
});
