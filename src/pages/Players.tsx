import { Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { ErrorState, LoadingState, PageHeader } from "@/components/Shell";
import { getPlayers } from "@/services/api";
import type { Player, Position } from "@/types/api";

export function Players() {
  const [players, setPlayers] = useState<Player[]>([]);
  const [query, setQuery] = useState(""); const [position, setPosition] = useState<Position | "ALL">("ALL"); const [sort, setSort] = useState<keyof Player>("total_points"); const [error, setError] = useState("");
  useEffect(() => { getPlayers().then(setPlayers).catch((e: unknown) => setError(e instanceof Error ? e.message : "Unable to load players.")); }, []);
  const visible = useMemo(() => players.filter((p) => p.full_name.toLowerCase().includes(query.toLowerCase()) && (position === "ALL" || p.element_type === position)).sort((a, b) => Number(b[sort]) - Number(a[sort])), [players, query, position, sort]);
  if (error) return <ErrorState message={error} />; if (!players.length) return <LoadingState />;
  return <><PageHeader eyebrow="FPL / Player explorer" title="Every player. Every signal." description="Search and compare the real player records loaded by the prediction service." /><div className="toolbar"><label className="search-field"><Search size={16} /><input placeholder="Search player name..." value={query} onChange={(e) => setQuery(e.target.value)} /></label><label>Position <select value={position} onChange={(e) => setPosition(e.target.value as Position | "ALL")}><option value="ALL">All</option><option value="GK">GK</option><option value="DEF">DEF</option><option value="MID">MID</option><option value="FWD">FWD</option></select></label><label>Sort by <select value={sort} onChange={(e) => setSort(e.target.value as keyof Player)}><option value="total_points">Points</option><option value="cost_m">Price</option><option value="minutes">Minutes</option><option value="goals_scored">Goals</option><option value="assists">Assists</option></select></label></div><div className="player-grid">{visible.map((player) => <a href={`#/players/${encodeURIComponent(player.full_name.toLowerCase().replace(/\s+/g, "-"))}`} className="player-card" key={player.full_name}><div className="player-top"><span className="position-pill" style={{ borderColor: `color-mix(in srgb, var(--${player.element_type}), transparent 50%)` }}>{player.element_type}</span><b>£{player.cost_m}m</b></div><h3>{player.full_name}</h3><div className="player-stats"><span><small>Points</small>{player.total_points}</span><span><small>Minutes</small>{player.minutes}</span><span><small>ICT</small>{player.ict_index}</span></div></a>)}</div>{!visible.length && <div className="empty-state">No players match those filters.</div>}</>;
}
