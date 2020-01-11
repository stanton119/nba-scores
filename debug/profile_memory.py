# %% reload modules when changed
# %load_ext autoreload
# %autoreload 2

# %% Add main path
import os 
import sys
dir_path = os.path.dirname(os.path.realpath(__file__))
base_dir, cur_dir = os.path.split(dir_path)
sys.path.append(os.path.join(base_dir, 'src'))

# %% Profile imports
@profile
def run_imports():
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

    import main
run_imports()

# %% Profile memory usage
import main
@profile
def run_game_plot(game_id):

    url = f"https://www.basketball-reference.com/boxscores/pbp/{game_id}.html"
    score_df = main.dataframe_from_url(url)
    score_df = main.clean_table(score_df)
    score_plot = main.create_plot(score_df)
    score_plot_html = main.convert_plot_to_html(score_plot)
    return score_plot_html

game_id = "202001040DAL"
score_plot_html = run_game_plot(game_id)

"""
python -m memory_profiler debug/profile_memory.py

The biggest memory users are pandas+numpy and plotting tools

Line #    Mem usage    Increment   Line Contents
================================================
    13   36.535 MiB   36.535 MiB   @profile
    14                             def run_imports():
    15   36.535 MiB    0.000 MiB       import re
    16   36.535 MiB    0.000 MiB       import datetime
    17   40.102 MiB    3.566 MiB       import requests
    18                             
    19   80.727 MiB   40.625 MiB       import pandas as pd
    20   80.727 MiB    0.000 MiB       import numpy as np
    21  138.832 MiB   58.105 MiB       import hvplot.pandas
    22  138.832 MiB    0.000 MiB       from bokeh.models import HoverTool
    23  138.832 MiB    0.000 MiB       from bokeh.resources import CDN
    24  138.832 MiB    0.000 MiB       from bokeh.embed import file_html
    25  138.832 MiB    0.000 MiB       import holoviews as hv
    26  142.492 MiB    3.660 MiB       from flask import Flask, request
    27                             
    28  142.602 MiB    0.109 MiB       import main

Line #    Mem usage    Increment   Line Contents
================================================
    33  142.941 MiB  142.941 MiB   @profile
    34                             def run_game_plot(game_id):
    35                             
    36  142.941 MiB    0.000 MiB       url = f"https://www.basketball-reference.com/boxscores/pbp/{game_id}.html"
    37  156.539 MiB   13.598 MiB       score_df = main.dataframe_from_url(url)
    38  157.777 MiB    1.238 MiB       score_df = main.clean_table(score_df)
    39  158.051 MiB    0.273 MiB       score_plot = main.create_plot(score_df)
    40  160.973 MiB    2.922 MiB       score_plot_html = main.convert_plot_to_html(score_plot)
    41  160.973 MiB    0.000 MiB       return score_plot_html
"""