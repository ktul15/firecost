# Build Plan — Firebase Cost Predictor + Query Linter

**Date:** 2026-05-12
**Companion to:** [firebase-cost-analysis.md](./firebase-cost-analysis.md)
**Cadence:** 15–20 hrs/week (heavy side-project)
**Target:** MVP revenue by month 6, $5K MRR kill-or-continue gate at month 9

---

## 0. Locked Decisions (Interview Output)

| Area | Choice | Why |
|---|---|---|
| Backend lang | **TypeScript / Node 22 LTS** | Same lang as customer code, native AST tooling (ts-morph, Babel) |
| Frontend | **Next.js 15 (App Router) + Tailwind + shadcn/ui** | Default dev-tool stack, large talent pool |
| Hosting | **Fly.io (apps) + Supabase (Postgres + Auth)** | Cheap, bundled, low ops for solo dev |
| Auth | **Supabase Auth, GitHub OAuth primary** | Right vibe for dev-tool buyer, free |
| Repo | **Monorepo (pnpm + Turborepo), MIT** | One repo, public + private packages |
| Linter v1 surface | **Standalone CLI** (npx) | Fastest ship, no ESLint plugin maintenance |
| Cost data | **BigQuery billing export only** | Most accurate; customer enables export (5 min) |
| Payments | **Stripe Checkout + Customer Portal** | Self-serve, ~1 day integration |
| SDK shim | **Month 4–6** | After OSS traction + dashboard prove value |
| LLM features | **None in v1**, add month 4+ | Ship deterministic rules first |
| Queue | **pg-boss** (Postgres-backed) | Reuses Supabase, no extra infra |
| Observability | **Sentry + Axiom** | Free tiers cover v1 |
| PR bot | **Month 3**, gated to Growth tier | Drives Growth tier upgrade |
| OSS telemetry | **Anonymous opt-out** | Standard, drives rule prioritization |
| Design partners | **None yet** → Milestone 0 = source 3 | OSS launch doubles as lead-gen |

---

## 1. Tech Stack — Full Bill of Materials

### Core runtime
- **Node 22 LTS** everywhere
- **pnpm 9** + **Turborepo 2** for monorepo
- **TypeScript 5.6** strict mode
- **Biome** for lint+format (faster than ESLint+Prettier, fewer configs)

### Linter package
- **ts-morph** — primary AST walker (high-level wrapper over TS compiler)
- **@babel/parser** + **@babel/traverse** — fallback for non-TS JS, JSX edge cases
- **commander** — CLI arg parsing
- **picocolors** + **ora** — terminal UX (no chalk; lighter)
- **cosmiconfig** — load `firecost.config.{ts,js,json}`
- **vitest** — tests (not jest; faster, ESM-native)
- **changesets** — version + publish to npm

### Cost predictor package
- **@google-cloud/bigquery** — pull billing export
- **firebase-admin** — service account auth + lightweight usage reads
- **zod** — config + API payload validation
- **date-fns** — time math, no moment
- **simple-statistics** — linear regression for trend projection (no need for full stats lib)

### Backend API (Next.js Route Handlers + standalone Fly worker)
- **Next.js 15** route handlers for dashboard API
- **Fastify** standalone worker on Fly for long-running ingestion jobs (separate process from Next)
- **Prisma 6** ORM against Supabase Postgres
- **pg-boss** queue (Postgres-backed)
- **Stripe Node SDK**
- **@octokit/app** — GitHub App (month 3)

### Frontend dashboard
- **Next.js 15 App Router**, RSC + Server Actions
- **Tailwind 4** + **shadcn/ui**
- **Recharts** — cost charts (or **visx** if more flexibility needed)
- **TanStack Table** — query/rule explorer tables
- **next-safe-action** — typed server actions
- **Supabase JS client** — auth on client

