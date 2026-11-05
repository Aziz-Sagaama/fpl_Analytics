import { ArrowRight, BarChart3, Database, Sparkles, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { ErrorState, LoadingState, PageHeader } from "@/components/Shell";
import { getAdvancedData, getOverview } from "@/services/api";
import type { AdvancedData, Overview } from "@/types/api";

export function Dashboard() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [data, setData] = useState<AdvancedData | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { Promise.all([getOverview(), getAdvancedData()]).then(([o, d]) => { setOverview(o); setData(d); }).catch((e: unknown) => setError(e instanceof Error ? e.message : "Unable to load dashboard.")); }, []);
  if (error) return <ErrorState message={error} />;
  if (!overview || !data) return <LoadingState />;
  return <><PageHeader eyebrow="FPL / Dashboard" title="Make smarter transfers with data." description="A live analytics workspace for exploring player performance, testing model recommendations, and evaluating recruitment value." /><div className="kpi-grid">{[["Players", overview.total_players], ["Features", overview.feature_count], ["Avg points", overview.average_total_points], ["Avg price", `£${overview.average_price}m`]].map(([label, value]) => <div className="kpi" key={String(label)}><span>{label}</span><strong>{value}</strong></div>)}</div><div className="dashboard-grid"><section className="hero-panel"><div className="hero-icon"><BarChart3 /></div><p className="eyebrow">The workflow</p><h2>Dataset → exploration → prediction → decision.</h2><p>Inspect the actual player dataset, understand positional performance, then use the Random Forest model to find candidates and assess recruitment potential.</p><div className="hero-actions"><a className="button primary" href="#/explore">Explore the data <ArrowRight size={16} /></a><a className="button secondary" href="#/recommend">Find players <Sparkles size={16} /></a></div></section><section className="quick-panel"><p className="eyebrow">Dataset health</p><div className="health-row"><Database size={18} /><span>Missing values</span><b>{overview.missing_values}</b></div><div className="health-row"><Users size={18} /><span>Duplicate records</span><b>{overview.duplicate_records}</b></div><div className="health-row"><BarChart3 size={18} /><span>Top performer</span><b>{data.top_players[0]?.player}</b></div></section></div></>;
}
