import pandas as pd


history_df = pd.read_csv("data/raw/gatrout_history.csv")
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


history_df["stocked_on"] = pd.to_datetime(history_df["stocked_on"])


history_df = history_df.sort_values(
    ["dnr_waterbody", "dnr_county", "stocked_on"]
)


history_df["days_since_previous"] = (
    history_df
    .groupby(["dnr_waterbody", "dnr_county"])["stocked_on"]
    .diff()
    .dt.days
)


interval_stats = (
    history_df
    .groupby(["dnr_waterbody", "dnr_county"])["days_since_previous"]
    .agg(["count", "mean", "median", "min", "max"])
    .reset_index()
)


latest_stocking = (
    history_df
    .groupby(["dnr_waterbody", "dnr_county"])["stocked_on"]
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


prediction_date = pd.Timestamp("2026-08-21")


prediction_df["days_since_last"] = (
    prediction_date - prediction_df["last_stocked"]
).dt.days

# Start with the historical median
prediction_df["expected_days"] = prediction_df["median"]

# Table 1 regular streams: about twice before Labor Day
prediction_df.loc[
    (prediction_df["table"] == 1) &
    (prediction_df["modifier"].isna()),
    "expected_days"
] = 14

# Table 1 **: twice monthly after July 4
prediction_df.loc[
    (prediction_df["table"] == 1) &
    (prediction_df["modifier"] == "**"),
    "expected_days"
] = 14

# Table 2 regular: twice monthly
prediction_df.loc[
    (prediction_df["table"] == 2) &
    (prediction_df["modifier"].isna()),
    "expected_days"
] = 14

# Table 2 **: once monthly after July 4
prediction_df.loc[
    (prediction_df["table"] == 2) &
    (prediction_df["modifier"] == "**"),
    "expected_days"
] = 30

# Table 3: once monthly
prediction_df.loc[
    prediction_df["table"] == 3,
    "expected_days"
] = 30

# New due ratio based on the CURRENT schedule
prediction_df["due_ratio"] = (
    prediction_df["days_since_last"] /
    prediction_df["expected_days"]
)

prediction_df = prediction_df.sort_values(
    "due_ratio",
    ascending=False
)


prediction_df["eligible"] = True

prediction_df.loc[
    (prediction_df["table"] == 1) &
    (prediction_df["modifier"] == "*"),
    "eligible"
] = False

prediction_df.loc[
    (prediction_df["table"] == 2) &
    (prediction_df["modifier"] == "*"),
    "eligible"
] = False

prediction_df.loc[
    (prediction_df["table"] == 4) &
    (prediction_df["modifier"] == "*"),
    "eligible"
] = False

prediction_df.loc[
    prediction_df["table"] == 5,
    "eligible"
] = False

prediction_df = prediction_df[
    prediction_df["eligible"] == True
]

prediction_df = prediction_df.sort_values(
    "due_ratio",
    ascending=False
)

august_stockings = history_df[
    history_df["stocked_on"].dt.month == 8
].groupby(
    ["dnr_waterbody", "dnr_county"]
).size().reset_index(name="august_count")

prediction_df = prediction_df.merge(
    august_stockings,
    on=["dnr_waterbody", "dnr_county"],
    how="left"
)

prediction_df["august_count"] = (
    prediction_df["august_count"]
    .fillna(0)
    .astype(int)
)



prediction_df.loc[
    (prediction_df["table"] == 1) &
    (prediction_df["modifier"].isna()) &
    (prediction_df["august_count"] >= 2),
    "eligible"
] = False


prediction_df.loc[
    (prediction_df["table"] == 1) &
    (prediction_df["modifier"] == "**") &
    (prediction_df["august_count"] >= 2),
    "eligible"
] = False


prediction_df.loc[
    (prediction_df["table"] == 2) &
    (prediction_df["modifier"].isna()) &
    (prediction_df["august_count"] >= 2),
    "eligible"
] = False


prediction_df.loc[
    (prediction_df["table"] == 2) &
    (prediction_df["modifier"] == "**") &
    (prediction_df["august_count"] >= 1),
    "eligible"
] = False

prediction_df.loc[
    (prediction_df["table"] == 3) &
    (prediction_df["august_count"] >= 1),
    "eligible"
] = False



prediction_df = prediction_df[
    prediction_df["eligible"] == True
]

prediction_df["prediction_score"] = prediction_df["due_ratio"]

prediction_df = prediction_df.sort_values(
    "prediction_score",
    ascending=False
)

final_predictions = prediction_df[
    [
        "dnr_waterbody",
        "dnr_county",
        "last_stocked",
        "days_since_last",
        "table",
        "modifier",
        "august_count",
        "expected_days",
        "prediction_score"
    ]
].head(20)

final_predictions.to_csv(
    "data/processed/prediction_2026-08-21.csv",
    index=False
)

print(final_predictions)
print("\nSaved prediction_2026-08-21.csv")