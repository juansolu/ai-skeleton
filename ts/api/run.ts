// 201: the trigger layer. Vercel runs this.
// POST /api/run  body {"task": "..."}, header Authorization: Bearer $WEBHOOK_SECRET
import type { VercelRequest, VercelResponse } from "@vercel/node";
import { runValidated } from "../src/validate";

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== "POST") return res.status(405).json({ error: "POST only" });
  const secret = process.env.WEBHOOK_SECRET;
  if (!secret || req.headers.authorization !== `Bearer ${secret}`) return res.status(401).json({ error: "unauthorized" });
  const task = req.body?.task;
  if (!task) return res.status(400).json({ error: 'body must be {"task": "..."}' });
  return res.status(200).json(await runValidated(task));
}