### Auth + DB
- **Supabase Postgres** (free → Pro at $25/mo when needed)
- **Supabase Auth** — GitHub OAuth, magic link as fallback
- Row Level Security on multi-tenant tables, enforced at DB

### Infra + ops
- **Fly.io** — 2 apps: `firecost-web` (Next.js) + `firecost-worker` (Fastify + pg-boss)
- **Supabase** — DB + Auth + storage for uploaded reports
- **Cloudflare** — DNS + edge cache for marketing site
- **Sentry** — errors (Node + browser)
- **Axiom** — structured logs, BQ-style query
- **PostHog Cloud** — product analytics + CLI telemetry endpoint
- **GitHub Actions** — CI: build, test, publish, deploy

### Payments
- **Stripe** — Checkout + Customer Portal + webhooks
- Pricing IDs: starter_monthly, growth_monthly, scale_monthly + annual variants

### Marketing site
- Same Next.js app, `/` route. No separate Astro/Hugo until needed.
- **Fumadocs** for docs (better than Nextra for App Router)

---

## 2. Monorepo Layout

```
firecost/
├── apps/
│   ├── web/                  # Next.js 15 dashboard + marketing + docs
│   └── worker/               # Fastify + pg-boss ingestion worker
├── packages/
│   ├── linter/               # @firecost/linter — OSS, published to npm
│   │   ├── rules/            # one file per rule
│   │   ├── engine/           # AST walkers, rule runner
│   │   └── reporters/        # cli, json, github-actions, sarif
│   ├── cli/                  # @firecost/cli — npx entrypoint, depends on linter
│   ├── cost-core/            # @firecost/cost-core — projection math, shared types
│   ├── bq-ingest/            # BigQuery billing pull adapter
│   ├── db/                   # Prisma schema + client
│   ├── config/               # Shared tsconfig, biome, env zod schemas
│   └── ui/                   # shared shadcn components used in web
├── .changeset/
├── turbo.json
├── pnpm-workspace.yaml
└── package.json
```

OSS-public: `packages/linter`, `packages/cli`, plus a thin `packages/cost-core` types subset. Everything else private.

Use **pnpm publishConfig** + Changesets to publish only OSS packages to npm.

---

## 3. Database Schema (initial)

Prisma sketch. Iterate per phase.

```prisma
model Org {
  id            String   @id @default(cuid())
  name          String
  stripeCustomerId String? @unique
  plan          Plan     @default(FREE)
  createdAt     DateTime @default(now())
  members       Membership[]
  projects      Project[]
}

model User {
  id            String   @id @default(cuid())
  email         String   @unique
  authId        String   @unique  // supabase auth uid
  memberships   Membership[]
}

model Membership {
  id      String @id @default(cuid())
  orgId   String
  userId  String
  role    Role   @default(MEMBER)
  org     Org    @relation(fields: [orgId], references: [id])
  user    User   @relation(fields: [userId], references: [id])
  @@unique([orgId, userId])
}

model Project {
  id              String @id @default(cuid())
  orgId           String
  firebaseProjectId String
  bqDataset       String?
  saCredentialRef String?   // path in Supabase storage, encrypted
  createdAt       DateTime  @default(now())
  org             Org       @relation(fields: [orgId], references: [id])
  costSnapshots   CostSnapshot[]
}

model CostSnapshot {
  id          String   @id @default(cuid())
  projectId   String
  capturedAt  DateTime @default(now())
  service     String   // firestore, functions, storage, etc
  metric      String   // reads, writes, gb-seconds
  unitsUsed   BigInt
  costUsd     Decimal  @db.Decimal(12, 4)
  collection  String?  // when attributable
  @@index([projectId, capturedAt])
}

model RuleHit {            // telemetry from OSS CLI (anonymized)
  id          String   @id @default(cuid())
  ruleId      String
  cliVersion  String
  anonId      String   // hashed machine id, opt-out aware
  occurredAt  DateTime @default(now())
  @@index([ruleId, occurredAt])
}

enum Plan  { FREE STARTER GROWTH SCALE ENTERPRISE }
enum Role  { OWNER ADMIN MEMBER }
```

