import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectTrigger, SelectContent, SelectItem } from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";

export default function XPCalculator() {
  const [playerName, setPlayerName] = useState("");
  const [season, setSeason] = useState("2023-24");
  const [seasonType, setSeasonType] = useState("Regular Season");
  const [result, setResult] = useState(null);

  const fetchXP = async () => {
    const response = await fetch("http://127.0.0.1:5000/calculate_xp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ player_name: playerName, season, season_type: seasonType })
    });
    const data = await response.json();
    setResult(data);
  };

  return (
    <div className="max-w-md mx-auto p-4 space-y-4">
      <Input placeholder="Enter player name" value={playerName} onChange={(e) => setPlayerName(e.target.value)} />
      
      <Select value={season} onValueChange={setSeason}>
        <SelectTrigger>{season}</SelectTrigger>
        <SelectContent>
          {[...Array(10)].map((_, i) => (
            <SelectItem key={i} value={`${2023 - i}-${(2024 - i).toString().slice(2)}`}>{`${2023 - i}-${(2024 - i).toString().slice(2)}`}</SelectItem>
          ))}
        </SelectContent>
      </Select>
      
      <Select value={seasonType} onValueChange={setSeasonType}>
        <SelectTrigger>{seasonType}</SelectTrigger>
        <SelectContent>
          <SelectItem value="Regular Season">Regular Season</SelectItem>
          <SelectItem value="Playoffs">Playoffs</SelectItem>
        </SelectContent>
      </Select>
      
      <Button onClick={fetchXP}>Calculate xPT</Button>
      
      {result && (
        <Card>
          <CardContent className="p-4">
            <p><strong>Player:</strong> {result.Player}</p>
            <p><strong>Season:</strong> {result.Season}</p>
            <p><strong>Expected Points:</strong> {result.xPT !== null ? result.xPT : "N/A"}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
