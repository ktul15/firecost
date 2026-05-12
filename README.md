# firecost

Catch Firestore queries that will blow up your Firebase bill — before they ship.

> **Status:** Early development. The OSS linter (v0.1) is the first deliverable. See the roadmap below.

## What it will do

- **Linter** — static analysis for TS / JS that flags expensive Firestore patterns: unbounded `onSnapshot`, missing `.limit()`, N+1 reads, forgotten unsubscribes, self-triggering Cloud Functions, and more.
- **Cost dashboard** — connects to your Firebase project, pulls billing + usage from BigQuery, projects next-month cost, alerts on spikes.
- **Code-to-cost attribution** — runtime SDK shim (Scale tier) maps every read/write to the exact line of code that triggered it.

## Why

Firebase Console tells you the total bill. It does not tell you which 12 lines of code drove 80% of your reads. firecost does.

## Roadmap

| Milestone | Scope | Target |
|---|---|---|
| M1 | OSS TS linter, 12 rules, npm + GitHub Actions | Weeks 1–6 |
| M2 | Cost dashboard MVP + BigQuery ingestion + Stripe | Weeks 7–12 |
| M3 | GitHub PR bot + Slack alerts (Growth tier) | Weeks 13–18 |
| M4 | Runtime SDK shim — the moat (Scale tier) | Weeks 19–26 |
| M5 | Dart / Flutter support | Weeks 27–34 |

## Pricing (planned)

| Tier | Price | Who |
|---|---|---|
| OSS linter | Free | Anyone |
| Starter | $49/mo | Seed startups, 1 project |
| Growth | $149/mo | Series A, PR bot + Slack |
| Scale | $499/mo | Series B+, runtime attribution |
| Enterprise | Custom | SAML, SOC2, audit reports |

## License

MIT (linter, CLI, SDK). Dashboard application code is source-available in this repo but not licensed for redistribution.

## Contact

Pre-launch. Watching this repo is the best way to follow progress.