Add later (month 4+): `SdkEvent` (runtime attribution), `Repo` + `PullRequest` (GitHub App).

---

## 4. Phased Roadmap

Phases keyed to weeks of side-project effort (15–20 hrs/wk). Gates from analysis doc §12 enforced at month 3 / 6 / 9.

### Milestone 0 — Foundations (Week 0, ~1 week)

Get the boring stuff out of the way before any product code.

- [ ] Create GitHub org `firecost` (or chosen name; check npm + github availability)
- [ ] Register domain (firecost.dev / costlens.dev / similar). Cloudflare DNS.
- [ ] Init monorepo: pnpm, Turborepo, Biome, TS strict, Vitest, Changesets
- [ ] Init Supabase project (DB + Auth, GitHub OAuth app)
- [ ] Init Fly orgs + 2 placeholder apps
- [ ] Sentry + Axiom + PostHog projects created
- [ ] Stripe account in test mode
- [ ] **Source design partners:** post in Flutter Discord + r/Firebase + personal Twitter asking for startups with bill-shock pain who'll trial. **Goal: 3 verbal commitments by end of week 2.**

Exit criteria: monorepo builds + deploys "hello world" to Fly. 3 design-partner conversations booked.

### Milestone 1 — OSS Linter v0.1 (Weeks 1–6, ~6 weeks)

Ship the OSS linter. This is the funnel; everything else depends on it.

**Week 1 — Engine skeleton**
- `packages/linter` scaffold
- `Rule` interface: `id`, `severity`, `confidence`, `check(node, ctx)`, `fix?`
- `Engine`: load files, build ts-morph Project, walk per rule, collect diagnostics
- `Reporter` interface + CLI reporter (pretty terminal output)
- Vitest harness with fixture-based tests (`fixtures/<rule-id>/{bad,good}.ts`)

**Week 2 — First 4 rules**
Pick highest-confidence, lowest-FP rules first:
- `firestore/no-unbounded-snapshot`
- `firestore/no-unbounded-get`
- `firestore/cleanup-listener`
- `firestore/no-empty-where`

Each rule must have ≥5 fixture cases (3 bad, 2 good edge cases).

**Week 3 — Next 4 rules**
- `firestore/no-loop-read`
- `firestore/no-large-batch-get`
- `firestore/limit-or-pagination`
- `functions/no-trigger-self-write`

**Week 4 — Final 4 rules + config**
- `firestore/no-redundant-listener`
- `firestore/prefer-collection-group-with-index`
- `firestore/index-write-amplification`
- `firestore/no-debug-listener-in-prod`
- Cosmiconfig: `firecost.config.ts` with rule enable/disable, severity overrides
- `// firecost-disable-next-line <rule-id>` inline suppression

**Week 5 — CLI polish + reporters**
- `packages/cli` with `firecost lint`, `firecost init`, `firecost rules`
- Reporters: `json`, `github-actions` (annotation format), `sarif`
- GitHub Actions example workflow in repo
- Anonymous opt-out telemetry: `firecost telemetry off` writes config; default sends `RuleHit` to `/api/telemetry`

**Week 6 — Docs + launch**
- Fumadocs site at `/docs` route
- Rule catalog page (each rule: description, bad/good examples, why it costs $)
- Quickstart, CI integration, config reference
- README with 30-second demo gif
- **Launch:** post on HN ("Show HN: Open-source linter that finds Firestore queries that will blow up your bill"), Reddit r/Firebase + r/Flutter (NOT r/javascript — wrong audience), Flutter Discord, your Twitter

Exit criteria:
- 12 rules shipping with <10% false-positive rate on 3 design-partner codebases
- npm package published, ≥50 weekly downloads
- ≥150 GitHub stars in first 2 weeks post-launch
- Telemetry pipeline working

