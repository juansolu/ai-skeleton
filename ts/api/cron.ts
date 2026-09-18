// 201: Vercel Cron hits this on the schedule in vercel.json, with Authorization: Bearer $CRON_SECRET
import type { VercelRequest, VercelResponse } from "@vercel/node";
import { runValidated } from "../src/validate";

export default async function handler(req: VercelRequest, res: VercelResponse) {
  const secret = process.env.CRON_SECRET;
  if (!secret || req.headers.authorization !== `Bearer ${secret}`) return res.status(401).json({ error: "unauthorized" });
  const task = process.env.CRON_TASK ?? "Recall what we stored under last_run and summarize it in one line.";
  return res.status(200).json(await runValidated(task));
}
