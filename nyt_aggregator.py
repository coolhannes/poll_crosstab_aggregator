import json
import re

import janitor
import pandas as pd

from nyt_functions import get_crosstabs

poll_dict = {
    "nytimes_2024_03_05_likely_voters": [
        "2024-02-28",
        "https://www.nytimes.com/interactive/2024/03/05/us/elections/times-siena-poll-likely-electorate-crosstabs.html",
    ],
    "nytimes_2024_03_05_all_voters": [
        "2024-02-28",
        "https://www.nytimes.com/interactive/2024/03/05/us/elections/times-siena-poll-registered-voter-crosstabs.html",
    ],
    "nytimes_2023_12_19_likely_voters": [
        "2023-12-14",
        "https://www.nytimes.com/interactive/2023/12/19/us/elections/times-siena-poll-likely-electorate-crosstabs.html",
    ],
    "nytimes_2023_12_19_all_voters": [
        "2023-12-14",
        "https://www.nytimes.com/interactive/2023/12/19/us/elections/times-siena-poll-registered-voter-crosstabs.html",
    ],
    "nytimes_2023_11_17_swing_state_likely_voters": [
        "2023-11-03",
        "https://www.nytimes.com/interactive/2023/11/07/us/elections/times-siena-battlegrounds-likely-electorate.html",
    ],
    "nytimes_2023_11_17_swing_state_all_voters": [
        "2023-11-03",
        "https://www.nytimes.com/interactive/2023/11/07/us/elections/times-siena-battlegrounds-registered-voters.html",
    ],
    "nytimes_2023_08_01_all_voters": [
        "2023-07-27",
        "https://www.nytimes.com/interactive/2023/08/01/us/elections/times-siena-poll-registered-voters-crosstabs.html",
    ],
}

# Place to store data
dfs = []

for df_name, metadata in poll_dict.items():

    poll_date = metadata[0]
    url = metadata[1]

    # Get crosstabs
    df = get_crosstabs(url)
    df["df_name"] = df_name  # Add df_name column
    df["fielding_end_date"] = poll_date
    df = janitor.clean_names(df)

    df_pivot = df.melt(
        id_vars=["df_name", "fielding_end_date", "question", "response"],
        var_name="cross_tab",
        value_name="values",
    )

    dfs.append(df_pivot)
    print(f"Processed: {df_name}")

# Concatenate dataframes
concatenated_df = pd.concat(dfs, ignore_index=True)

# Compile the regex pattern once for efficiency
pattern = re.compile(r"[%<-]")

concatenated_df["values_clean"] = pd.to_numeric(
    concatenated_df["values"].str.replace(pattern, "", regex=True), errors="coerce"
)

# Apply mask to find rows not equal to "Number of respondents"
mask = concatenated_df["response"] != "Number of respondents"

# Only divide these selected values by 100, the others are non-percentage integers
concatenated_df.loc[mask, "values_clean"] = (
    concatenated_df.loc[mask, "values_clean"] / 100
)

# Load the mappings from the JSON file
with open("nyt_crosstab_mappings.json") as f:
    nyt_crosstab_mappings = json.load(f)

# Extract the mappings dictionary
mappings = nyt_crosstab_mappings["nytimes"]["mappings"]

# Apply the mappings to the 'crosstab' column of concatenated_df
concatenated_df["cross_tab"] = concatenated_df["cross_tab"].map(
    lambda x: mappings.get(x, x)
)

# Save the dataframe to a CSV file
concatenated_df.to_csv("exports/nyt_crosstabs.csv", index=False)
