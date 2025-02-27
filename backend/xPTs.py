from flask import Flask, request, jsonify
from flask_cors import CORS
from nba_api.stats.endpoints import playerdashptshots, playercareerstats, playergamelog
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import commonplayerinfo

import pandas as pd
import math
import time

from nba_api.stats.endpoints import playercareerstats

xPTs = Flask(__name__)
CORS(xPTs, resources={r"/get_xpt": {"origins": "http://localhost:3000"}})

def get_team_for_season(player_id, season):
    """Fetches the player's team ID for a given season."""
    try:
        player_stats = playercareerstats.PlayerCareerStats(player_id=player_id)
        df = player_stats.get_data_frames()[0]
        season_data = df[df['SEASON_ID'] == season]
        if season_data.empty:
            return None
        return int(season_data.iloc[0]['TEAM_ID'])
    except Exception:
        return None

def calcXP(row):
    """Calculate expected points based on FG attempts and percentages."""
    fg3 = row["FG3A"] * row["FG3_PCT"] * 3 if row["FG3A"] > 0 else 0
    fg2 = row["FG2A"] * row["FG2_PCT"] * 2 if row["FG2A"] > 0 else 0
    return fg3 + fg2

def get_player_xPT(player_name, season, season_type):
    """Calculate a player's expected points for a given season."""
    player = next((p for p in players.get_active_players() if p["full_name"].lower() == player_name.lower()), None)
    if not player:
        return {"Player": player_name, "Season": season, "xPT": None, "error": "Player not found"}

    player_id = player["id"]
    team_id = get_team_for_season(player_id, season)
    if not team_id:
        return {"Player": player_name, "Season": season, "xPT": None, "error": "Team not found"}

    try:
        dash_pt_shots = playerdashptshots.PlayerDashPtShots(
            player_id=player_id, team_id=team_id, season=season, season_type_all_star=season_type
        )
        player_data = playergamelog.PlayerGameLog(player_id=player_id, season=season, season_type_all_star=season_type)
        
        free_throw_data = player_data.get_data_frames()[0][['FTA', 'FT_PCT']]
        closest_defender_shooting = dash_pt_shots.closest_defender_shooting.get_data_frame()
        
        if closest_defender_shooting.empty:
            return {"Player": player_name, "Season": season, "xPT": None, "error": "No shooting data"}

        closest_defender_shooting["xPT"] = closest_defender_shooting.apply(calcXP, axis=1)
        xp_total = closest_defender_shooting["xPT"].sum()
        xft_total = (free_throw_data["FTA"] * free_throw_data["FT_PCT"]).sum()
        totalXP = math.floor(xp_total + xft_total)
        
        return {"Player": player_name, "Season": season, "xPT": totalXP}
    
    except Exception as e:
        return {"Player": player_name, "Season": season, "xPT": None, "error": str(e)}

@xPTs.route('/get_xpt', methods=['POST'])
def get_xpt():
    """API endpoint to fetch expected points for a player."""
    data = request.json
    player_name = data.get("player_name")
    season = data.get("season")
    season_type = data.get("season_type")

    if not player_name or not season or not season_type:
        return jsonify({"error": "Missing required parameters"}), 400

    result = get_player_xPT(player_name, season, season_type)
    return jsonify(result)

if __name__ == '__main__':
    xPTs.run(debug=True)
