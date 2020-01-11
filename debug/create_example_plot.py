# %% reload modules when changed
# %load_ext autoreload
# %autoreload 2

# %%
import os 
import sys
dir_path = os.path.dirname(os.path.realpath(__file__))
base_dir, cur_dir = os.path.split(dir_path)
sys.path.append(os.path.join(base_dir, 'src'))

import main

# %% Scrape match information
game_id = "202001040DAL"
score_plot = main.generate_plot(game_id)

# %% Save example match
main.save_plot_to_html(score_plot)
