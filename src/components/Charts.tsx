import type { AdvancedData, Player, Position } from "@/types/api";

export const colors: Record<Position, string> = { GK: "#f6c453", DEF: "#63a5ff", MID: "#45d6a0", FWD: "#ff7189" };
const labels: Record<string, string> = { minutes: "Minutes", goals_scored: "Goals", assists: "Assists", ict_index: "ICT index", total_points: "Total points", cost_m: "Price" };

export function Scatter({ players, xKey, title }: { players: Player[]; xKey: "cost_m" | "minutes" | "goals_scored" | "assists" | "ict_index"; title: string }) {
  const maxX = Math.max(...players.map((p) => p[xKey]), 1);
  const maxY = Math.max(...players.map((p) => p.total_points), 1);
  return <div className="chart-card"><div className="chart-title">{title}<span>n={players.length}</span></div><div className="scatter"><svg viewBox="0 0 100 100" preserveAspectRatio="none">{players.map((p) => <circle key={p.full_name} cx={p[xKey] / maxX * 100} cy={100 - p.total_points / maxY * 100} r=".85" fill={colors[p.element_type]} opacity=".72"><title>{`${p.full_name} · ${p.element_type} · ${labels[xKey]} ${p[xKey]} · Points ${p.total_points}`}</title></circle>)}</svg><span className="axis-x">{labels[xKey]}</span><span className="axis-y">Points</span></div><Legend /></div>;
}

function Legend() { return <div className="legend">{(Object.keys(colors) as Position[]).map((position) => <span key={position}><i style={{ background: colors[position] }} />{position}</span>)}</div>; }

export function Bars({ data, value, title, prefix = "" }: { data: AdvancedData["position_stats"]; value: "average_total_points" | "average_price"; title: string; prefix?: string }) {
  const max = Math.max(...data.map((d) => d[value]), 1);
  return <div className="chart-card"><div className="chart-title">{title}</div><div className="bars">{data.map((d) => <div className="bar-row" key={d.position}><b style={{ color: colors[d.position] }}>{d.position}</b><div className="bar-track"><div style={{ width: `${d[value] / max * 100}%`, background: colors[d.position] }} /></div><span>{prefix}{d[value]}</span></div>)}</div></div>;
}

export function Histogram({ bins, title, summary }: { bins: { label: string; count: number }[]; title: string; summary: string }) {
  const max = Math.max(...bins.map((b) => b.count), 1);
  return <div className="chart-card"><div className="chart-title">{title}</div><p className="chart-subtitle">{summary}</p><div className="histogram">{bins.map((b) => <div key={b.label} className="hist-bar" title={`${b.label}: ${b.count} players`} style={{ height: `${Math.max(3, b.count / max * 100)}%` }} />)}</div><div className="chart-range"><span>{bins[0]?.label}</span><span>{bins.at(-1)?.label}</span></div></div>;
}
