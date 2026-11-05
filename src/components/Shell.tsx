import { BarChart3, Database, Home, Search, Sparkles, Trophy } from "lucide-react";
import type { ReactNode } from "react";

const links = [
  { href: "#/", label: "Dashboard", icon: Home },
  { href: "#/explore", label: "Data exploration", icon: BarChart3 },
  { href: "#/players", label: "Player explorer", icon: Search },
  { href: "#/recommend", label: "Recommendations", icon: Sparkles },
  { href: "#/analysis", label: "Recruitment analysis", icon: Trophy },
];

export function Shell({ children, route }: { children: ReactNode; route: string }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a href="#/" className="brand"><span className="brand-mark"><Database size={19} /></span><span>FPL<span className="accent">/</span>LAB</span></a>
        <p className="sidebar-label">Analytics workspace</p>
        <nav>{links.map(({ href, label, icon: Icon }) => <a key={href} href={href} className={route === href.slice(1) ? "active" : ""}><Icon size={17} />{label}</a>)}</nav>
        <div className="sidebar-foot"><span className="live-dot" /> Model API online</div>
      </aside>
      <main className="main-content"><header className="topbar"><span>Fantasy Premier League Intelligence</span><span className="season-tag">DATA SCIENCE PROJECT · LIVE DATA</span></header>{children}</main>
    </div>
  );
}

export function PageHeader({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return <div className="page-header"><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p>{description}</p></div>;
}

export function ErrorState({ message }: { message: string }) {
  return <div className="error-state">{message}</div>;
}

export function LoadingState({ label = "Loading live dataset..." }: { label?: string }) {
  return <div className="loading-state"><span className="spinner" />{label}</div>;
}