### Milestone 2 — Cost Dashboard MVP (Weeks 7–12, ~6 weeks)

Now you have a funnel. Build the paid product.

**Week 7 — Auth + org model**
- Next.js app deployed at root domain
- Supabase Auth GitHub OAuth flow
- Org creation on first signup, membership table
- Marketing landing page (single page, hero + 3 features + pricing + CTA)

**Week 8 — Firebase project connection**
- Onboarding wizard: paste Firebase project ID, upload service account JSON
- Encrypt SA JSON at rest (libsodium sealed box, key in Fly secrets)
- Validate SA can read BigQuery + Firestore monitoring
- Show "first sync in progress" state

**Week 9 — BigQuery ingestion**
- Worker app on Fly, pg-boss schedules nightly pull per project
- Pull last 28 days of `gcp_billing_export_v1_*` rows
- Normalize into `CostSnapshot` rows, attributed by service + collection where possible
- Backfill job on project connect
- Sentry-tracked retries

**Week 10 — Dashboard charts**
- Overview: total spend last 30 days, projected next 30, breakdown by service
- Drill-down: Firestore → top collections by reads/writes
- Trend chart with confidence interval
- "Top cost-driving collections" leaderboard

**Week 11 — Projection engine**
- `cost-core` package: linear regression over 28 days, weekly seasonality flag
- Project monthly cost, surface % error vs current bill (sanity check)
- Alert thresholds: % over budget, day-over-day spike
- Email + Slack incoming webhook for alerts

**Week 12 — Stripe + paid tiers**
- Stripe Checkout, 3 products: Starter $49, Growth $149, Scale $499
- Webhook handler updates `Org.plan`
- Plan gating middleware: feature flags per tier
- Customer Portal link in settings
- 14-day free trial on Starter+

Exit criteria (**Month 3 kill/continue gate**):
- Dashboard ingests 3 design-partner Firebase projects without manual intervention
- ≥1 design partner converts to paid Starter or Growth
- ≥300 GitHub stars OR ≥5 paid signups
- If neither: re-evaluate before continuing

### Milestone 3 — Growth Tier Features (Weeks 13–18, ~6 weeks)

Make Growth tier ($149) worth it. PR bot is the killer.

**Week 13–14 — GitHub App**
- Register GitHub App `firecost-bot`
- Install flow: org admin installs on repos
- Webhook on pull_request opened/synchronized
- Run linter on changed files only, post PR comment with diagnostics
- Inline suggestions where `fix` is available

**Week 15 — Cost diff on PR**
- For PRs touching Firestore code, estimate cost delta (heuristic: new listener × baseline read rate)
- "This PR is projected to add $X/mo at current traffic"
- Tag PR with `firecost:cost-risk` label

**Week 16 — Slack integration**
- Slack OAuth, install per org
- Daily digest channel post: "Yesterday's spend, top movers, new alerts"
- Real-time alert when spike crosses threshold

**Week 17 — Multi-project + team UX**
- Switch active project in dashboard
- Team invites via email
- Per-project rule overrides

**Week 18 — Cold outreach + content**
- Write 3 case-study blog posts (anonymized bill-shock teardowns)
- Cold-email 50 startups from public bill-shock stories on Twitter/HN
- Offer free audit → upsell to Growth

Exit criteria:
- Growth tier launched, ≥3 Growth customers
- PR bot installed on ≥10 repos (paid + free)
- 1 blog post on HN front page or 1 Twitter post >1K likes

### Milestone 4 — SDK Shim (Weeks 19–26, ~8 weeks) — The Moat

This is the defensibility play. Customers install your wrapper around Firestore; you get true code-to-cost attribution.

