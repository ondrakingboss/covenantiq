"use client";

import Link from "next/link";
import { ArrowRight, CheckCircle2, GitCompareArrows, Loader2, ShieldAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { getGuidedDemos } from "@/lib/api";
import type { GuidedDemo } from "@/lib/types";

const icons = {"healthy-approval":CheckCircle2,"distressed-decline":ShieldAlert,"structure-comparison":GitCompareArrows};

export default function GuidedDemosPage(){
  const [demos,setDemos]=useState<GuidedDemo[]>([]);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState("");
  useEffect(()=>{getGuidedDemos().then(setDemos).catch(e=>setError(e.message)).finally(()=>setLoading(false))},[]);
  return <main className="mx-auto max-w-[1500px] px-5 py-10 lg:px-8 lg:py-14">
    <header className="max-w-3xl"><p className="font-mono text-xs uppercase tracking-[.12em] text-accent">Product walkthrough</p><h1 className="mt-3 text-4xl font-semibold tracking-[-.045em] sm:text-5xl">Guided workflows</h1><p className="mt-5 text-base leading-relaxed text-ink/65">Three focused workflows show how CovenantIQ moves from calculated evidence to a credit decision. Each route uses the same deterministic Python engines as the full workspace.</p></header>
    {error&&<div role="alert" className="mt-8 border border-risk/40 bg-risk/5 p-5 text-sm text-risk"><strong>Workflow guide unavailable.</strong><span className="mt-1 block">{error}</span></div>}
    {loading?<div className="mt-10 grid gap-5 lg:grid-cols-3" aria-label="Loading guided workflows">{[0,1,2].map(i=><div key={i} className="h-96 animate-pulse border border-ink/15 bg-white"/>)}</div>:<div className="mt-10 grid gap-5 lg:grid-cols-3">{demos.map((demo,index)=>{const Icon=icons[demo.id as keyof typeof icons]||CheckCircle2;return <article key={demo.id} className="flex min-h-[430px] flex-col border border-ink/20 bg-white p-6 sm:p-8"><div className="flex items-start justify-between"><span className="grid h-11 w-11 place-items-center border border-ink/25 bg-paper"><Icon className="h-5 w-5 text-accent"/></span><span className="font-mono text-xs text-ink/40">0{index+1}</span></div><h2 className="mt-8 text-2xl font-semibold tracking-tight">{demo.title}</h2><p className="mt-3 text-sm leading-relaxed text-ink/65">{demo.explanation}</p><div className="mt-6 border-l-2 border-accent pl-4"><p className="font-mono text-[9px] uppercase tracking-wider text-ink/45">Expected outcome</p><p className="mt-2 text-sm font-semibold leading-relaxed">{demo.expected_outcome}</p></div><div className="mt-6"><p className="font-mono text-[9px] uppercase tracking-wider text-ink/45">Review notes</p><ul className="mt-3 space-y-2 text-sm text-ink/65">{demo.talking_points.map(point=><li key={point} className="flex gap-2"><span className="text-accent">•</span><span>{point}</span></li>)}</ul></div><Link href={demo.route} className="group mt-auto flex items-center justify-between border-t border-ink/20 pt-6 font-semibold text-accent"><span>Open workflow</span><ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1"/></Link></article>})}</div>}
    <section className="mt-10 border border-ink/20 bg-navy p-6 text-white sm:p-8"><p className="font-mono text-[10px] uppercase tracking-widest text-white/55">Decision standard</p><p className="mt-3 max-w-4xl text-xl leading-relaxed">Explain not only what the decision is, but which rule fired, which calculated evidence supported it, and how a different capital structure changes the result.</p></section>
  </main>;
}
