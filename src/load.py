"""Load raw data from FPL (players stats) and transfermarkt (values)"""

from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data"
VAASTAV = DATA / "vaastav" / "data"
TM = DATA / "transfermarkt"

SEASONS = ["2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]

# Performance columns available in every season.
# Excluded: xP, value, selected, transfers, expected_* (zeros before GW16 2022-23, missing in 2021-22),
# starts (missing before 2022-23)
GW_COLS = [
    "name", "element", "position", "team", "kickoff_time", "minutes",
    "goals_scored", "assists", "clean_sheets", "goals_conceded", "saves",
    "penalties_saved", "influence", "creativity", "threat", "ict_index",
    "bonus", "bps", "yellow_cards", "red_cards", "own_goals",
]


def load_gw(seasons=SEASONS):
    frames = []
    for s in seasons:
        df = pd.read_csv(VAASTAV / s / "gws" / "merged_gw.csv", usecols=GW_COLS)
        df["season"] = s
        frames.append(df)
    gw = pd.concat(frames, ignore_index=True)

    # 2024-25 includes assistant managers ("AM") who are not players, so we drop them
    gw = gw[gw["position"] != "AM"].reset_index(drop=True)

    # 2021-22 uses both "GK" and "GKP" for goalkeepers so we standardize to "GK" for all seasons
    gw["position"] = gw["position"].replace("GKP", "GK")
    gw["kickoff_time"] = pd.to_datetime(gw["kickoff_time"], utc=True)
    return gw


def load_valuations(start="2021-07-01"):
    # no filter on player_club_domestic_competition_id: it's not reliable at the valuation date
    # (Firmino's Liverpool values are tagged SA1), Premier League clubs are kept in 02_matching
    val = pd.read_csv(TM / "player_valuations.csv.gz", parse_dates=["date"])
    val = val[val["date"] >= start]
    return val.reset_index(drop=True)


def load_fpl_players(seasons=SEASONS):
    # one row per FPL player per season; id is the same as element in merged_gw
    frames = []
    for s in seasons:
        df = pd.read_csv(
            VAASTAV / s / "players_raw.csv",
            usecols=["id", "code", "first_name", "second_name", "web_name"],
        )
        df["season"] = s
        frames.append(df)
    return pd.concat(frames, ignore_index=True).rename(columns={"id": "element"})


# market_value_in_eur, highest_market_value_in_eur and contract_expiration_date excluded (leakage)
def load_players():
    return pd.read_csv(
        TM / "players.csv.gz",
        usecols=["player_id", "name", "date_of_birth", "position", "sub_position"],
        parse_dates=["date_of_birth"],
    )
