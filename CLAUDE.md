# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repo status

Pre-code. The repo currently contains only product documentation, GitHub templates, and the issue-seeder script. No application code, monorepo scaffolding, or `package.json` exists yet. **Most "common commands" do not exist until Milestone 0 is executed.** Treat `docs/BUILD_PLAN.md` as the source of truth for what is supposed to land next.

## Source-of-truth documents

- `docs/firebase-cost-analysis.md` — Product/market analysis. ICP, pricing, competitive landscape, the full v1 rule list (Appendix A), and kill/continue gates (§12). Read before changing positioning, pricing, or rule scope.
- `docs/BUILD_PLAN.md` — Engineering execution plan. Locked tech decisions (§0), full tech BOM (§1), monorepo layout (§2), Prisma sketch (§3), and the week-by-week roadmap (§4) that the seeder script mirrors. Read before changing stack, schema, or milestone ordering.

Any deviation from the analysis doc's positions should be logged in `BUILD_PLAN.md` as a new section **before** writing code.

## Git Workflow (STRICT RULE)

**NEVER work directly on `main` or `dev`. Always create a feature branch.**

### Branch structure

- **`main`** — Production branch. Only merged into from `dev` after ALL issues in a phase are completed.
- **`dev`** — Integration branch. Only merged into from feature branches.
- **`feature/*`** — Created from `dev` for every GitHub issue. Format: `feature/issue-<number>-<short-description>`.
- **Flow:** `feature/*` → `dev` → `main`

### Steps for every issue

1. Move issue to "In Progress" on the project board.
2. `git checkout dev && git pull`
3. `git checkout -b feature/issue-<number>-<short-description>`
4. Do all work on the feature branch.
5. Run the mandatory 3-step review flow (see Development Workflow below).
6. **Wait for user approval before committing. Do NOT commit until the user explicitly clears it.**
7. Pull latest `dev` before merging: `git checkout dev && git pull && git checkout - && git merge dev`. Resolve any merge conflicts on the feature branch first.
8. After approval, commit and merge feature branch into `dev` with `--no-ff`.
9. Move issue to "Done": `gh issue close <number>` and update project board status.
10. Only after an entire phase is complete, merge `dev` into `main`.

## Development Workflow (Mandatory)

After completing every feature, the following 3-step review flow is strictly required before merging. Do not skip any step.

### Step 1 — Developer Explanation

Immediately after finishing a feature, provide a detailed explanation:
- What was done, why, and how — describe the feature, its purpose, and the approach taken.
- List ALL created/modified files with a one-line purpose for each.
- Explain the complete data flow through the system (e.g., UI → Provider → Repository → API/DB and back).

**Wait for the user to review before proceeding to Step 2.**

### Step 2 — Code Review

After the user has reviewed Step 1:
- Launch a code-reviewer agent to audit all feature code.
- List ALL issues found with their respective file names.
- For each issue: explain what it is, why it's a problem, and give a real-world example of the consequence if left unfixed.

**Present the full list to the user and wait for their decision before proceeding to Step 3.**

### Step 3 — Fix Approved Issues

After the user has reviewed Step 2:
- Fix only the issues the user has approved — do NOT fix issues the user has not approved.
- If fixes are substantial (new files, significant logic changes), repeat from Step 1 for the fixes.

### Testing (Mandatory)

Every feature must include unit tests. Tests are written as part of the feature, not after — they are included in the same branch and reviewed in the 3-step review flow above.

## Issue + PR workflow

Work is tracked as GitHub issues seeded by `scripts/seed_issues.py` against repo `ktul15/firecost`, project `Firecost Roadmap`. The script is **idempotent** — it skips issues whose title already exists, keyed on the exact `[TID] Title` form (e.g. `[M1-09] Rule: firestore/no-unbounded-snapshot + fixtures + docs`).

- Task IDs (`M0-01` … `M5-21`) are stable; never renumber. Adding a task = append with the next free ID in that milestone.
- Each issue body is generated from `BUILD_PLAN.md` §4 and includes a DoD checklist. The seeder applies labels `milestone:<m>`, `type:<…>`, `tier:<…>`, `size:<…>`, `priority:<…>` — keep these label families consistent when adding tasks.
- Run dry-run first: `python3 scripts/seed_issues.py --dry-run`. The script assumes `gh` is authenticated as `ktul15` (the analysis doc was written under user `mobilions`; this repo lives on a different GitHub identity — `gh auth switch -u ktul15` before running).
- PRs follow `.github/pull_request_template.md` and must reference the issue they close.

## Locked stack (from BUILD_PLAN §0–§1)

When scaffolding, do not substitute alternatives without updating the build plan first:

