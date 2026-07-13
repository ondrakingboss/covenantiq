import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "CovenantIQ | Deterministic private-credit analysis",
  description: "Educational private-credit analysis with traceable debt, covenant, sensitivity, and recommendation calculations.",
};

function Mark() { return <span className="grid h-8 w-8 place-items-center border border-current font-mono text-[10px] font-bold">CIQ</span>; }

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body className="font-sans antialiased">
    <header className="no-print sticky top-0 z-50 border-b border-ink/20 bg-paper">
      <nav className="mx-auto flex h-16 max-w-[1500px] items-center justify-between px-5 lg:px-8">
        <Link href="/" className="flex items-center gap-3"><Mark /><span className="font-semibold tracking-tight">CovenantIQ</span></Link>
        <div className="flex items-center gap-4 text-sm sm:gap-5"><Link href="/demos" className="hover:text-accent">Demo</Link><Link href="/borrowers" className="hover:text-accent">Borrowers</Link><Link href="/analyses" className="hidden hover:text-accent sm:inline">Saved analyses</Link><span className="hidden font-mono text-[10px] text-ink/55 lg:inline">EDUCATIONAL CREDIT MODEL</span></div>
      </nav>
    </header>{children}
  </body></html>;
}
