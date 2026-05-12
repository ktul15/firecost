#!/usr/bin/env python3
"""
Seed all build-plan issues into ktul15/firecost.

Idempotent: skips issues whose title already exists.
Adds each new issue to the "Firecost Roadmap" project.

Requirements:
  - gh CLI authenticated as ktul15 (gh auth switch -u ktul15)
  - Labels + milestones already created (see seed-labels.sh, seed-milestones.sh)

Usage:
  python3 scripts/seed_issues.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable

REPO = "ktul15/firecost"
PROJECT_OWNER = "ktul15"
PROJECT_TITLE = "Firecost Roadmap"

MILESTONE_TITLES = {
    "m0": "M0 — Foundations",
    "m1": "M1 — OSS Linter v0.1",
    "m2": "M2 — Cost Dashboard MVP",
    "m3": "M3 — Growth Tier + PR Bot",
    "m4": "M4 — SDK Shim (Scale tier)",
    "m5": "M5 — Dart / Flutter",
}


@dataclass(frozen=True)
class Task:
    tid: str
    milestone: str  # m0..m5
    week: str  # e.g. "wk 0", "wk 1"
    title: str
    labels: tuple[str, ...]


def L(milestone: str, *extras: str) -> tuple[str, ...]:
    return (f"milestone:{milestone}", *extras)


TASKS: list[Task] = [
    # ──────────────────────── M0 Foundations ────────────────────────
    Task("M0-01", "m0", "wk 0", "Register firecost.dev domain + Cloudflare DNS",
         L("m0", "type:infra", "size:s", "priority:p0")),
    Task("M0-02", "m0", "wk 0", "Initialize pnpm + Turborepo workspace at repo root",
         L("m0", "type:infra", "size:m", "priority:p0")),
    Task("M0-03", "m0", "wk 0", "Add packages/config: shared tsconfig, biome.json, env zod schema",
         L("m0", "type:infra", "size:m", "priority:p0")),
    Task("M0-04", "m0", "wk 0", "Add .nvmrc, .editorconfig, .npmrc, root package.json scripts",
         L("m0", "type:infra", "size:s", "priority:p0")),
    Task("M0-05", "m0", "wk 0", "Provision Supabase project + GitHub OAuth app",
         L("m0", "type:infra", "size:m", "priority:p0")),
    Task("M0-06", "m0", "wk 0", "Provision Fly orgs + 2 placeholder apps (web, worker)",
         L("m0", "type:infra", "size:m", "priority:p0")),
    Task("M0-07", "m0", "wk 0", "Create Sentry, Axiom, PostHog projects + capture DSNs",
         L("m0", "type:infra", "size:s", "priority:p1")),
    Task("M0-08", "m0", "wk 0", "Create Stripe account in test mode + initial product placeholders",
         L("m0", "type:infra", "size:s", "priority:p1")),
    Task("M0-09", "m0", "wk 0", "Add .github/ISSUE_TEMPLATE/task.yml + pull_request_template.md",
         L("m0", "type:docs", "size:s", "priority:p1")),
    Task("M0-10", "m0", "wk 0", "Add CI workflow (lint + typecheck + test placeholder)",
         L("m0", "type:infra", "size:m", "priority:p0")),
    Task("M0-11", "m0", "wk 0", "Source 3 design partners — DM Flutter Discord, r/Firebase, personal Twitter",
         L("m0", "type:gtm", "size:m", "priority:p0")),

    # ──────────────────────── M1 OSS Linter ────────────────────────
    # Week 1 — Engine + harness
    Task("M1-01", "m1", "wk 1", "Scaffold packages/linter + packages/cli skeletons",
         L("m1", "type:infra", "tier:oss", "size:m", "priority:p0")),
    Task("M1-02", "m1", "wk 1", "Engine: ts-morph project loader (engine/project.ts)",
         L("m1", "type:feature", "tier:oss", "size:m", "priority:p0")),
    Task("M1-03", "m1", "wk 1", "Engine: rule runner iterating registered rules over files",
         L("m1", "type:feature", "tier:oss", "size:m", "priority:p0")),
    Task("M1-04", "m1", "wk 1", "Engine: diagnostic shape + types (engine/diagnostic.ts, types.ts)",
         L("m1", "type:feature", "tier:oss", "size:s", "priority:p0")),
    Task("M1-05", "m1", "wk 1", "Engine: inline suppression parser (// firecost-disable-next-line)",
         L("m1", "type:feature", "tier:oss", "size:m", "priority:p1")),
    Task("M1-06", "m1", "wk 1", "Engine: confidence-level tagging on diagnostics",
         L("m1", "type:feature", "tier:oss", "size:s", "priority:p1")),
    Task("M1-07", "m1", "wk 1", "Vitest fixture harness auto-loading fixtures/<rule-id>/{bad,good}-*.ts",
         L("m1", "type:infra", "tier:oss", "size:m", "priority:p0")),
    Task("M1-08", "m1", "wk 1", "Reporter: pretty CLI terminal output (picocolors)",
         L("m1", "type:feature", "tier:oss", "size:m", "priority:p0")),

    # Week 2 — Rules 1-4 (high confidence)
    Task("M1-09", "m1", "wk 2", "Rule: firestore/no-unbounded-snapshot + fixtures + docs",
         L("m1", "type:rule", "tier:oss", "size:m", "priority:p0")),
    Task("M1-10", "m1", "wk 2", "Rule: firestore/no-unbounded-get + fixtures + docs",
         L("m1", "type:rule", "tier:oss", "size:m", "priority:p0")),
    Task("M1-11", "m1", "wk 2", "Rule: firestore/cleanup-listener + fixtures + docs",
         L("m1", "type:rule", "tier:oss", "size:m", "priority:p0")),
    Task("M1-12", "m1", "wk 2", "Rule: firestore/no-empty-where + fixtures + docs",
         L("m1", "type:rule", "tier:oss", "size:m", "priority:p0")),

    # Week 3 — Rules 5-8
    Task("M1-13", "m1", "wk 3", "Rule: firestore/no-loop-read + fixtures + docs",
         L("m1", "type:rule", "tier:oss", "size:m", "priority:p0")),
    Task("M1-14", "m1", "wk 3", "Rule: firestore/no-large-batch-get + fixtures + docs",
         L("m1", "type:rule", "tier:oss", "size:m", "priority:p1")),
    Task("M1-15", "m1", "wk 3", "Rule: firestore/limit-or-pagination + fixtures + docs",
         L("m1", "type:rule", "tier:oss", "size:m", "priority:p1")),
    Task("M1-16", "m1", "wk 3", "Rule: functions/no-trigger-self-write + fixtures + docs",
         L("m1", "type:rule", "tier:oss", "size:m", "priority:p0")),

    # Week 4 — Rules 9-12 + config
    Task("M1-17", "m1", "wk 4", "Rule: firestore/no-redundant-listener + fixtures + docs",
         L("m1", "type:rule", "tier:oss", "size:m", "priority:p1")),
    Task("M1-18", "m1", "wk 4", "Rule: firestore/prefer-collection-group-with-index + fixtures + docs",
         L("m1", "type:rule", "tier:oss", "size:m", "priority:p2")),
    Task("M1-19", "m1", "wk 4", "Rule: firestore/index-write-amplification + fixtures + docs",
         L("m1", "type:rule", "tier:oss", "size:m", "priority:p1")),
    Task("M1-20", "m1", "wk 4", "Rule: firestore/no-debug-listener-in-prod + fixtures + docs",
         L("m1", "type:rule", "tier:oss", "size:m", "priority:p2")),
    Task("M1-21", "m1", "wk 4", "Cosmiconfig loader for firecost.config.{ts,js,json}",
         L("m1", "type:feature", "tier:oss", "size:m", "priority:p0")),
    Task("M1-22", "m1", "wk 4", "Config schema: rule enable/disable + severity overrides (zod)",
         L("m1", "type:feature", "tier:oss", "size:m", "priority:p0")),

    # Week 5 — CLI + reporters
    Task("M1-23", "m1", "wk 5", "CLI: commander bootstrap + bin/firecost shebang",
         L("m1", "type:feature", "tier:oss", "size:s", "priority:p0")),
    Task("M1-24", "m1", "wk 5", "CLI command: lint (run engine, format with chosen reporter)",
         L("m1", "type:feature", "tier:oss", "size:m", "priority:p0")),
    Task("M1-25", "m1", "wk 5", "CLI command: init (scaffold firecost.config.ts)",
         L("m1", "type:feature", "tier:oss", "size:s", "priority:p1")),
    Task("M1-26", "m1", "wk 5", "CLI command: rules (list all rules with meta)",
         L("m1", "type:feature", "tier:oss", "size:s", "priority:p1")),
    Task("M1-27", "m1", "wk 5", "CLI command: telemetry on/off/status",
         L("m1", "type:feature", "tier:oss", "size:s", "priority:p1")),
    Task("M1-28", "m1", "wk 5", "Reporter: JSON output",
         L("m1", "type:feature", "tier:oss", "size:s", "priority:p1")),
    Task("M1-29", "m1", "wk 5", "Reporter: GitHub Actions annotations",
         L("m1", "type:feature", "tier:oss", "size:s", "priority:p0")),
    Task("M1-30", "m1", "wk 5", "Reporter: SARIF (for GitHub code-scanning UI)",
         L("m1", "type:feature", "tier:oss", "size:m", "priority:p2")),
    Task("M1-31", "m1", "wk 5", "Telemetry client: hashed anon id + opt-out config",
         L("m1", "type:feature", "tier:oss", "size:m", "priority:p1")),
    Task("M1-32", "m1", "wk 5", "Example GitHub Actions workflow in repo (examples/ci/)",
         L("m1", "type:docs", "tier:oss", "size:s", "priority:p1")),

    # Week 6 — Docs + npm + launch
    Task("M1-33", "m1", "wk 6", "Fumadocs setup in apps/web",
         L("m1", "type:docs", "tier:oss", "size:m", "priority:p0")),
    Task("M1-34", "m1", "wk 6", "Auto-generate rule catalog doc page from meta.ts",
         L("m1", "type:docs", "tier:oss", "size:m", "priority:p0")),
    Task("M1-35", "m1", "wk 6", "Docs: Quickstart",
         L("m1", "type:docs", "tier:oss", "size:s", "priority:p0")),
    Task("M1-36", "m1", "wk 6", "Docs: CI integration guide",
         L("m1", "type:docs", "tier:oss", "size:s", "priority:p0")),
    Task("M1-37", "m1", "wk 6", "Docs: Config reference",
         L("m1", "type:docs", "tier:oss", "size:s", "priority:p1")),
    Task("M1-38", "m1", "wk 6", "Polish README + record asciicast demo",
         L("m1", "type:docs", "tier:oss", "size:m", "priority:p0")),
    Task("M1-39", "m1", "wk 6", "Add .changeset/config.json + first changeset",
         L("m1", "type:infra", "tier:oss", "size:s", "priority:p0")),
    Task("M1-40", "m1", "wk 6", "CI workflow: Changesets-driven npm publish on main",
         L("m1", "type:infra", "tier:oss", "size:m", "priority:p0")),
    Task("M1-41", "m1", "wk 6", "Telemetry endpoint in apps/web/src/app/api/telemetry/route.ts",
         L("m1", "type:feature", "tier:oss", "size:m", "priority:p1")),
    Task("M1-42", "m1", "wk 6", "Launch — HN Show post + Reddit r/Firebase + r/Flutter + Flutter Discord + Twitter thread",
         L("m1", "type:gtm", "tier:oss", "size:m", "priority:p0")),

    # ──────────────────────── M2 Cost Dashboard MVP ────────────────────────
    # Week 7 — Auth + org
    Task("M2-01", "m2", "wk 7", "Scaffold Next.js 15 app in apps/web with App Router",
         L("m2", "type:infra", "tier:starter", "size:m", "priority:p0")),
    Task("M2-02", "m2", "wk 7", "Supabase server client helpers (lib/auth.ts)",
         L("m2", "type:feature", "tier:starter", "size:m", "priority:p0")),
    Task("M2-03", "m2", "wk 7", "Auth pages: login + GitHub OAuth callback",
         L("m2", "type:feature", "tier:starter", "size:m", "priority:p0")),
    Task("M2-04", "m2", "wk 7", "Prisma schema: Org, User, Membership, Project + first migration",
         L("m2", "type:infra", "tier:starter", "size:m", "priority:p0")),
    Task("M2-05", "m2", "wk 7", "Org creation flow on first signup + slug picker",
         L("m2", "type:feature", "tier:starter", "size:m", "priority:p0")),
    Task("M2-06", "m2", "wk 7", "RLS policies on multi-tenant tables (Org/Project/Membership)",
         L("m2", "type:infra", "tier:starter", "size:m", "priority:p0")),
    Task("M2-07", "m2", "wk 7", "Marketing landing page (hero + 3 features + pricing teaser)",
         L("m2", "type:feature", "tier:oss", "size:m", "priority:p1")),

    # Week 8 — Firebase connection
    Task("M2-08", "m2", "wk 8", "Onboarding wizard skeleton ((app)/onboarding)",
         L("m2", "type:feature", "tier:starter", "size:m", "priority:p0")),
    Task("M2-09", "m2", "wk 8", "Service account JSON upload + libsodium sealed-box encryption at rest",
         L("m2", "type:feature", "tier:starter", "size:m", "priority:p0")),
    Task("M2-10", "m2", "wk 8", "Validate SA can read BigQuery + Firestore monitoring (dry-run probe)",
         L("m2", "type:feature", "tier:starter", "size:m", "priority:p0")),
    Task("M2-11", "m2", "wk 8", "Project entity create + first-sync pending state UI",
         L("m2", "type:feature", "tier:starter", "size:m", "priority:p0")),

    # Week 9 — BQ ingestion
    Task("M2-12", "m2", "wk 9", "Scaffold apps/worker (Fastify + pg-boss bootstrap)",
         L("m2", "type:infra", "tier:starter", "size:m", "priority:p0")),
    Task("M2-13", "m2", "wk 9", "Scaffold packages/bq-ingest + @google-cloud/bigquery client wrapper",
         L("m2", "type:feature", "tier:starter", "size:m", "priority:p0")),
    Task("M2-14", "m2", "wk 9", "BQ query: daily cost by service",
         L("m2", "type:feature", "tier:starter", "size:m", "priority:p0")),
    Task("M2-15", "m2", "wk 9", "BQ query: collection-level attribution",
         L("m2", "type:feature", "tier:starter", "size:m", "priority:p1")),
    Task("M2-16", "m2", "wk 9", "Normalize raw BQ rows → CostSnapshot Prisma writes",
         L("m2", "type:feature", "tier:starter", "size:m", "priority:p0")),
    Task("M2-17", "m2", "wk 9", "Backfill job: 28-day pull on project connect",
         L("m2", "type:feature", "tier:starter", "size:m", "priority:p0")),
    Task("M2-18", "m2", "wk 9", "Nightly pg-boss schedule + retry policy",
         L("m2", "type:infra", "tier:starter", "size:m", "priority:p0")),
    Task("M2-19", "m2", "wk 9", "Sentry breadcrumb + error capture in ingestion path",
         L("m2", "type:infra", "tier:starter", "size:s", "priority:p1")),

    # Week 10 — Charts
    Task("M2-20", "m2", "wk 10", "Overview page: total spend last 30d + projected 30d",
         L("m2", "type:feature", "tier:starter", "size:m", "priority:p0")),
    Task("M2-21", "m2", "wk 10", "Recharts trend chart with confidence interval band",
         L("m2", "type:feature", "tier:starter", "size:m", "priority:p0")),
    Task("M2-22", "m2", "wk 10", "Firestore drill-down page: top collections by reads/writes",
         L("m2", "type:feature", "tier:starter", "size:m", "priority:p0")),
    Task("M2-23", "m2", "wk 10", "Top cost-driving collections leaderboard component",
         L("m2", "type:feature", "tier:starter", "size:m", "priority:p1")),
    Task("M2-24", "m2", "wk 10", "Date range selector + service filters",
         L("m2", "type:feature", "tier:starter", "size:m", "priority:p1")),

    # Week 11 — Projection + alerts
    Task("M2-25", "m2", "wk 11", "packages/cost-core: linear regression projection",
         L("m2", "type:feature", "tier:starter", "size:m", "priority:p0")),
    Task("M2-26", "m2", "wk 11", "Cost-core: weekly seasonality flag",
         L("m2", "type:feature", "tier:starter", "size:m", "priority:p1")),
    Task("M2-27", "m2", "wk 11", "Alert thresholds config UI (% over budget)",
         L("m2", "type:feature", "tier:starter", "size:m", "priority:p1")),
    Task("M2-28", "m2", "wk 11", "Day-over-day spike detector + alert",
         L("m2", "type:feature", "tier:starter", "size:m", "priority:p0")),
    Task("M2-29", "m2", "wk 11", "Email alert delivery (Resend)",
         L("m2", "type:feature", "tier:starter", "size:m", "priority:p0")),
    Task("M2-30", "m2", "wk 11", "Slack incoming-webhook alert delivery",
         L("m2", "type:feature", "tier:starter", "size:s", "priority:p1")),

    # Week 12 — Stripe
    Task("M2-31", "m2", "wk 12", "Stripe Checkout integration + Pricing IDs",
         L("m2", "type:feature", "tier:starter", "size:m", "priority:p0")),
    Task("M2-32", "m2", "wk 12", "Stripe webhook handler updates Org.plan",
         L("m2", "type:feature", "tier:starter", "size:m", "priority:p0")),
    Task("M2-33", "m2", "wk 12", "Plan-gating middleware (lib/plan-gate.ts)",
         L("m2", "type:feature", "tier:starter", "size:m", "priority:p0")),
    Task("M2-34", "m2", "wk 12", "Customer Portal link in settings + 14-day trial logic",
         L("m2", "type:feature", "tier:starter", "size:m", "priority:p0")),

    # ──────────────────────── M3 Growth Tier + PR Bot ────────────────────────
    # Weeks 13-14 — GitHub App
    Task("M3-01", "m3", "wk 13", "Register firecost-bot GitHub App + manifest commit",
         L("m3", "type:infra", "tier:growth", "size:m", "priority:p0")),
    Task("M3-02", "m3", "wk 13", "Install flow + per-org repo selection in dashboard",
         L("m3", "type:feature", "tier:growth", "size:m", "priority:p0")),
    Task("M3-03", "m3", "wk 13", "Webhook handler: pull_request opened + synchronize",
         L("m3", "type:feature", "tier:growth", "size:m", "priority:p0")),
    Task("M3-04", "m3", "wk 14", "PR diff parser + changed-files filter",
         L("m3", "type:feature", "tier:growth", "size:m", "priority:p0")),
    Task("M3-05", "m3", "wk 14", "Worker job: run linter on changed files only",
         L("m3", "type:feature", "tier:growth", "size:m", "priority:p0")),
    Task("M3-06", "m3", "wk 14", "Post PR review comments with diagnostics",
         L("m3", "type:feature", "tier:growth", "size:m", "priority:p0")),
    Task("M3-07", "m3", "wk 14", "Inline GitHub Suggestions when rule has fix",
         L("m3", "type:feature", "tier:growth", "size:m", "priority:p1")),

    # Week 15 — Cost diff
    Task("M3-08", "m3", "wk 15", "Cost-impact heuristic (new listener × baseline read rate)",
         L("m3", "type:feature", "tier:growth", "size:m", "priority:p0")),
    Task("M3-09", "m3", "wk 15", "PR comment surface: projected $/mo delta",
         L("m3", "type:feature", "tier:growth", "size:m", "priority:p0")),
    Task("M3-10", "m3", "wk 15", "firecost:cost-risk PR label automation",
         L("m3", "type:feature", "tier:growth", "size:s", "priority:p1")),

    # Week 16 — Slack
    Task("M3-11", "m3", "wk 16", "Slack OAuth + install per org",
         L("m3", "type:feature", "tier:growth", "size:m", "priority:p0")),
    Task("M3-12", "m3", "wk 16", "Daily digest channel post job",
         L("m3", "type:feature", "tier:growth", "size:m", "priority:p0")),
    Task("M3-13", "m3", "wk 16", "Real-time spike alert post to Slack",
         L("m3", "type:feature", "tier:growth", "size:m", "priority:p1")),

    # Week 17 — Multi-project + teams
    Task("M3-14", "m3", "wk 17", "Project switcher in dashboard nav",
         L("m3", "type:feature", "tier:growth", "size:m", "priority:p0")),
    Task("M3-15", "m3", "wk 17", "Team invite by email + role assignment",
         L("m3", "type:feature", "tier:growth", "size:m", "priority:p0")),
    Task("M3-16", "m3", "wk 17", "Per-project rule enable/disable overrides",
         L("m3", "type:feature", "tier:growth", "size:m", "priority:p1")),

    # Week 18 — Content + outreach
    Task("M3-17", "m3", "wk 18", "Case-study blog post 1 (anonymized bill-shock teardown)",
         L("m3", "type:gtm", "size:m", "priority:p0")),
    Task("M3-18", "m3", "wk 18", "Case-study blog post 2",
         L("m3", "type:gtm", "size:m", "priority:p1")),
    Task("M3-19", "m3", "wk 18", "Case-study blog post 3",
         L("m3", "type:gtm", "size:m", "priority:p1")),
    Task("M3-20", "m3", "wk 18", "Cold-outreach 50 startups — list build + template + send",
         L("m3", "type:gtm", "size:m", "priority:p0")),

    # ──────────────────────── M4 SDK Shim / Scale ────────────────────────
    # Weeks 19-20 — Shim wrappers
    Task("M4-01", "m4", "wk 19", "Scaffold packages/sdk (@firecost/firestore) re-exporting firebase/firestore shape",
         L("m4", "type:infra", "tier:scale", "size:m", "priority:p0")),
    Task("M4-02", "m4", "wk 19", "Wrap getDocs with instrumentation",
         L("m4", "type:feature", "tier:scale", "size:m", "priority:p0")),
    Task("M4-03", "m4", "wk 19", "Wrap getDoc",
         L("m4", "type:feature", "tier:scale", "size:s", "priority:p0")),
    Task("M4-04", "m4", "wk 19", "Wrap onSnapshot with subscription tracking",
         L("m4", "type:feature", "tier:scale", "size:m", "priority:p0")),
    Task("M4-05", "m4", "wk 19", "Wrap addDoc / setDoc / updateDoc / deleteDoc",
         L("m4", "type:feature", "tier:scale", "size:m", "priority:p0")),
    Task("M4-06", "m4", "wk 20", "Source-mapped stack frame capture (browser source maps)",
         L("m4", "type:feature", "tier:scale", "size:l", "priority:p0")),
    Task("M4-07", "m4", "wk 20", "PII redaction with configurable redactor",
         L("m4", "type:feature", "tier:scale", "size:m", "priority:p0")),
    Task("M4-08", "m4", "wk 20", "Transport: in-memory buffer + batch flush",
         L("m4", "type:feature", "tier:scale", "size:m", "priority:p0")),
    Task("M4-09", "m4", "wk 20", "Transport: gzip + retry with exponential backoff",
         L("m4", "type:feature", "tier:scale", "size:m", "priority:p0")),

    # Week 21 — Ingestion
    Task("M4-10", "m4", "wk 21", "/api/sdk/events endpoint with token auth",
         L("m4", "type:feature", "tier:scale", "size:m", "priority:p0")),
    Task("M4-11", "m4", "wk 21", "Per-org token rate limiting",
         L("m4", "type:feature", "tier:scale", "size:m", "priority:p0")),
    Task("M4-12", "m4", "wk 21", "Prisma model SdkEvent + migration (time-partitioned ready)",
         L("m4", "type:infra", "tier:scale", "size:m", "priority:p0")),
    Task("M4-13", "m4", "wk 21", "Hourly rollup pg-boss cron → aggregates by stackHash + collection",
         L("m4", "type:feature", "tier:scale", "size:m", "priority:p0")),

    # Week 22 — Attribution UI
    Task("M4-14", "m4", "wk 22", "Dashboard view: Cost by source location",
         L("m4", "type:feature", "tier:scale", "size:m", "priority:p0")),
    Task("M4-15", "m4", "wk 22", "stackHash → first non-node_modules frame mapping + GitHub link",
         L("m4", "type:feature", "tier:scale", "size:m", "priority:p0")),
    Task("M4-16", "m4", "wk 22", "Top-20 lines by attributed cost table",
         L("m4", "type:feature", "tier:scale", "size:m", "priority:p0")),

    # Week 23 — Scale tier gating
    Task("M4-17", "m4", "wk 23", "Scale tier feature gate in plan-gate.ts",
         L("m4", "type:feature", "tier:scale", "size:s", "priority:p0")),
    Task("M4-18", "m4", "wk 23", "Org token generation + rotation UI in settings",
         L("m4", "type:feature", "tier:scale", "size:m", "priority:p0")),
    Task("M4-19", "m4", "wk 23", "Quota tracking (10M events/mo) + overage email",
         L("m4", "type:feature", "tier:scale", "size:m", "priority:p0")),

    # Weeks 24-25 — Hardening
    Task("M4-20", "m4", "wk 24", "Load test ingestion at 1k events/sec sustained",
         L("m4", "type:infra", "tier:scale", "size:l", "priority:p0")),
    Task("M4-21", "m4", "wk 25", "Migrate SdkEvent to monthly time-partitioned schema",
         L("m4", "type:infra", "tier:scale", "size:l", "priority:p1")),

    # Week 26 — Launch
    Task("M4-22", "m4", "wk 26", "Blog post: How we attribute every Firestore read to a line of code",
         L("m4", "type:gtm", "size:m", "priority:p0")),
    Task("M4-23", "m4", "wk 26", "Demo video <2 min showing attribution UI",
         L("m4", "type:gtm", "size:m", "priority:p0")),
    Task("M4-24", "m4", "wk 26", "HN Show post for Scale tier launch",
         L("m4", "type:gtm", "size:s", "priority:p0")),

    # ──────────────────────── M5 Dart / Flutter ────────────────────────
    # Weeks 27-28 — Analyzer
    Task("M5-01", "m5", "wk 27", "Spike: dart analyzer plugin API vs standalone CLI invocation — write ADR",
         L("m5", "type:docs", "tier:oss", "size:l", "priority:p0")),
    Task("M5-02", "m5", "wk 28", "CLI: firecost dart subcommand wiring",
         L("m5", "type:feature", "tier:oss", "size:m", "priority:p0")),
    Task("M5-03", "m5", "wk 28", "Dart fixture harness mirroring TS structure",
         L("m5", "type:infra", "tier:oss", "size:m", "priority:p0")),

    # Weeks 29-31 — Port 12 rules to Dart
    Task("M5-04", "m5", "wk 29", "Port rule: firestore/no-unbounded-snapshot (Dart)",
         L("m5", "type:rule", "tier:oss", "size:m", "priority:p0")),
    Task("M5-05", "m5", "wk 29", "Port rule: firestore/no-unbounded-get (Dart)",
         L("m5", "type:rule", "tier:oss", "size:m", "priority:p0")),
    Task("M5-06", "m5", "wk 29", "Port rule: firestore/cleanup-listener (Dart)",
         L("m5", "type:rule", "tier:oss", "size:m", "priority:p0")),
    Task("M5-07", "m5", "wk 29", "Port rule: firestore/no-empty-where (Dart)",
         L("m5", "type:rule", "tier:oss", "size:m", "priority:p0")),
    Task("M5-08", "m5", "wk 30", "Port rule: firestore/no-loop-read (Dart)",
         L("m5", "type:rule", "tier:oss", "size:m", "priority:p1")),
    Task("M5-09", "m5", "wk 30", "Port rule: firestore/no-large-batch-get (Dart)",
         L("m5", "type:rule", "tier:oss", "size:m", "priority:p1")),
    Task("M5-10", "m5", "wk 30", "Port rule: firestore/limit-or-pagination (Dart)",
         L("m5", "type:rule", "tier:oss", "size:m", "priority:p1")),
    Task("M5-11", "m5", "wk 30", "Port rule: functions/no-trigger-self-write (Dart)",
         L("m5", "type:rule", "tier:oss", "size:m", "priority:p1")),
    Task("M5-12", "m5", "wk 31", "Port rule: firestore/no-redundant-listener (Dart)",
         L("m5", "type:rule", "tier:oss", "size:m", "priority:p2")),
    Task("M5-13", "m5", "wk 31", "Port rule: firestore/prefer-collection-group-with-index (Dart)",
         L("m5", "type:rule", "tier:oss", "size:m", "priority:p2")),
    Task("M5-14", "m5", "wk 31", "Port rule: firestore/index-write-amplification (Dart)",
         L("m5", "type:rule", "tier:oss", "size:m", "priority:p2")),
    Task("M5-15", "m5", "wk 31", "Port rule: firestore/no-debug-listener-in-prod (Dart)",
         L("m5", "type:rule", "tier:oss", "size:m", "priority:p2")),

    # Week 32 — Dart SDK shim
    Task("M5-16", "m5", "wk 32", "Publish firecost_firestore package on pub.dev",
         L("m5", "type:feature", "tier:scale", "size:l", "priority:p0")),
    Task("M5-17", "m5", "wk 32", "Drop-in wrapper around cloud_firestore with parity to TS shim",
         L("m5", "type:feature", "tier:scale", "size:l", "priority:p0")),

    # Weeks 33-34 — Content + outreach
    Task("M5-18", "m5", "wk 33", "FlutterCon talk submission (CFP draft + abstract)",
         L("m5", "type:gtm", "size:m", "priority:p0")),
    Task("M5-19", "m5", "wk 33", "Flutter blog post: Firestore queries with cost glasses on (Flutter edition)",
         L("m5", "type:gtm", "size:m", "priority:p0")),
    Task("M5-20", "m5", "wk 34", "Build outreach list: 10 Flutter-heavy agencies + template",
         L("m5", "type:gtm", "size:m", "priority:p0")),
    Task("M5-21", "m5", "wk 34", "Free audit offer DM to 5 Flutter agencies in exchange for testimonial",
         L("m5", "type:gtm", "size:m", "priority:p1")),
]


def sh(args: list[str], check: bool = True, capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=check, capture_output=capture, text=True)


def fetch_existing_titles() -> set[str]:
    """Pull all existing issue titles in the repo (open + closed) for idempotency check."""
    print(f"Loading existing issues from {REPO}...")
    result = sh([
        "gh", "issue", "list",
        "--repo", REPO,
        "--state", "all",
        "--limit", "500",
        "--json", "title",
    ])
    rows = json.loads(result.stdout)
    titles = {r["title"] for r in rows}
    print(f"  Found {len(titles)} existing issues.")
    return titles


def fetch_project_number() -> int:
    result = sh([
        "gh", "project", "list",
        "--owner", PROJECT_OWNER,
        "--format", "json",
    ])
    data = json.loads(result.stdout)
    for p in data["projects"]:
        if p["title"] == PROJECT_TITLE:
            return int(p["number"])
    raise SystemExit(f"Project '{PROJECT_TITLE}' not found under {PROJECT_OWNER}")


def build_body(task: Task) -> str:
    return (
        f"**Milestone:** {MILESTONE_TITLES[task.milestone]}\n"
        f"**Build plan reference:** see `BUILD_PLAN.md` §4 → {task.milestone.upper()} ({task.week})\n"
        f"**Task ID:** `{task.tid}`\n\n"
        f"## Outcome\n"
        f"{task.title}.\n\n"
        f"## Definition of Done\n"
        f"- [ ] Implementation complete\n"
        f"- [ ] Tests / fixtures added where applicable\n"
        f"- [ ] Docs updated where applicable\n"
        f"- [ ] PR merged to main\n"
    )


def create_issue(task: Task, project_number: int, dry_run: bool) -> str | None:
    issue_title = f"[{task.tid}] {task.title}"
    cmd = [
        "gh", "issue", "create",
        "--repo", REPO,
        "--title", issue_title,
        "--milestone", MILESTONE_TITLES[task.milestone],
        "--body", build_body(task),
    ]
    for lbl in task.labels:
        cmd += ["--label", lbl]

    if dry_run:
        print(f"  [dry-run] would create: {issue_title}")
        return None

    result = sh(cmd, check=False)
    if result.returncode != 0:
        print(f"  ✗ FAILED to create {task.tid}: {result.stderr.strip()}", file=sys.stderr)
        return None

    url = result.stdout.strip()
    # Add to project
    add = sh(
        ["gh", "project", "item-add", str(project_number),
         "--owner", PROJECT_OWNER, "--url", url],
        check=False,
    )
    if add.returncode != 0:
        print(f"  ! created but failed to add to project: {task.tid} — {add.stderr.strip()}", file=sys.stderr)
    return url


def main(argv: Iterable[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print actions without creating issues")
    args = parser.parse_args(list(argv))

    project_number = fetch_project_number()
    print(f"Target project #{project_number} ({PROJECT_TITLE})")

    existing = fetch_existing_titles()

    created = 0
    skipped = 0
    failed = 0

    for i, task in enumerate(TASKS, start=1):
        issue_title = f"[{task.tid}] {task.title}"
        if issue_title in existing:
            print(f"  [{i:3d}/{len(TASKS)}] · skip (exists): {task.tid}")
            skipped += 1
            continue

        print(f"  [{i:3d}/{len(TASKS)}] + creating {task.tid} ...")
        url = create_issue(task, project_number, dry_run=args.dry_run)
        if args.dry_run:
            continue
        if url:
            print(f"            → {url}")
            created += 1
        else:
            failed += 1

    print("")
    print(f"Done. created={created} skipped={skipped} failed={failed} total={len(TASKS)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
