from nba_api.stats.endpoints import ShotChartDetail
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playerdashptshots
from nba_api.stats.library.parameters import SeasonAll
from nba_api.stats.endpoints import playercareerstats
import math
import pandas as pd

player_name = "LeBron James"
player = [p for p in players.get_players() if p["full_name"] == player_name][0]
player_id = player["id"]
season = '2023-24'
season_type = 'Regular Season'
team_name = "Los Angeles Lakers"
team = [t for t in teams.get_teams() if t["full_name"] == team_name][0]
team_id = team["id"]



dash_pt_shots = playerdashptshots.PlayerDashPtShots(
    player_id=player_id,
    season=season,
    team_id = team_id,
    season_type_all_star=season_type
)

dash_pt_shots.get_data_frames()[0].to_csv("dash.csv", index=False)
player_stats = playercareerstats.PlayerCareerStats(player_id=player_id)
career_data = player_stats.get_data_frames()[0]

free_throw_data = career_data[career_data['SEASON_ID'] == season][['SEASON_ID', 'FTM', 'FTA', 'FT_PCT']]

def calcXP(row):
    if row["FG3A"] == 0:
        fg3 = 0
    else:
        fg3 = row["FG3A"] * row["FG3_PCT"] * 3
    if row["FG2A"] == 0:
        fg2 = 0
    else:
        fg2 = row["FG2A"] * row["FG2_PCT"] * 2
    return fg3 + fg2
closest_defender_shooting = dash_pt_shots.closest_defender_shooting.get_data_frame()

closest_defender_shooting["xPT"] = closest_defender_shooting.apply(calcXP, axis = 1)
closest_defender_shooting.to_csv("closest_def_with_expected_points.csv", index=False)
xft_total = free_throw_data["FTA"] * free_throw_data["FT_PCT"]
xp_total = closest_defender_shooting["xPT"].sum()
totalXP = math.floor(xp_total + xft_total)
print("EXPECTED POINTS: ")
print(totalXP)
