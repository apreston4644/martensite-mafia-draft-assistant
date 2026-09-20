#!/usr/bin/env python3
"""Read-only Sleeper league snapshot for the MartensiteMafia GitHub repository.

Uses only Python's standard library. Never modifies a Sleeper lineup.
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

API = "https://api.sleeper.app/v1"
LEAGUE_ID = os.environ.get("SLEEPER_LEAGUE_ID", "1313649591102500864")
USERNAME = os.environ.get("SLEEPER_USERNAME", "MartensiteMafia")
FALLBACK_ROSTER_ID = int(os.environ.get("SLEEPER_ROSTER_ID", "5"))
OUT = Path("data")
SKILL = {"QB", "RB", "WR", "TE"}
DETAIL_KEYS = ("player_id", "full_name", "first_name", "last_name", "position",
               "team", "status", "injury_status", "search_rank", "depth_chart_order",
               "fantasy_positions", "active", "bye_week")


def get(path):
    req = Request(API + path, headers={"User-Agent": "martensite-mafia-readonly/1.0",
                                      "Accept": "application/json"})
    for attempt in range(4):
        try:
            with urlopen(req, timeout=35) as response:
                return json.load(response)
        except (HTTPError, URLError, TimeoutError) as exc:
            if attempt == 3 or (isinstance(exc, HTTPError) and exc.code not in
                                (429, 500, 502, 503, 504)):
                raise RuntimeError("Sleeper request failed: " + path) from exc
            time.sleep(2 ** attempt)
    raise RuntimeError("Sleeper request failed: " + path)


def compact(raw, player_id):
    raw = raw or {}
    item = {key: raw.get(key) for key in DETAIL_KEYS if raw.get(key) is not None}
    item["player_id"] = str(player_id)
    item["name"] = (raw.get("full_name") or
                    " ".join(str(raw.get(k) or "") for k in ("first_name", "last_name")).strip()
                    or str(player_id))
    return item


def main():
    if not LEAGUE_ID.isdigit():
        raise ValueError("League ID must be numeric")
    league = get("/league/" + LEAGUE_ID)
    if not league or str(league.get("league_id")) != LEAGUE_ID:
        raise ValueError("Sleeper did not return the requested league")
    if str(league.get("season")) != "2026":
        raise ValueError("Refusing to overwrite the 2026 snapshot with another season")
    users = get("/league/" + LEAGUE_ID + "/users") or []
    rosters = get("/league/" + LEAGUE_ID + "/rosters") or []
    state = get("/state/nfl") or {}
    week = int(state.get("week") or 1)
    if not 1 <= week <= 22:
        raise ValueError("Unexpected NFL week: " + str(week))
    matchups = get("/league/" + LEAGUE_ID + "/matchups/" + str(week)) or []
    trends_add = get("/players/nfl/trending/add?lookback_hours=48&limit=100") or []
    trends_drop = get("/players/nfl/trending/drop?lookback_hours=48&limit=100") or []
    players = get("/players/nfl") or {}
    if not users or not rosters or not players:
        raise ValueError("Sleeper returned incomplete league data; preserving prior snapshot")

    identity = None
    try:
        identity = get("/user/" + quote(USERNAME, safe=""))
    except RuntimeError:
        pass
    match = next((u for u in users if identity and
                  str(u.get("user_id")) == str(identity.get("user_id"))), None)
    if match is None:
        match = next((u for u in users if USERNAME.casefold() in
                      (str(u.get("username") or "").casefold(),
                       str(u.get("display_name") or "").casefold())), None)
    mine = next((r for r in rosters if match and
                 str(r.get("owner_id")) == str(match.get("user_id"))), None)
    matched_by = "username"
    if mine is None:
        mine = next((r for r in rosters if r.get("roster_id") == FALLBACK_ROSTER_ID), None)
        matched_by = "fallback_roster_id"
    if mine is None:
        raise ValueError("Could not identify MartensiteMafia's Sleeper roster")

    roster_positions = league.get("roster_positions") or []
    by_matchup = {str(m.get("roster_id")): m for m in matchups}
    owners = {str(u.get("user_id")): u for u in users}
    taken = {str(pid) for roster in rosters for pid in
             (roster.get("players") or []) + (roster.get("reserve") or []) +
             (roster.get("taxi") or [])}
    my_roster_id = str(mine["roster_id"])

    def roster_details(roster):
        roster_id = str(roster["roster_id"])
        owner = owners.get(str(roster.get("owner_id")), {})
        matchup = by_matchup.get(roster_id, {})
        starter_ids = [str(i) for i in
                       (matchup.get("starters") or roster.get("starters") or [])]
        owned_ids = [str(i) for i in roster.get("players") or []]
        reserve_ids = [str(i) for i in roster.get("reserve") or []]
        taxi_ids = [str(i) for i in roster.get("taxi") or []]
        started = set(starter_ids)
        reserved = set(reserve_ids + taxi_ids)
        starter_slots = [{"slot": roster_positions[i] if i < len(roster_positions)
                          else "STARTER_" + str(i + 1),
                          "player": compact(players.get(pid), pid) if pid not in ("0", "", "None")
                          else None}
                         for i, pid in enumerate(starter_ids)]
        return {
            "roster_id": roster["roster_id"],
            "team_name": owner.get("metadata", {}).get("team_name") or
                         owner.get("display_name") or owner.get("username") or roster_id,
            "username": owner.get("username"),
            "matchup_id": matchup.get("matchup_id"),
            "points_so_far": matchup.get("points"),
            "starters": starter_slots,
            "bench": [compact(players.get(pid), pid) for pid in owned_ids
                      if pid not in started and pid not in reserved],
            "reserve": [compact(players.get(pid), pid) for pid in reserve_ids],
            "taxi": [compact(players.get(pid), pid) for pid in taxi_ids],
            "player_ids": owned_ids,
            "settings": roster.get("settings") or {},
        }

    teams = [roster_details(r) for r in rosters]
    me = next(t for t in teams if str(t["roster_id"]) == my_roster_id)
    opponent = next((t for t in teams if t["roster_id"] != me["roster_id"]
                     and t["matchup_id"] is not None
                     and t["matchup_id"] == me["matchup_id"]), None)
    available = [compact(p, pid) for pid, p in players.items()
                 if str(pid) not in taken and
                 (p or {}).get("position") in SKILL and
                 (p or {}).get("active", True) is not False]
    available.sort(key=lambda p: (p.get("search_rank") is None,
                   p.get("search_rank") or 999999, p["name"]))

    def trend(items):
        return [{"count": entry.get("count", 0),
                 "available": str(entry["player_id"]) not in taken,
                 "player": compact(players.get(str(entry["player_id"])),
                                   str(entry["player_id"]))}
                for entry in items if entry.get("player_id") is not None]

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    snapshot = {
        "schema_version": 1,
        "source": "Sleeper public read-only API",
        "updated_at_utc": now,
        "league": {"league_id": LEAGUE_ID, "name": league.get("name"),
                   "season": league.get("season"), "status": league.get("status"),
                   "scoring_settings": league.get("scoring_settings"),
                   "roster_positions": roster_positions,
                   "settings": league.get("settings")},
        "nfl_state": {"week": week, "season": state.get("season"),
                      "season_type": state.get("season_type"),
                      "display_week": state.get("display_week")},
        "my_team": me,
        "my_team_matched_by": matched_by,
        "opponent": opponent,
        "teams": teams,
        "rostered_player_ids": sorted(taken),
        "available_skill_players": available,
        "trending_adds_48h": trend(trends_add),
        "trending_drops_48h": trend(trends_drop),
        "note": "Live injuries, projections, and locks require separate current verification. "
                "This is a timestamped Sleeper snapshot, not a live connection.",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "league_snapshot.json").write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    def format_player(p):
        if not p:
            return "EMPTY"
        status = p.get("injury_status") or p.get("status") or ""
        return p["name"] + " (" + str(p.get("position") or "?") + ", " + \
               str(p.get("team") or "FA") + (", " + status if status else "") + ")"

    def roster_md(t):
        result = ["### " + str(t["team_name"]) + " (roster " + str(t["roster_id"]) + ")"]
        result.extend("- " + s["slot"] + ": " + format_player(s["player"])
                      for s in t["starters"])
        for label in ("bench", "reserve", "taxi"):
            result.append("- " + label.title() + ": " +
                          (", ".join(format_player(p) for p in t[label]) or "none"))
        return "\n".join(result)

    lines = ["# MartensiteMafia Sleeper league snapshot",
             "**Captured (UTC):** " + now,
             "**NFL week:** " + str(week) + " | **League:** " +
             str(league.get("name")) + " (" + LEAGUE_ID + ")",
             "**Data:** Sleeper public read-only API; not live. Check capture time before advice.",
             "", "## My current lineup", roster_md(me), "",
             "## Current opponent", roster_md(opponent) if opponent else
             "No opponent returned for this week.", "",
             "## Top available skill players (Sleeper search order)"]
    lines.extend("- " + format_player(p) for p in available[:100])
    lines += ["", "## Trending additions (48h)"]
    lines.extend("- " + format_player(t["player"]) + " | adds: " +
                 str(t["count"]) + (" | AVAILABLE" if t["available"] else " | rostered")
                 for t in snapshot["trending_adds_48h"][:40])
    lines += ["", "## All league rosters"]
    lines.extend(roster_md(t) + "\n" for t in teams if t["roster_id"] != me["roster_id"])
    lines += ["", "For the complete available pool, scoring rules, player IDs, "
              "and team data, read data/league_snapshot.json.",
              "Source: https://docs.sleeper.com/"]
    (OUT / "league_snapshot.md").write_text("\n".join(lines) + "\n",
                                           encoding="utf-8")
    print("Snapshot complete: " + str(league.get("name")) +
          ", week " + str(week) + ", " + str(len(teams)) +
          " teams, " + str(len(available)) + " available skill players.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("Snapshot failed; existing files were not committed: " + str(exc),
              file=sys.stderr)
        sys.exit(1)