**Week 19–20 — Shim design**
- `@firecost/firestore` — drop-in re-export of `firebase/firestore` with instrumentation
- Wrap `getDocs`, `getDoc`, `onSnapshot`, `addDoc`, `setDoc`, `updateDoc`, `deleteDoc`
- Capture: query path, op type, doc count, duration, stack frame (source-mapped client-side)
- Buffer + batch ship to `/api/sdk/events`, gzip, retry with backoff
- PII redaction: hash user IDs in paths via configurable redactor

**Week 21 — Ingestion**
- `/api/sdk/events` endpoint, rate-limit per org token
- `SdkEvent` table: project, collection path template, op, count, stackHash
- Materialize hourly rollups via pg-boss cron

**Week 22 — Attribution UI**
- New dashboard view: "Cost by source location"
- Map stackHash → first non-node_modules frame → source link (GitHub link if repo configured)
- Top 20 lines by attributed read/write cost

**Week 23 — Scale tier gating**
- SDK shim gated to Scale tier ($499)
- Org token generation + rotation in settings
- Quota: 10M events/mo Scale; overage emails

**Week 24–25 — Production hardening**
- Load test ingestion at 1K events/sec sustained
- Move event table to time-partitioned schema (monthly partitions)
- Add ClickHouse later if Postgres aggregation slows (defer until needed)

**Week 26 — Launch + content**
- Blog post: "How we attribute every Firestore read to a line of code"
- HN re-launch ("Show HN: Firecost Scale tier — code-level Firestore cost attribution")
- Demo video <2 min

Exit criteria (**Month 6 kill/continue gate**):
- ≥$1,000 MRR with ≥10 paying customers
- ≥1 Scale tier customer using SDK shim in production
- If MRR <$1K: pause new features, double down on GTM for 4 weeks

### Milestone 5 — Dart / Flutter Support (Weeks 27–34, ~8 weeks)

Your personal-fit advantage. Flutter community is high-affinity ICP.

**Week 27–28 — Dart analyzer plugin**
- Spike: dart analyzer plugin API, build hello-world rule
- Decide: plugin API vs standalone `dart run firecost`
- Recommend standalone CLI invoking analyzer programmatically (plugin API fragile)

**Week 29–31 — Port v1 rules to Dart**
- Pattern: `FirebaseFirestore.instance.collection(...).where(...).get()`
- Reuse rule definitions where possible; per-language matcher implementations
- Fixture suite mirroring TS

**Week 32 — Dart SDK shim**
- Publish `firecost_firestore` on pub.dev
- Drop-in replacement for `cloudfirestore` (or thin wrapper if API constraints)

**Week 33 — Flutter-specific content**
- Talk submission to FlutterCon
- Blog post: "Reading Firestore queries with cost glasses on (Flutter edition)"
- Demo on personal Flutter app

**Week 34 — Outreach to Flutter agencies**
- DM Flutter-heavy agencies (Very Good Ventures, Invertase, Codemate-style shops)
- Offer free audit of one of their clients' apps in exchange for testimonial

Exit criteria (**Month 9 kill/continue gate**):
- ≥$5,000 MRR → real business, scale GTM, consider 2nd hire
- $2K–$5K MRR → keep going but reassess
- <$2K MRR → archive per analysis doc §12

### Milestone 6+ — Beyond MVP (Month 10+)

Driven by data, not pre-planned. Likely candidates:
- LLM fix-suggestions and weekly cost narratives (Anthropic Claude API with prompt caching)
- Swift / Kotlin support
- Supabase / Convex / PlanetScale expansion (DB-agnostic rule engine)
- SOC2 Type I + SAML for Enterprise tier
- v2 rule packs: Storage, Cloud Functions deep, Auth abuse

---

## 5. Standing Practices (Apply Every Phase)

### Quality gates per merge
- Biome lint + format clean
- Vitest + Turborepo affected-only on PR
- Type-check across monorepo
- Changeset required for any change in `packages/` published to npm
- Sentry release tagged on deploy

