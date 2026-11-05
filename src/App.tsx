import { useEffect, useState } from "react";
import { Shell } from "@/components/Shell";
import { Analysis } from "@/pages/Analysis";
import { Dashboard } from "@/pages/Dashboard";
import { DataExploration } from "@/pages/DataExploration";
import { PlayerDetail } from "@/pages/PlayerDetail";
import { Players } from "@/pages/Players";
import { Recommendations } from "@/pages/Recommendations";
import "./styles/app.css";

function routeFromHash() {
  return window.location.hash.slice(1) || "/";
}

export default function App() {
  const [route, setRoute] = useState(routeFromHash);
  useEffect(() => {
    const update = () => setRoute(routeFromHash());
    window.addEventListener("hashchange", update);
    return () => window.removeEventListener("hashchange", update);
  }, []);
  const base = route.split("?")[0];
  const playerSlug = base.startsWith("/players/") ? decodeURIComponent(base.slice("/players/".length)) : "";
  let page = base === "/" ? <Dashboard /> : base === "/explore" ? <DataExploration /> : base === "/players" ? <Players /> : base === "/recommend" ? <Recommendations /> : base === "/analysis" ? <Analysis /> : playerSlug ? <PlayerDetail slug={playerSlug} /> : <Dashboard />;
  if (base === "/analysis" && route.includes("?player=")) {
    const player = new URLSearchParams(route.split("?")[1]).get("player");
    page = <Analysis key={player ?? "analysis"} />;
  }
  return <Shell route={`/${base.replace(/^\//, "")}`}>{page}</Shell>;
}
