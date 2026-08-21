import pandas as pd

history_df= pd.read_csv("data/raw/gatrout_history.csv")
rules_df = pd.read_csv("data/processed/stocking_rules_2026.csv")

rules_df["county"] = (
    rules_df["county"]
    .str.replace("\n", " ", regex=False)
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

name_aliases = {
    "Black Rock Lake": "Blackrock Lake",
    "Blueridge TW": "Blue Ridge Tailwaters",

    "Brasstown Creek (T)": "Brasstown Creek",
    "Brasstown Creek (U)": "Brasstown Creek",

    "Chattahoochee River (WMA)": "Chattahoochee River",

    "East Fork Little River - 2": "East Fork Little River",

    "Lanier Tailwater": "Lanier Tailwaters",

    "Little Amicalola": "Little Amicalola Creek",

    "Middle Broad River": "Middle Fork Broad R.",

    "Mill Creek - 1": "Mill Creek",

    "Panther Creek (H)": "Panther Creek",
    "Panther Creek (S)": "Panther Creek",

    "Rock Creek (F)": "Rock Creek Lake",

    "Tallulah River (R)": "Tallulah River",
    "Tallulah River (T)": "Tallulah River",

    "Timpson": "Timpson Creek",

    "Toccoa River (F)": "Toccoa River",

    "Town Creek (W)": "Town Creek",

    "W.F. Wolf Creek": "West Fork Wolf Creek",

    "West Armuchee": "West Armurchee Creek",

    "West Fork Chattooga River": "West Fork Chattooga"
}
county_aliases = {
    "Forsyth/Gwinnett": "Forsyth, Gwinnett"
}


history_df["dnr_waterbody"] = history_df["waterbody"].replace(name_aliases)
history_df["dnr_county"] = history_df["county"].replace(county_aliases)

print(
    history_df[
        ["waterbody", "dnr_waterbody", "dnr_county"]
    ].head(20)
)

history_df["stocked_on"] = pd.to_datetime(history_df["stocked_on"])

history_df = history_df.sort_values(
    ["dnr_waterbody", "dnr_county", "stocked_on"]
)

history_df["days_since_previous"] = (
    history_df.groupby(["dnr_waterbody", "dnr_county"])["stocked_on"]
    .diff()
    .dt.days
)
interval_stats = (
    history_df.groupby(["dnr_waterbody", "dnr_county"])["days_since_previous"]
    .agg(["count", "mean", "median", "min", "max"])
    .reset_index()
)

latest_stocking = (
    history_df.groupby(["dnr_waterbody", "dnr_county"])["stocked_on"]
    .max()
    .reset_index()
    .rename(columns={"stocked_on": "last_stocked"})
)
stream_summary = latest_stocking.merge(
    interval_stats,
    on=["dnr_waterbody", "dnr_county"],
    how="left"
)

prediction_df = stream_summary.merge(
    rules_df,
    left_on=["dnr_waterbody", "dnr_county"],
    right_on=["waterbody", "county"],
    how="left"
)

print(prediction_df.head(20))
print("Matched rules:", prediction_df["table"].notna().sum())
print("Missing rules:", prediction_df["table"].isna().sum())

missing_rules = prediction_df[
    prediction_df["table"].isna()
][["dnr_waterbody", "dnr_county"]]

print("Matched rules:", prediction_df["table"].notna().sum())
print("Missing rules:", prediction_df["table"].isna().sum())

print(missing_rules.to_string(index=False))


prediction_date = pd.Timestamp("2026-08-21")

prediction_df["days_since_last"] = (
    prediction_date - prediction_df["last_stocked"]
).dt.days

prediction_df["due_ratio"] = (
    prediction_df["days_since_last"] / prediction_df["median"]
)

prediction_df = prediction_df.sort_values(
    "due_ratio",
    ascending=False
)

print(
    prediction_df[
        [
            "dnr_waterbody",
            "dnr_county",
            "last_stocked",
            "median",
            "days_since_last",
            "table",
            "modifier",
            "due_ratio"
        ]
    ].head(20)
)

check_streams = [
    "Boggs Creek",
    "Amicalola Creek",
    "Big Creek",
    "Allison Creek",
    "Canada Creek",
    "Dukes Creek"
]

print(
    rules_df[
        rules_df["waterbody"].isin(check_streams)
    ][["waterbody", "county", "table", "modifier"]]
)