# %%
import re
import datetime
import requests

import pandas as pd
import numpy as np
import hvplot.pandas
from bokeh.models import HoverTool
from bokeh.resources import CDN
from bokeh.embed import file_html
import holoviews as hv
from flask import Flask, request

# %% Request page
def score_table_from_url(url):
    # Fetch URL contents
    response = requests.get(url)
    return response.content
    # if ~response.ok:
    #     return None
    # page_data = BeautifulSoup(response.content, "html.parser")
    # return page_data.find(name="table", attrs={"id": "pbp"})


# %% Create dataframe
def dataframe_from_table_html(html_str):
    score_table = pd.read_html(io=html_str, attrs={"id": "pbp"}, flavor="bs4",)[0]
    return score_table["1st Q"]


# %% Cleaning functions
def remove_unnamed_columns(score_df) -> pd.DataFrame:
    p = re.compile(r"Unnamed\S*")
    del_cols = list(filter(p.match, score_df.columns))
    return score_df.drop(columns=del_cols)


def add_quarter_column(score_df) -> pd.DataFrame:
    # Search for rows matching "x__ Q" for quarter starts
    filter_rows = score_df["Score"].str.contains(
        r"(\d{1}\w{2} Q\S*)|(\d{1}\w{2} OT\S*)"
    )
    # TODO: add in overtimes
    score_df["Quarter"] = 0
    score_df["Quarter"][0] = 1
    score_df["Quarter"].loc[filter_rows] = 1
    score_df["Quarter"] = score_df["Quarter"].cumsum()
    return score_df


def remove_nonscore_rows(score_df) -> pd.DataFrame:
    filter_rows = score_df["Score"].str.contains(r"\d+-\d+")
    return score_df.loc[filter_rows]


def scores_to_separate_columns(score_df) -> pd.DataFrame:
    score_df["Scores"] = score_df["Score"].apply(lambda x: x.split("-"))
    score_df["HomeScore"] = score_df["Scores"].apply(lambda x: x[0]).astype(int)
    score_df["AwayScore"] = score_df["Scores"].apply(lambda x: x[1]).astype(int)
    return score_df.drop(columns=["Score", "Scores"])


def add_team_label(score_df) -> pd.DataFrame:
    team_names = [
        col
        for col in score_df.columns
        if col not in ["Time", "Quarter", "HomeScore", "AwayScore"]
    ]
    team_label = score_df[team_names[0]].isna()
    score_df["TeamLabel"] = None
    score_df["TeamLabel"].loc[~team_label] = team_names[0]
    score_df["TeamLabel"].loc[team_label] = team_names[1]
    return score_df, team_names


def add_action_label(score_df, team_names) -> pd.DataFrame:
    score_df["Label"] = score_df[team_names].fillna("").sum(axis=1)
    return score_df.drop(columns=team_names)


def create_quarter_dict(max_quarter=7) -> pd.DataFrame:
    # Assumes max 4 quarters and 3 OTs, unless specified
    quarters = np.arange(stop=max_quarter, start=0) + 1
    quarter_dict = pd.DataFrame(data=pd.Series(quarters), columns=["Quarter"])
    quarter_dict["QuarterLen"] = 12
    quarter_dict["QuarterLen"][quarter_dict["Quarter"] > 4] = 5

    time_elapsed = [0]
    time_elapsed[1:] = quarter_dict["QuarterLen"][:-1].cumsum()
    # quarter_starts["TimeElapsed"] = quarter_starts["QuarterLen"]
    quarter_dict["TimeElapsed"] = time_elapsed
    return quarter_dict.set_index("Quarter")


def normalise_time_remaining(score_df) -> pd.DataFrame:
    quarter_dict = create_quarter_dict(score_df["Quarter"].max())
    score_df = score_df.join(quarter_dict, on="Quarter", how="left",)

    # Make single index column of elapsed in match
    score_df["TimeStamp"] = pd.to_datetime(
        score_df["QuarterLen"], format="%M"
    ) - pd.to_datetime(score_df["Time"], format="%M:%S.%f")

    score_df["TimeElapsed"] = score_df["TimeStamp"] + pd.to_datetime(
        score_df["TimeElapsed"], format="%M"
    )
    score_df.drop(columns=["QuarterLen", "TimeStamp"], inplace=True)
    return score_df


def relabel_quarter(score_df) -> pd.DataFrame:
    temp: pd.Series = score_df["Quarter"]
    temp.to_string()
    score_df["Quarter"] = score_df["Quarter"].to_string(flo)
    return score_df


def clean_table(score_df) -> pd.DataFrame:
    score_df = remove_unnamed_columns(score_df)
    score_df = add_quarter_column(score_df)
    score_df = remove_nonscore_rows(score_df)
    score_df = scores_to_separate_columns(score_df)
    score_df, team_names = add_team_label(score_df)
    score_df = add_action_label(score_df, team_names)
    score_df = normalise_time_remaining(score_df)

    # Remove duplicates
    # Free throws at the same time

    # Make Time index
    # score_df.set_index(keys=["Time", "Quarter"], inplace=True)
    score_df.set_index(keys=["TimeElapsed"], inplace=True)
    return score_df


# %% Wrapping functions
def dataframe_from_url(url) -> pd.DataFrame:
    table_html = score_table_from_url(url)
    score_df = dataframe_from_table_html(table_html)
    if score_df is None:
        return None
    return score_df


def create_plot(score_df):
    # %% create plot
    score_plot = score_df.hvplot(
        y=["HomeScore", "AwayScore"], hover_cols=list(score_df.columns)
    )

    hover = HoverTool(
        tooltips=[(col, "@" + col) for col in ["HomeScore", "AwayScore"]]
    )  # score_df.columns])
    score_plot = score_plot.opts(tools=[hover])
    return score_plot


def save_plot_to_html(score_plot):
    hvplot.save(score_plot, "MatchScorePlot.html", resources=INLINE)


def convert_plot_to_html(score_plot):
    bokeh_score_plot = hv.render(score_plot)
    return file_html(bokeh_score_plot, CDN, "Basketball Reference Plot")


# %% Plot changes
# Add lines for quarter starts
# Change x-axis to min
# major tick for quarter
# minor tick for minor
# add grid
# add hovers
# add larger axis limits

# %% Setup as webservice
app = Flask(__name__)

@app.route("/nba_score_plot", methods=["GET"])
def generate_plot():
    game_id = request.args.get("game_id")
    url = f"https://www.basketball-reference.com/boxscores/pbp/{game_id}.html"
    score_df = dataframe_from_url(url)
    score_df = clean_table(score_df)
    score_plot = create_plot(score_df)
    score_plot_html = convert_plot_to_html(score_plot)
    return score_plot_html, 200

if __name__ == "__main__":
    app.run(port=5000)

