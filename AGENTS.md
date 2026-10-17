# AGENTS.md — tiroltourismus

Instructions for all agents (Gas Town: Mayor, Polecat, Refinery — and any other
AI assistant) working in this repository. Read this file before starting any task.

## Project

- **Name:** tiroltourismus — tourism portal for Tirol (Austria).
- **Stack:** Astro 5 static site. JSON-driven content lives in `src/data/`.
- **Languages (8):** `de`, `en`, `it`, `fr`, `nl`, `es`, `cs`, `zh`.
  Every content entry must exist in all 8 languages.
- **Hosting:** Cloudflare Pages. Build and multi-language deploy are defined in
  `wrangler.toml` and `.github/workflows/deploy.yml`.
  **Do NOT edit `wrangler.toml` or `deploy.yml`** — they are owned by the
  deployment pipeline.

## Roles

- **Mayor** — coordinates the work, splits tasks into small units, tracks
  progress, and reports status to Vali.
- **Polecat** — implements a task in its own git worktree / branch. Never
  merges; hands off a branch and a report.
- **Refinery** — reviews work, opens pull requests, and verifies the gates.
  The Refinery **never merges to `master`** — only Vali approves and merges.

## Hard rules

- **PR-only.** Never push directly to `master`. All work goes through a pull
  request. Only Vali merges.
- **No force-push, no history rewrite** (no `git push --force`, no rebase of
  shared branches, no `filter-branch`).
- **No deploys.** Never run a deploy or a deploy workflow.
- **Secrets are off-limits.** Never read, print, echo, or commit `.env`,
  `.env_temp`, or any other secret/key file. Do not touch CI secrets.
- **Paywall and LemonSqueezy are taboo.** Do not modify or reference paywall,
  gated-content, or LemonSqueezy code, copy, or configuration. Ask Vali first.
- **No emails and no public posts.** Do not send mail, do not post publicly.
- **Facts only, with live deep-link sources.** Every factual content claim needs
  a working `https://` source that deep-links the specific page. Prefer the
  business's own website as the first source. **Never** use a tourism-board home
  page as a source.
- **Tyrol-only content.** Only Tirol locations belong on the site.
- **Hide non-Tyrol entries** by listing the slug in
  `src/data/_hidden-nicht-tirol.json` and adding matching 301 redirect rules to
  `public/_redirects`. **Place static 301 rules BEFORE the splat (`*`) rules.**
  Cloudflare counts every rule after a dynamic rule as dynamic, and allows only
  **100 dynamic rules**.
- **Money:** if anything would cost money, stop and ask Vali first.

## Task size

- One task = **one collection**.
- **Max 10–20 slugs** per task.
- **Change all 8 languages together** — never ship a partial translation.

## Required gates before Done

Run these using the exact `package.json` script names, and report the output:

1. `npm run test:content` — content unit tests.
2. `npm run check:content -- --no-network` — fast offline content gate; **must
   pass**.
3. `npm run check:content` — network link check; **report the results**
   (advisory: third-party dead links can be flaky).
4. `npm run build` — required when layout, config, or scripts change.
   Content-only tasks may skip it if the CI build is already green.

## Hand-off

When a task is Done, report:

- **Task id**
- **Slugs** changed (with the collection)
- **Sources** (live deep-links used)
- **Gate output** (the results of the required gates above)
- **Open questions for Vali**
