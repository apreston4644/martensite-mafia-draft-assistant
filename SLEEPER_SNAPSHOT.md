# MartensiteMafia automated Sleeper snapshot

The repository's [Refresh Sleeper league snapshot](./.github/workflows/refresh-sleeper.yml)
GitHub Actions workflow reads Sleeper's **public, read-only** API and commits two
timestamped files:

- [data/league_snapshot.md](./data/league_snapshot.md): my starters, bench,
  IR/taxi, weekly opponent, league teams, top free agents and add trends.
- [data/league_snapshot.json](./data/league_snapshot.json): structured scoring
  settings, every roster, full available QB/RB/WR/TE pool, 48-hour adds/drops,
  matchup points and player IDs.

**No Sleeper login, token, or private GitHub secret is required.** No lineup
changes, trades, or waiver claims can be made through this integration.

## Schedule (America/New_York)

- Daily: 8:23 AM, 12:23 PM, 5:23 PM, 9:23 PM.
- Sundays: also every 30 minutes, 11:13 AM–11:43 PM.
- Mondays and Thursdays: also hourly, 6:43 PM–11:43 PM.

GitHub scheduled jobs can be delayed or missed. A public repository's scheduled
workflows can be disabled after 60 days without repository activity. Capture
timestamps are in UTC so they can be checked before making lineup decisions.

## Refresh manually

Go to **Actions → Refresh Sleeper league snapshot → Run workflow → main**.
Wait for the job to complete, then open the two data files. If a job fails,
select that run to see the failing step. If GitHub reports a permission failure
on the commit/push step, check **Settings → Actions → General → Workflow
permissions**; this workflow needs Contents: write permission for its token.

The action never commits a failed or incomplete Sleeper fetch. The previous
snapshot remains available if Sleeper has a temporary outage.

## Ask Otis / ChatGPT

In ChatGPT with the GitHub app connected, say:

> Read \`data/league_snapshot.json\` in
> \`apreston4644/martensite-mafia-draft-assistant\`, check its capture time
> and NFL week, then recommend my starters using current injuries and matchups.
> Compare every eligible bench player and identify my opponent's starters.

The GitHub app lets ChatGPT read the latest committed snapshot. This is a
**timestamped snapshot, not a direct live Sleeper connection**; always check
the timestamp and verify late-breaking injuries or kickoff locks separately.
For older snapshots or in case of app access trouble, open/copy the Markdown.

Sleeper API attribution: https://docs.sleeper.com/

## Configuration

The default 2026 league ID, username, and fallback roster ID are set as
environment variables in the workflow and can also be overridden when running
\`python scripts/sleeper_snapshot.py\` locally. Update the expected season in
the script when migrating to a new year's league.
