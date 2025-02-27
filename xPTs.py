from nba_api.stats.endpoints import playerdashptshots, playercareerstats, playergamelog
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import commonplayerinfo

import pandas as pd
import math
import time

from nba_api.stats.endpoints import playercareerstats

def get_team_for_season(player_id, season):
    """Fetches the player's team ID for a given season."""
    try:
        player_stats = playercareerstats.PlayerCareerStats(player_id=player_id)
        df = player_stats.get_data_frames()[0]

        # Extract the row matching the given season
        season_data = df[df['SEASON_ID'] == season]

        if season_data.empty:
            print(f"No data found for player {player_id} in season {season}.")
            return None

        team_id = season_data.iloc[0]['TEAM_ID']  # Get the first row's team_id
        return int(team_id) if not pd.isna(team_id) else None
    except Exception as e:
        print(f"Error fetching team for player {player_id} in {season}: {e}")
        return None




def calcXP(row):
    """Calculate expected points based on FG attempts and percentages."""
    fg3 = row["FG3A"] * row["FG3_PCT"] * 3 if row["FG3A"] > 0 else 0
    fg2 = row["FG2A"] * row["FG2_PCT"] * 2 if row["FG2A"] > 0 else 0
    return fg3 + fg2

def get_player_xPT(player, season, season_type):
    player_id = player["id"]
    player_name = player["full_name"]
    
    team_id = get_team_for_season(player_id, season)
    if not team_id:
        print(f"Team not found for {player_name}, skipping...")
        return {"Player": player_name, "Season": season, "xPT": None}
    
    try:
        
        dash_pt_shots = playerdashptshots.PlayerDashPtShots(
            player_id=player_id, team_id=team_id, season=season, season_type_all_star=season_type
        )
        player_data = playergamelog.PlayerGameLog(
            player_id=player_id,season=season, season_type_all_star=season_type
        )
        free_throw_data = player_data.get_data_frames()[0][['FTA', 'FT_PCT']]
        closest_defender_shooting = dash_pt_shots.closest_defender_shooting.get_data_frame()
        
        if closest_defender_shooting.empty:
            print(f"No shooting data available for {player_name} in {season}. Skipping...")
            return {"Player": player_name, "Season": season, "xPT": None}
        closest_defender_shooting["xPT"] = closest_defender_shooting.apply(calcXP, axis=1)
        closest_defender_shooting.to_csv("closest.csv", index=False)

        xp_total = closest_defender_shooting["xPT"].sum()
        player_stats = playercareerstats.PlayerCareerStats(player_id=player_id)
        career_data = player_stats.get_data_frames()[0]
        
        xft_total = (free_throw_data["FTA"] * free_throw_data["FT_PCT"]).sum()
        totalXP = math.floor(xp_total + xft_total)
        return {"Player": player_name, "Season": season, "xPT": totalXP}
    
    except Exception as e:
        print(f"Error processing {player_name}: {e}")
        return {"Player": player_name, "Season": season, "xPT": None}

def main():
    player_name = input("Enter player name: ")  #search bar
    player = next((p for p in players.get_active_players() if p["full_name"].lower() == player_name.lower()), None) 
    season = input("Enter season (i.e. 2023-24): ")     #also will be a button
    season_type = input("Enter season type: (Regular Season or Playoffs): ")        #this will be a button
    result = get_player_xPT(player, season, season_type)
    #df = pd.DataFrame(results)
    #df.to_csv("all_players_xPT.csv", index=False)
    print(result)
    #print("All player xPTs saved to all_players_xPT.csv")

if __name__ == "__main__":
    main()
