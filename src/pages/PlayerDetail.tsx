import { useEffect, useState } from "react";
import { ArrowLeft, Target } from "lucide-react";
import { ErrorState, LoadingState } from "@/components/Shell";
import { getPlayers } from "@/services/api";
import type { Player } from "@/types/api";

export function PlayerDetail({ slug }: { slug: string }) {
  const [player, setPlayer] = useState<Player | null>(null); const [error, setError] = useState("");
  useEffect(() => { getPlayers().then((players) => setPlayer(players.find((p) => p.full_name.toLowerCase().replace(/\s+/g, "-") === slug) ?? null)).catch((e: unknown) => setError(e instanceof Error ? e.message : "Unable to load player.")); }, [slug]);
  if (error) return <ErrorState message={error} />; if (!player) return <LoadingState label="Loading player profile..." />;
  const stats = [["Total points", player.total_points], ["Minutes", player.minutes], ["Goals", player.goals_scored], ["Assists", player.assists], ["Clean sheets", player.clean_sheets], ["ICT index", player.ict_index], ["Influence", player.influence], ["Creativity", player.creativity], ["Threat", player.threat]];
  return <><a className="back-link" href="#/players"><ArrowLeft size={15} /> Back to player explorer</a><section className="profile-hero"><div className="profile-badge"><Target size={28} /></div><div><span className="eyebrow">{player.element_type} · £{player.cost_m}m</span><h1>{player.full_name}</h1><p>Live player profile from the FPL dataset.</p></div></section><div className="stat-grid">{stats.map(([label, value]) => <div className="stat-card" key={String(label)}><small>{label}</small><strong>{value}</strong></div>)}</div><div className="detail-actions"><a className="button primary" href={`#/analysis?player=${encodeURIComponent(player.full_name)}`}>Recruitment analysis</a></div></>;
}
