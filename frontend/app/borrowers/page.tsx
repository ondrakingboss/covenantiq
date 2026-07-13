"use client";

import Link from "next/link";
import { ArrowRight, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getBorrowers } from "@/lib/api";
import type { Borrower } from "@/lib/types";

function riskTone(id: string) { return id === "ironbridge-components" ? "risk" : id === "vantage-services" ? "positive" : "warning"; }

export default function BorrowersPage() {
  const [items, setItems] = useState<Borrower[]>([]); const [error, setError] = useState(""); const [loading, setLoading] = useState(true);
  const load = () => { setLoading(true); setError(""); getBorrowers().then(setItems).catch(e => setError(e.message)).finally(() => setLoading(false)); };
  useEffect(load, []);
  return <main className="mx-auto max-w-[1500px] px-5 py-10 lg:px-8 lg:py-14">
    <div className="mb-10 max-w-2xl"><p className="font-mono text-xs uppercase tracking-[.12em] text-accent">Borrower universe</p><h1 className="mt-3 text-4xl font-semibold tracking-[-.045em] sm:text-5xl">Select a credit file</h1><p className="mt-4 text-ink/65">Five fictional borrowers span growth, stable, cyclical, asset-light, and distressed credit profiles.</p></div>
    {loading && <div className="grid gap-px bg-ink/15 border border-ink/15 lg:grid-cols-2">{[1,2,3,4].map(x=><div key={x} className="h-56 animate-pulse bg-paper p-6"><div className="h-5 w-1/2 bg-ink/10"/></div>)}</div>}
    {error && <div className="border border-risk/40 bg-risk/5 p-6"><p className="font-semibold text-risk">Could not reach the analysis API</p><p className="mt-2 text-sm text-ink/70">{error}</p><Button variant="outline" onClick={load} className="mt-4"><RefreshCw className="h-4 w-4"/>Retry</Button></div>}
    {!loading && !error && <div className="grid gap-px border border-ink/20 bg-ink/20 lg:grid-cols-2">
      {items.map((b) => { const p=b.periods[2], leverage=p.ebitda>0?p.total_debt/p.ebitda:null; return <Link href={`/analysis/${b.id}`} key={b.id} className="group bg-paper p-6 transition-colors hover:bg-white lg:p-8">
        <div className="flex items-start justify-between gap-4"><div><p className="font-mono text-[10px] uppercase tracking-widest text-ink/50">{b.industry}</p><h2 className="mt-2 text-2xl font-semibold tracking-tight">{b.name}</h2></div><Badge tone={riskTone(b.id) as "risk"|"positive"|"warning"}>{b.id === "ironbridge-components" ? "Elevated" : b.id === "vantage-services" ? "Lower" : "Moderate"}</Badge></div>
        <p className="mt-5 max-w-[58ch] text-sm leading-relaxed text-ink/65">{b.profile}</p>
        <div className="mt-7 grid grid-cols-3 border-y border-ink/15 py-4"><div><span className="block font-mono text-[9px] uppercase tracking-widest text-ink/45">Revenue</span><strong className="mt-1 block">${p.revenue.toFixed(1)}m</strong></div><div><span className="block font-mono text-[9px] uppercase tracking-widest text-ink/45">EBITDA</span><strong className="mt-1 block">${p.ebitda.toFixed(1)}m</strong></div><div><span className="block font-mono text-[9px] uppercase tracking-widest text-ink/45">Gross lev.</span><strong className="mt-1 block">{leverage?.toFixed(2) ?? "N/M"}x</strong></div></div>
        <div className="mt-5 flex items-center justify-between text-sm font-semibold"><span>Open credit file</span><ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1"/></div>
      </Link>})}
    </div>}
  </main>;
}
