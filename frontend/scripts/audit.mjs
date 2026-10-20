// Usage: node scripts/audit.mjs <url> [more urls...]   (run against `next build && next start`, never `next dev`)
// Fails (exit 1) if any Lighthouse category is under MIN on mobile or desktop, or axe finds any violation.
/* eslint-disable no-restricted-properties */
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { launch } from "chrome-launcher";
import lighthouse from "lighthouse";
import desktopConfig from "lighthouse/core/config/desktop-config.js";
import puppeteer from "puppeteer-core";
import axe from "axe-core";

const MIN = Number(process.env.MIN_SCORE ?? 90); // hard floor is 80; we gate at 90
const URLS = process.argv.slice(2);
if (!URLS.length) throw new Error("pass at least one url");

const chrome = await launch({
  chromePath: process.env.CHROME_PATH,
  userDataDir: false, // chrome-launcher rewrites the profile path on WSL and a Linux Chrome then creates a stray dir in the cwd
  chromeFlags: [
    "--headless=new",
    "--no-sandbox",
    `--user-data-dir=${mkdtempSync(join(tmpdir(), "audit-chrome-"))}`,
  ],
});
const browser = await puppeteer.connect({ browserURL: `http://localhost:${chrome.port}` });
let failed = false;
const settings = {
  onlyCategories: ["performance", "accessibility", "best-practices", "seo"],
  throttlingMethod: "simulate",
};

for (const url of URLS) {
  for (const form of ["mobile", "desktop"]) {
    const { lhr } = await lighthouse(
      url,
      { port: chrome.port, output: "json", logLevel: "error" },
      // Desktop must use Lighthouse's desktop config: desktop scoring with mobile throttling fails any page
      form === "desktop"
        ? { ...desktopConfig, settings: { ...desktopConfig.settings, ...settings } }
        : { extends: "lighthouse:default", settings },
    );
    // Otherwise a failed run (e.g. NO_FCP) only shows up as every score reading 0
    if (lhr.runtimeError) console.log(`FAIL ${url} ${form} ${lhr.runtimeError.code}`);
    for (const c of Object.values(lhr.categories)) {
      const s = Math.round(c.score * 100);
      const bad = s < MIN;
      failed ||= bad;
      console.log(`${bad ? "FAIL" : "ok  "} ${url} ${form} ${c.id} ${s}`);
      if (bad || s < 100)
        for (const r of c.auditRefs) {
          const a = lhr.audits[r.id];
          if (a.score !== null && a.score < 1 && a.scoreDisplayMode !== "informative")
            console.log(`       - ${a.id}: ${a.title}`);
        }
    }
  }
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: "networkidle0" });
  await page.evaluate(axe.source);
  const { violations } = await page.evaluate(() =>
    axe.run({ runOnly: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa", "best-practice"] }),
  );
  await page.close();
  failed ||= violations.length > 0;
  console.log(`${violations.length ? "FAIL" : "ok  "} ${url} axe ${violations.length} violations`);
  for (const v of violations)
    for (const n of v.nodes) console.log(`       - ${v.id} (${v.impact}): ${n.target.join(" ")}`);
}

await browser.disconnect();
await chrome.kill();
process.exit(failed ? 1 : 0);
