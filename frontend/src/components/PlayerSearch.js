import React, { useState, useEffect } from "react";

const PlayerSearch = () => {
    const [playerName, setPlayerName] = useState("");
    const [season, setSeason] = useState("2023-24");
    const [seasonType, setSeasonType] = useState("Regular Season");
    const [result, setResult] = useState(null);
    const [playerList, setPlayerList] = useState([]);
    const [filteredPlayers, setFilteredPlayers] = useState([]);
    const [gameDates, setGameDates] = useState([]);
    const [selectedGameDate, setSelectedGameDate] = useState("");
    const [isLoadingDates, setIsLoadingDates] = useState(false);

    // Fetch all player names when the component mounts
    useEffect(() => {
        const fetchPlayers = async () => {
            try {
                const response = await fetch("http://127.0.0.1:5000/get_players");
                const data = await response.json();
                setPlayerList(data.players);
            } catch (error) {
                console.error("Failed to fetch players:", error);
            }
        };
        fetchPlayers();
    }, []);

    // Filter players as the user types
    useEffect(() => {
        if (playerName.length > 1) {
            const filtered = playerList.filter(player =>
                player.toLowerCase().includes(playerName.toLowerCase())
            );
            setFilteredPlayers(filtered.slice(0, 10)); // Limit to top 10 results
        } else {
            setFilteredPlayers([]);
        }
    }, [playerName, playerList]);

    // Fetch game dates when a player is selected
    
    // Add this debugging console log in the fetchGameDates function
    useEffect(() => {
        const fetchGameDates = async () => {
            if (playerName && playerList.includes(playerName)) {
                setIsLoadingDates(true);
                console.log(`Fetching game dates for ${playerName}, ${season}, ${seasonType}`);
                try {
                    const response = await fetch("http://127.0.0.1:5000/get_game_dates", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ 
                            player_name: playerName, 
                            season, 
                            season_type: seasonType 
                        }),
                    });
                    const data = await response.json();
                    console.log("Game dates API response:", data);
                    if (data.dates && Array.isArray(data.dates)) {
                        console.log(`Received ${data.dates.length} game dates`);
                        setGameDates(data.dates);
                        setSelectedGameDate(""); // Reset selected date
                    } else {
                        console.log("No dates array in response or empty array");
                        setGameDates([]);
                    }
                } catch (error) {
                    console.error("Failed to fetch game dates:", error);
                    setGameDates([]);
                } finally {
                    setIsLoadingDates(false);
                }
            } else {
                setGameDates([]);
                setSelectedGameDate("");
            }
        };

        fetchGameDates();
    }, [playerName, season, seasonType, playerList]);

    const fetchXPT = async () => {
        try {
            const response = await fetch("http://127.0.0.1:5000/get_xpt", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                    player_name: playerName, 
                    season, 
                    season_type: seasonType,
                    game_date: selectedGameDate || null // Pass null if no date selected
                }),
            });
            const data = await response.json();
            setResult(data);
        } catch (error) {
            console.error("Failed to fetch xPT:", error);
            setResult({ error: "Failed to fetch data. Please try again." });
        }
    };

    const handlePlayerSelect = (player) => {
        setPlayerName(player);
        setFilteredPlayers([]);
        setResult(null); // Clear previous results
    };

    return (
        <div style={{ maxWidth: 400, margin: "auto", padding: 20 }}>
            <h2>NBA Player xPT Calculator</h2>

            {/* Player search input */}
            <div style={{ marginBottom: 15 }}>
                <label style={{ display: "block", marginBottom: 5 }}>Player Name:</label>
                <input
                    type="text"
                    placeholder="Enter player name"
                    value={playerName}
                    onChange={(e) => setPlayerName(e.target.value)}
                    style={{ width: "100%", padding: 8, marginBottom: 5 }}
                />
                
                {/* Dropdown suggestions */}
                {filteredPlayers.length > 0 && (
                    <ul style={{
                        border: "1px solid #ccc", 
                        maxHeight: "150px", 
                        overflowY: "auto", 
                        listStyle: "none", 
                        padding: 0, 
                        margin: 0
                    }}>
                        {filteredPlayers.map((player, index) => (
                            <li key={index} 
                                style={{ padding: "8px", cursor: "pointer", backgroundColor: "#f9f9f9" }}
                                onClick={() => handlePlayerSelect(player)}>
                                {player}
                            </li>
                        ))}
                    </ul>
                )}
            </div>

            {/* Season selection */}
            <div style={{ marginBottom: 15 }}>
                <label style={{ display: "block", marginBottom: 5 }}>Season:</label>
                <select 
                    value={season} 
                    onChange={(e) => setSeason(e.target.value)} 
                    style={{ width: "100%", padding: 8 }}
                >
                    {["2024-25", "2023-24", "2022-23", "2021-22", "2020-21", "2019-20", "2018-19", 
                      "2017-18", "2016-17", "2015-16", "2014-15", "2013-14"].map((s) => (
                        <option key={s} value={s}>{s}</option>
                    ))}
                </select>
            </div>

            {/* Season type selection */}
            <div style={{ marginBottom: 15 }}>
                <label style={{ display: "block", marginBottom: 5 }}>Season Type:</label>
                <select 
                    value={seasonType} 
                    onChange={(e) => setSeasonType(e.target.value)} 
                    style={{ width: "100%", padding: 8 }}
                >
                    <option value="Regular Season">Regular Season</option>
                    <option value="Playoffs">Playoffs</option>
                </select>
            </div>

            {/* Game date selection */}
            {playerName && (
                <div style={{ marginBottom: 15 }}>
                    <label style={{ display: "block", marginBottom: 5 }}>Game Date (Optional):</label>
                    {isLoadingDates ? (
                        <p>Loading game dates...</p>
                    ) : gameDates.length > 0 ? (
                        <select
                            value={selectedGameDate}
                            onChange={(e) => setSelectedGameDate(e.target.value)}
                            style={{ width: "100%", padding: 8 }}
                        >
                            <option value="">All Games (Season Average)</option>
                            {gameDates.map((date) => (
                                <option key={date} value={date}>{date}</option>
                            ))}
                        </select>
                    ) : (
                        <p>No game dates found for this player in the selected season.</p>
                    )}
                </div>
            )}

            {/* Submit button */}
            <button 
                onClick={fetchXPT} 
                disabled={!playerName}
                style={{ 
                    width: "100%", 
                    padding: 10, 
                    background: !playerName ? "#cccccc" : "#007bff", 
                    color: "white", 
                    border: "none",
                    cursor: !playerName ? "not-allowed" : "pointer"
                }}
            >
                Get xPT
            </button>

            {/* Results */}
            {result && (
                <div style={{ marginTop: 20 }}>
                    <h3>Results:</h3>
                    {result.error ? (
                        <p style={{ color: "red" }}>Error: {result.error}</p>
                    ) : (
                        <div>
                            <p>
                                <strong>{result.Player}</strong> ({result.Season})
                                {result.GameDate && ` - ${result.GameDate}`}
                            </p>
                            <p>Expected Points: <strong>{result.xPT}</strong></p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default PlayerSearch;