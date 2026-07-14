import Link from "next/link";
import { ArrowRight, Braces, FileText, Scale } from "lucide-react";

export default function Landing() {
  const principles = [
    { Icon: Braces, title: "Deterministic", body: "Financial metrics and risk rules run in Python without an external AI API." },
    { Icon: Scale, title: "Explainable", body: "Every metric exposes formula, inputs, source period, result, interpretation, and limits." },
    { Icon: FileText, title: "Memo-ready", body: "The same calculated result set flows into a print-optimized preliminary credit memo." },
  ];
  return <main>
    <section className="border-b border-ink/20">
      <div className="mx-auto grid min-h-[calc(100dvh-4rem)] max-w-[1500px] items-stretch lg:grid-cols-[1.08fr_.92fr]">
        <div className="flex flex-col justify-center px-6 py-20 lg:px-12 xl:px-20">
          <p className="mb-6 font-mono text-xs font-semibold uppercase tracking-[.14em] text-accent">Deterministic private-credit workbench</p>
          <h1 className="max-w-3xl text-5xl font-semibold leading-[.96] tracking-[-.055em] sm:text-6xl xl:text-7xl">Credit conclusions you can trace.</h1>
          <p className="mt-7 max-w-[56ch] text-lg leading-relaxed text-ink/70">Structure debt, stress operating cases, test covenants, and produce a preliminary credit memo from deterministic calculations.</p>
          <div className="mt-9 flex flex-wrap items-center gap-6"><Link href="/borrowers" className="group inline-flex h-12 items-center gap-8 rounded-[3px] bg-navy px-5 font-semibold text-white transition-colors hover:bg-ink">Start analysis <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" /></Link><Link href="/demos" className="border-b border-accent pb-1 text-sm font-semibold text-accent">Open guided workflows</Link></div>
        </div>
        <div className="relative flex items-end overflow-hidden border-t border-ink/20 bg-navy p-6 text-white lg:border-l lg:border-t-0 lg:p-10">
          <div className="absolute inset-0 opacity-15" style={{backgroundImage:"linear-gradient(#fff 1px, transparent 1px),linear-gradient(90deg,#fff 1px,transparent 1px)",backgroundSize:"48px 48px"}} />
          <div className="relative w-full border border-white/25 bg-navy/80 p-6 backdrop-blur sm:p-8">
            <div className="mb-14 flex items-center justify-between font-mono text-[10px] uppercase tracking-widest text-white/60"><span>Decision chain</span><span>4 calculation layers</span></div>
            {["Normalized statements", "Debt and interest", "Covenant stress", "Rule-based decision"].map((x, i) => <div key={x} className="flex items-center gap-4 border-t border-white/20 py-5"><span className="font-mono text-xs text-white/45">0{i+1}</span><span className="text-xl tracking-tight">{x}</span></div>)}
          </div>
        </div>
      </div>
    </section>
    <section className="mx-auto grid max-w-[1500px] border-x border-ink/15 md:grid-cols-3">
      {principles.map(({ Icon, title, body }, i) => <article key={title} className={`border-ink/15 p-8 lg:p-12 ${i < 2 ? "border-b md:border-b-0 md:border-r" : ""}`}><Icon className="mb-10 h-6 w-6 text-accent"/><h2 className="text-2xl font-semibold tracking-tight">{title}</h2><p className="mt-3 max-w-[38ch] text-sm leading-relaxed text-ink/65">{body}</p></article>)}
    </section>
    <footer className="border-t border-ink/15 px-6 py-8 text-center text-xs leading-relaxed text-ink/55">CovenantIQ is a public beta using sample borrower data. Outputs are for product demonstration and education only and do not constitute lending, investment, legal, accounting, or financial advice.</footer>
  </main>;
}
