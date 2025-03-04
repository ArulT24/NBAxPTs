from flask import Flask, request, jsonify
from flask_cors import CORS
from nba_api.stats.endpoints import playerdashptshots, playercareerstats, playergamelog
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import commonplayerinfo

import pandas as pd
import math
import time
from datetime import datetime

xPTs = Flask(__name__)  # Keeping your original variable name
CORS(xPTs, resources={r"/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:3000"]}})

def get_player_id(player_name):
    """Get player ID from player name."""
    player = next((p for p in players.get_active_players() if p["full_name"].lower() == player_name.lower()), None)
    return player["id"] if player else None

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

def get_player_games(player_id, season, season_type):
    """Get all games for a player in a specific season."""
    try:
        player_games = playergamelog.PlayerGameLog(
            player_id=player_id,
            season=season,
            season_type_all_star=season_type
        )
        games_df = player_games.get_data_frames()[0]
        
        if games_df.empty:
            print(f"No games found for player {player_id} in season {season}")
            return []
            
        # The GAME_DATE column format in the NBA API can be inconsistent
        # Add debug print to inspect the format
        print(f"Date format sample: {games_df['GAME_DATE'].iloc[0] if not games_df.empty else 'No dates'}")
        
        # First make sure we're working with datetime objects
        games_df['GAME_DATE'] = pd.to_datetime(games_df['GAME_DATE'])
        # Then format to YYYY-MM-DD string format
        games_df['FORMATTED_DATE'] = games_df['GAME_DATE'].dt.strftime('%Y-%m-%d')
        
        dates = games_df['FORMATTED_DATE'].tolist()
        print(f"Found {len(dates)} game dates")
        return dates
    except Exception as e:
        print(f"Error getting player games: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

@xPTs.route('/get_game_dates', methods=['POST'])
def get_game_dates():
    """API endpoint to fetch game dates for a player in a specific season."""
    data = request.json
    player_name = data.get("player_name")
    season = data.get("season")
    season_type = data.get("season_type")

    print(f"Fetching game dates for: {player_name}, {season}, {season_type}")

    if not player_name or not season or not season_type:
        return jsonify({"error": "Missing required parameters"}), 400
        
    player_id = get_player_id(player_name)
    if not player_id:
        print(f"Player not found: {player_name}")
        return jsonify({"error": "Player not found"}), 404
        
    print(f"Found player ID: {player_id}")
    dates = get_player_games(player_id, season, season_type)
    print(f"Returning {len(dates)} dates")
    return jsonify({"dates": dates})

def get_player_xPT(player_name, season, season_type, game_date=None):
    """Calculate a player's expected points for a given season or specific game."""
    player = next((p for p in players.get_active_players() if p["full_name"].lower() == player_name.lower()), None)
    if not player:
        return {"Player": player_name, "Season": season, "xPT": None, "error": "Player not found"}

    player_id = player["id"]
    team_id = get_team_for_season(player_id, season)
    if not team_id:
        return {"Player": player_name, "Season": season, "xPT": None, "error": "Team not found"}

    try:
        # For both scenarios, use playerdashptshots but with optional date filtering
        
        player_data = playergamelog.PlayerGameLog(
            player_id=player_id, 
            season=season, 
            season_type_all_star=season_type
        )
        dash_pt_shots_season_ground = playerdashptshots.PlayerDashPtShots(
            player_id=player_id, 
            team_id=team_id, 
            season=season, 
            season_type_all_star='Regular Season'
        )
        dash_pt_shots_season = playerdashptshots.PlayerDashPtShots(
            player_id=player_id, 
            team_id=team_id, 
            season=season, 
            season_type_all_star=season_type
        )
        closest_defender_shooting_ground = dash_pt_shots_season_ground.closest_defender_shooting.get_data_frame()
        closest_defender_shooting_season = dash_pt_shots_season.closest_defender_shooting.get_data_frame()
        if closest_defender_shooting_season.empty:
            return {
                "Player": player_name, 
                "Season": season, 
                "GameDate": game_date,
                "xPT": None, 
                "error": "No shooting data available"
            }
        if closest_defender_shooting_ground.empty:
            return {
                "Player": player_name, 
                "Season": season, 
                "GameDate": game_date,
                "xPT": None, 
                "error": "No shooting data available"
            }
        closest_defender_shooting_season.to_csv("closest.csv", index=False)
        # Get season average shooting percentages - handle NaN values
        # season_fg2p = float(closest_defender_shooting_season["FG2_PCT"].iloc[0]) if len(closest_defender_shooting_season) > 0 and not pd.isna(closest_defender_shooting_season["FG2_PCT"].iloc[0]) else 0
        # season_fg3p = float(closest_defender_shooting_season["FG3_PCT"].iloc[0]) if len(closest_defender_shooting_season) > 0 and not pd.isna(closest_defender_shooting_season["FG3_PCT"].iloc[0]) else 0

        if game_date:
            # When game_date is provided, set date_from and date_to to the same date
            dash_pt_shots_game = playerdashptshots.PlayerDashPtShots(
                player_id=player_id, 
                team_id=team_id, 
                season=season, 
                season_type_all_star=season_type,
                date_from_nullable=game_date,  # Filter for specific date
                date_to_nullable=game_date     # Filter for specific date
            )
            
            # For game-specific free throw data, we need to get that game's stats
            player_games = playergamelog.PlayerGameLog(
                player_id=player_id,
                season=season,
                season_type_all_star=season_type
            )
            games_df = player_games.get_data_frames()[0]
            
            # Convert dates for comparison
            games_df['GAME_DATE'] = pd.to_datetime(games_df['GAME_DATE'])
            game_date_dt = datetime.strptime(game_date, '%Y-%m-%d')
            
            # Filter for the specific game
            game_data = games_df[games_df['GAME_DATE'].dt.date == game_date_dt.date()]
            
            if game_data.empty:
                return {
                    "Player": player_name, 
                    "Season": season, 
                    "GameDate": game_date,
                    "xPT": None, 
                    "error": "No game found for this date"
                }
                
            # Get FT data for this specific game - handle NaN values
            fta = float(game_data['FTA'].iloc[0]) if not game_data.empty and not pd.isna(game_data['FTA'].iloc[0]) else 0
            closest_defender_shooting_game = dash_pt_shots_game.closest_defender_shooting.get_data_frame()
            if closest_defender_shooting_game.empty:
                return {
                    "Player": player_name, 
                    "Season": season, 
                    "GameDate": game_date,
                    "xPT": None, 
                    "error": "No shooting data available"
                }
            
            # Get shots attempted for this specific game - handle NaN values
            

            fg3 = (closest_defender_shooting_game["FG3A"]*closest_defender_shooting_ground["FG3_PCT"]).sum()
            fg2 = (closest_defender_shooting_game["FG2A"]*closest_defender_shooting_ground["FG2_PCT"]).sum()
        else:
            # For season data (original functionality)
            # Get season shots attempted - handle NaN values
            # fg2a = float(closest_defender_shooting_season["FG2A"].sum()) if "FG2A" in closest_defender_shooting_season.columns and not pd.isna(closest_defender_shooting_season["FG2A"].sum()) else 0
            # fg3a = float(closest_defender_shooting_season["FG3A"].sum()) if "FG3A" in closest_defender_shooting_season.columns and not pd.isna(closest_defender_shooting_season["FG3A"].sum()) else 0
            
            fg3 = (closest_defender_shooting_season["FG3A"]*closest_defender_shooting_ground["FG3_PCT"]).sum()
            fg2 = (closest_defender_shooting_season["FG2A"]*closest_defender_shooting_ground["FG2_PCT"]).sum()
            # Handle NaN in FTA values
            player_df = player_data.get_data_frames()[0]
            fta = float(player_df['FTA'].sum()) if not player_df.empty and 'FTA' in player_df.columns and not pd.isna(player_df['FTA'].sum()) else 0
            
        # Get FT percentage - use season average, handle NaN values
        player_df = player_data.get_data_frames()[0]
        if not player_df.empty and 'FT_PCT' in player_df.columns:
            ft_pct_values = player_df['FT_PCT'].dropna()
            season_ft_pct = float(ft_pct_values.mean()) if not ft_pct_values.empty else 0
        else:
            season_ft_pct = 0
        
        # Calculate xPT for 2PT and 3PT field goals
        
        
        # Calculate xFT
        xft_total = fta * season_ft_pct
        fg2 = fg2*2
        fg3=fg3*3
        print(xft_total)
        print(fg2)
        print(fg3)
        # Total xPT - ensure it's a valid number before using math.floor
        total_xp = fg3 + fg2 + xft_total
        
        # Check if total_xp is NaN, if so, return a more informative error
        if pd.isna(total_xp):
            return {
                "Player": player_name, 
                "Season": season, 
                "GameDate": game_date,
                "xPT": None, 
                "error": "Unable to calculate xPT - insufficient data"
            }
            
        totalXP = math.floor(total_xp)
        
        return {
            "Player": player_name, 
            "Season": season, 
            "GameDate": game_date,
            "xPT": totalXP
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()  # Print the full error for debugging
        return {
            "Player": player_name, 
            "Season": season, 
            "GameDate": game_date,
            "xPT": None, 
            "error": str(e)
        }
@xPTs.route('/get_players', methods=['GET'])
def get_players():
    """API endpoint to fetch a list of NBA players."""
    try:
        player_list = [p["full_name"] for p in players.get_active_players()]
        return jsonify({"players": player_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@xPTs.route('/get_xpt', methods=['POST'])
def get_xpt():
    """API endpoint to fetch expected points for a player."""
    data = request.json
    player_name = data.get("player_name")
    season = data.get("season")
    season_type = data.get("season_type")
    game_date = data.get("game_date")  # New parameter

    if not player_name or not season or not season_type:
        return jsonify({"error": "Missing required parameters"}), 400

    result = get_player_xPT(player_name, season, season_type, game_date)
    return jsonify(result)

if __name__ == '__main__':
    xPTs.run(debug=True)