- **Runtime/lang:** Node 22 LTS, TypeScript 5.6 strict, pnpm 9, Turborepo 2
- **Lint/format:** Biome (not ESLint+Prettier)
- **Tests:** Vitest (not Jest)
- **Versioning:** Changesets, publishing only `packages/linter`, `packages/cli`, and the OSS subset of `packages/cost-core` to npm
- **Linter AST:** ts-morph primary, `@babel/parser`+`@babel/traverse` fallback
- **Backend:** Next.js 15 App Router (`apps/web`) for dashboard + marketing + Fumadocs, plus a Fastify+pg-boss worker (`apps/worker`) on Fly
- **DB/Auth:** Supabase Postgres + Supabase Auth (GitHub OAuth), Prisma 6, **RLS enforced on every org-scoped table**
- **Payments:** Stripe Checkout + Customer Portal + webhooks (signature verification mandatory)
- **Infra:** Fly.io (2 apps), Supabase, Cloudflare DNS, Sentry, Axiom, PostHog

## Architecture intent (multiple-file context)

These boundaries matter when adding code across packages:

1. **OSS vs private split.** `packages/{linter,cli}` (and a thin types subset of `cost-core`) are MIT and published to npm. Everything else (`apps/*`, `packages/{bq-ingest,db,ui,config}`, the rest of `cost-core`) is source-available but not redistributable. The dashboard application code lives in this repo but ships under the README's restricted license, not MIT. Do not import private packages from OSS packages.
2. **Rule authoring contract** (per BUILD_PLAN §5). Every new rule MUST ship with: (a) explicit confidence level (high/medium/low) justified in a doc comment; (b) ≥5 fixture cases under `packages/linter/fixtures/<rule-id>/{bad,good}-*.ts` driven by an auto-loading Vitest harness; (c) a docs page describing pattern, bad/good example, and "why it costs $"; (d) default severity per the analysis-doc Appendix A table, downgradeable via `firecost.config.ts`. Rules with >5% disable rate in telemetry get demoted to low-confidence + off-by-default.
3. **Engine pipeline.** Files → ts-morph Project loader (`engine/project.ts`) → rule runner iterating registered rules → diagnostics (`engine/diagnostic.ts`) → reporters (`reporters/{cli,json,github-actions,sarif}.ts`). Inline suppression via `// firecost-disable-next-line <rule-id>` is parsed in the engine, not per rule.
4. **Cost-attribution data flow.** BigQuery billing export (`packages/bq-ingest`) → normalized `CostSnapshot` rows in Postgres → `packages/cost-core` projection math (linear regression + weekly seasonality) → Next.js dashboard. Nightly pulls scheduled via pg-boss in the worker app. Runtime SDK shim (`@firecost/firestore`, Milestone 4) is a separate ingest path writing to `SdkEvent` with hourly rollups.
5. **Plan-gated features.** Feature gates live in `lib/plan-gate.ts` on the dashboard; PR bot is Growth-tier, SDK shim is Scale-tier. Always gate at the middleware layer, not only the UI.

## Security non-negotiables (BUILD_PLAN §5)

- Firebase service account JSON encrypted at rest with libsodium sealed box; key in Fly secrets.
- Stripe webhook signatures verified on every request — **no skip path** even in dev.
- Supabase RLS on every multi-tenant table.
- Customer Firestore data is never persisted — only aggregate counts, paths, and stack hashes.
- SDK-shim PII redaction on by default for user-id-shaped path segments; configurable redactor required.

## Expected commands (once Milestone 0 lands)

These will exist after `M0-02` (pnpm + Turborepo init) and `M0-10` (CI workflow). Until then they will fail.

```bash
pnpm install
pnpm turbo run build          # build all packages/apps
pnpm turbo run lint           # Biome
pnpm turbo run typecheck      # tsc across the workspace
pnpm turbo run test           # Vitest, all packages
pnpm --filter @firecost/linter test           # single package
pnpm --filter @firecost/linter test -- <pattern>   # single file/test
pnpm changeset                # create a changeset before publishing OSS packages
```

When adding scripts to `package.json` files, prefer `turbo` orchestration over direct invocations so CI affected-only builds work.

## What not to do

- Do not add LLM-powered rules or AI features before Month 4 (BUILD_PLAN §0 — ship deterministic rules first).
- Do not add Dart/Swift/Kotlin rules before Milestone 5; TypeScript-only through Milestone 4.
- Do not introduce ESLint/Prettier/Jest — the stack is intentionally Biome+Vitest.
- Do not publish private packages to npm. Use `publishConfig` + Changesets gating.
- Do not skip the OSS linter's `RuleHit` opt-out — anonymous-by-default with `firecost telemetry off` is the contract.
- Do not bypass the rule-authoring contract above when adding rules under time pressure.