### Rule authoring contract
Each new rule MUST ship with:
1. Confidence level (high/medium/low) explicitly justified in doc comment
2. ≥5 fixture cases (positive + negative + edge)
3. Markdown page in docs: description, bad example, good example, "why it costs $"
4. Severity defaulting per doc; downgradeable via config

### False-positive watch
- Telemetry RuleHit + customer disable rate per rule
- Any rule with >5% disable rate flagged for review weekly
- Move to low-confidence + off-by-default until fixed

### Security
- Service account JSON encrypted at rest (libsodium sealed box)
- Stripe webhook signature verification (no skip)
- Supabase RLS on all org-scoped tables
- No customer Firestore data ever persisted; only counts + paths
- PII redaction in SDK shim configurable + on-by-default for user-id-shaped path segments

### Pricing discipline
- Resist anchoring to indie expectations
- Annual plans only after 20+ monthly customers (need churn data first)
- Free OSS linter forever — non-negotiable per analysis doc §6

---

## 6. Immediate Next Actions (This Week)

Concrete, ordered. No yak shaving.

1. **Pick a name + secure assets**
   - Brainstorm 5 names. Check `.dev` domain, npm scope, github org, twitter handle all free for each. Pick the first that's clean across all four.
2. **Open `firebase-cost-analysis.md` design-partner outreach DMs**
   - Post in Flutter Discord, r/Firebase, personal channels: "Building a tool that catches Firestore queries that will blow up your bill. Looking for 3 design partners — 30 min call + try the alpha. DM me."
3. **Init monorepo locally**
   ```
   mkdir firecost && cd firecost
   pnpm init
   pnpm add -D turbo typescript @biomejs/biome vitest changesets
   # workspace + turbo.json
   mkdir -p packages/linter/{rules,engine,reporters,fixtures} packages/cli apps/web apps/worker
   ```
4. **Create GitHub org + push empty repo with README that already pitches the product**
   - README ships before code. It is the spec.
5. **Provision Supabase + Fly accounts**
   - Supabase: project, GitHub OAuth app, Postgres connection string
   - Fly: 2 apps (`firecost-web`, `firecost-worker`), placeholders
6. **Write the first rule end-to-end**
   - `firestore/no-unbounded-snapshot` — engine + fixture + reporter + test, all wired up
   - Proves the entire pipeline before scaling to 11 more rules

End of week 1 you should be able to run `pnpm firecost lint examples/` on a fixture project and see a single rule fire.

---

## 7. Open Risks Tracked Through Build

Carry these forward; revisit at each milestone gate.

| Risk | Trigger to react | Action |
|---|---|---|
| False-positive fatigue kills OSS adoption | Disable rate >5% on any rule | Demote to low-confidence, off by default; investigate before re-enabling |
| Google ships "Firebase Cost Lens" | Google IO announcement, console update | Pivot positioning to multi-DB (Convex, Supabase) faster; lean on SDK shim moat |
| BigQuery billing export shape changes | Schema drift detected in ingestion | Versioned adapter, snapshot tests against fixture export rows |
| Solo-dev burnout at 15–20 hrs/wk for 9 months | Missed weekly cadence 3 weeks in a row | Cut scope, defer non-revenue features, take 2 weeks off |
| Design partners don't materialize | <2 verbal commitments by week 2 | Pause Milestone 1; spend a week on outbound DMs before resuming |
| Supabase or Fly outage hits ingestion SLA | >2 outages in 30 days post-launch | Move ingestion worker to Cloud Run (closer to BQ anyway) |

---

## 8. Companion-Doc Cross-Reference

- ICP, pricing, GTM rationale → `firebase-cost-analysis.md` §§5–6, 10
- Rule severity + confidence framing → §8, Appendix A
- Kill/continue gates → §12
- Risks (master list) → §9
- Build estimate origin → §8 table

Any deviation from the analysis doc's positions should be logged here as a new section before code changes.
