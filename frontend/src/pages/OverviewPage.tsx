import { ArrowRight, Gauge, ShieldCheck, Wrench } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { formatProbability, PageHeader, RiskBadge, Status } from "../components";
import type { Prediction } from "../types";

type Overview = { total: number; flagged: number; normal: number; model_version: string; recent: Prediction[] };
export function OverviewPage() {
  const [data, setData] = useState<Overview | null>(null); const [error, setError] = useState("");
  useEffect(() => { api<Overview>("/api/overview").then(setData).catch((e: Error) => setError(e.message)); }, []);
  return <><PageHeader eyebrow="Operations overview" title="Know where to look next.">Machine-failure prediction estimates risk from current operating readings. It helps maintenance teams prioritize inspection; it does not diagnose a fault.</PageHeader>
    {error && <Status type="error">{error}</Status>}
    <section className="grid gap-px border bg-ink/20 sm:grid-cols-2 xl:grid-cols-4">
      {[['Total predictions', data?.total ?? '—'], ['Normal machines', data?.normal ?? '—'], ['Flagged machines', data?.flagged ?? '—'], ['Model version', data?.model_version ?? '—']].map(([label, value]) => <div className="bg-ivory p-6" key={label}><p className="eyebrow">{label}</p><p className="mt-3 font-display text-5xl font-semibold">{value}</p></div>)}
    </section>
    <section className="mt-12 grid gap-8 xl:grid-cols-[1fr_1.35fr]">
      <div><p className="eyebrow">How it works</p><h2 className="mt-2 text-4xl font-semibold">Six readings. One focused question.</h2><div className="mt-6 space-y-3">{[[Gauge, 'Read', 'Type, temperatures, speed, torque and tool wear.'], [ShieldCheck, 'Estimate', 'A fixed trained model returns a probability and risk band.'], [Wrench, 'Decide', 'Use the result to prioritize a qualified inspection.']].map(([Icon, title, text], index) => { const Component = Icon as typeof Gauge; return <div className="panel flex gap-4 p-4" key={String(title)}><Component className="mt-1 h-5 w-5" /><div><p className="font-bold">0{index + 1} / {String(title)}</p><p className="mt-1 text-sm text-ink/60">{String(text)}</p></div></div>; })}</div><Link to="/prediction" className="button mt-5">New prediction <ArrowRight className="h-4 w-4" /></Link></div>
      <div><div className="flex items-end justify-between"><div><p className="eyebrow">Recent activity</p><h2 className="mt-2 text-4xl font-semibold">Latest readings</h2></div><Link to="/history" className="text-sm font-bold underline">View all</Link></div><div className="mt-6 overflow-x-auto border"><table className="w-full min-w-[550px] text-left text-sm"><thead className="border-b bg-ink text-ivory"><tr><th className="p-3">Date</th><th className="p-3">Result</th><th className="p-3">Probability</th><th className="p-3">Risk</th></tr></thead><tbody>{data?.recent.length ? data.recent.map(item => <tr className="border-b last:border-0" key={item.id}><td className="p-3">{new Date(item.created_at).toLocaleString()}</td><td className="p-3 font-bold">{item.result}</td><td className="p-3">{formatProbability(item.probability)}</td><td className="p-3"><RiskBadge risk={item.risk_level} /></td></tr>) : <tr><td colSpan={4} className="p-8 text-center text-ink/55">No predictions yet. Start with a machine reading.</td></tr>}</tbody></table></div></div>
    </section></>;
}

