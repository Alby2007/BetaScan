// trpc variant of ../run_mutants.mjs. Runs INSIDE the container, cwd=/repo.
// node run_mutants.mjs jobs.json out.json
// jobs: [{id,file,start,end,replacement,tests:[...]}]. For each: splice, run vitest on `tests`, record failing files, restore.
// Differs from h3 version: no vitest.mut.config.mjs override (workspace aliases in vitest.shared.ts are required),
// --retry=0 to stop the shared config's CI retry masking kills, larger timeouts (env-tunable).
import fs from "node:fs"; import { spawnSync } from "node:child_process";
const jobs = JSON.parse(fs.readFileSync(process.argv[2])); const res = [];
const TMO = Number(process.env.MUT_TMO_MS || 300000), SPLIT_TMO = Number(process.env.MUT_SPLIT_TMO_MS || 90000);
const run = (tests, tmo = TMO) => {
  try { fs.rmSync("/tmp/vr.json"); } catch {}
  const p = spawnSync("pnpm", ["exec", "vitest", "--run", "--retry=0", "--reporter=json", "--outputFile=/tmp/vr.json", ...tests], { encoding: "utf8", timeout: tmo, env: { ...process.env, CI: "true" } });
  if (p.error || !fs.existsSync("/tmp/vr.json")) return { error: String(p.error ?? "no report"), failed: [] };
  const r = JSON.parse(fs.readFileSync("/tmp/vr.json"));
  return { failed: r.testResults.filter((f) => f.status !== "passed").map((f) => f.name.replace(/^\/repo\//, "")) };
};
for (const j of jobs) {
  const orig = fs.readFileSync(j.file, "utf8"); let r = { failed: [], status: "NoCoverage" };
  if (j.tests.length) {
    fs.writeFileSync(j.file, orig.slice(0, j.start) + j.replacement + orig.slice(j.end));
    try {
      const t0 = Date.now();
      if (j.split) {
        // per-file mode for mutants that hung the batch run: a file that fails OR times out counts as failing, confirmed by a second run
        const hit = (t) => { const x = run([t], SPLIT_TMO); return x.error || x.failed.length ? t : null; };
        const first = j.tests.map(hit).filter(Boolean); const second = new Set(first.map(hit).filter(Boolean));
        r = { failed: first.filter((t) => second.has(t)), status: "" }; r.status = r.failed.length ? "Killed" : "Survived"; r.via = "split-timeout"; r.secs = (Date.now() - t0) / 1000;
        res.push({ id: j.id, status: r.status, killed_by_files: r.failed, secs: r.secs, via: r.via }); fs.writeFileSync(process.argv[3], JSON.stringify(res)); continue;
      }
      r = run(j.tests);
      if (r.error) r.status = "Error";
      else if (r.failed.length) { const r2 = run(j.tests); r.failed = r.failed.filter((f) => r2.failed.includes(f)); r.status = r.failed.length ? "Killed" : "Flaky"; }
      else r.status = "Survived";
      r.secs = (Date.now() - t0) / 1000;
    } finally { fs.writeFileSync(j.file, orig); }
  }
  res.push({ id: j.id, status: r.status, killed_by_files: r.failed, secs: r.secs ?? 0 });
  fs.writeFileSync(process.argv[3], JSON.stringify(res));
}
