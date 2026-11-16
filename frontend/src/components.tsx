import { AlertTriangle, CheckCircle2, LoaderCircle, Menu, X } from "lucide-react";
import { useState, type ReactNode } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "./auth";

const nav = [
  ["/", "Overview"], ["/prediction", "New Prediction"], ["/batch", "Batch Analysis"],
  ["/history", "Prediction History"], ["/model", "Model Report"], ["/ask", "Ask MindMesh"], ["/account", "Account Settings"],
];

export function AppShell() {
  const [open, setOpen] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  return <div className="min-h-screen bg-ivory text-ink">
    <header className="sticky top-0 z-30 border-b border-ivory/20 bg-ink text-ivory">
      <div className="flex h-16 items-center justify-between px-4 md:px-7">
        <NavLink to="/" className="font-display text-2xl font-semibold">MindMesh <span className="text-acid">2</span></NavLink>
        <div className="hidden items-center gap-4 text-xs md:flex"><span className="text-ivory/60">Signed in as</span><strong>{user?.display_name}</strong><button className="border-b border-acid pb-0.5" onClick={async () => { await logout(); navigate("/login"); }}>Log out</button></div>
        <button aria-label="Toggle navigation" className="md:hidden" onClick={() => setOpen(!open)}>{open ? <X /> : <Menu />}</button>
      </div>
    </header>
    <div className="mx-auto grid max-w-[1600px] md:grid-cols-[250px_1fr]">
      <aside className={`${open ? "block" : "hidden"} fixed inset-x-0 top-16 z-20 border-b bg-ivory p-4 md:sticky md:top-16 md:block md:h-[calc(100vh-4rem)] md:border-b-0 md:border-r md:p-6`}>
        <p className="eyebrow mb-4">Workspace</p>
        <nav aria-label="Main navigation" className="space-y-1">{nav.map(([href, label], index) => <NavLink key={href} to={href} end={href === "/"} onClick={() => setOpen(false)} className={({ isActive }) => `flex items-center justify-between border px-3 py-2.5 text-sm transition ${isActive ? "border-ink bg-acid font-bold" : "border-transparent hover:border-ink/30"}`}><span>{label}</span><span className="font-mono text-[10px]">0{index + 1}</span></NavLink>)}</nav>
        <div className="mt-8 border-t pt-4 text-xs leading-5 text-ink/60">Decision support only. Always confirm model outputs through qualified inspection.</div>
      </aside>
      <main id="main" key={location.pathname} className="min-w-0 px-4 py-8 md:px-10 md:py-12"><Outlet /></main>
    </div>
  </div>;
}

export function PageHeader({ eyebrow, title, children }: { eyebrow: string; title: string; children?: ReactNode }) {
  return <header className="mb-9 max-w-3xl"><p className="eyebrow">{eyebrow}</p><h1 className="page-title">{title}</h1>{children && <div className="mt-4 max-w-2xl text-sm leading-6 text-ink/65">{children}</div>}</header>;
}

export function Status({ type = "info", children }: { type?: "info" | "error" | "success"; children: ReactNode }) {
  const Icon = type === "error" ? AlertTriangle : type === "success" ? CheckCircle2 : LoaderCircle;
  return <div role={type === "error" ? "alert" : "status"} className={`flex gap-3 border p-4 text-sm ${type === "error" ? "border-red-700 bg-red-50 text-red-900" : type === "success" ? "border-moss bg-green-50" : "bg-white/40"}`}><Icon className="h-5 w-5 shrink-0" />{children}</div>;
}

export function RiskBadge({ risk }: { risk: string }) {
  return <span className={`inline-flex border px-2 py-1 text-[10px] font-bold uppercase tracking-widest ${risk === "high" ? "border-red-700 bg-red-100 text-red-900" : risk === "medium" ? "border-amber-700 bg-amber-100" : "border-moss bg-green-100"}`}>{risk}</span>;
}

export function formatProbability(value: number) { return `${(value * 100).toFixed(1)}%`; }

