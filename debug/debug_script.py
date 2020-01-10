# %% reload modules when changed
# %load_ext autoreload
# %autoreload 2

# %%
import sys
sys.path.append('../src')
import main

# %% Scrape match information
game_id = "202001040DAL"
score_plot = main.generate_plot(game_id)

# %% Save example match
main.save_plot_to_html(score_plot)
