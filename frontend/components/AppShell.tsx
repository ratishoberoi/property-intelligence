"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const agencyLinks = [
  ["Overview", "/agency"],
  ["Applicants", "/agency/applicants"],
  ["Properties", "/agency/properties"],
  ["Requests", "/agency/requests"],
  ["Matches", "/agency/applicants/A-DEMO-SARAH"],
  ["Intelligence", "/agency/intelligence"],
  ["Search", "/agency/search"],
  ["Actions", "/agency/recommendations"],
];

const clientLinks = [
  ["Home", "/client"],
  ["My Matches", "/client#matches"],
  ["Saved", "/client#saved"],
  ["Viewings", "/client#viewings"],
  ["Profile", "/client#profile"],
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isClient = pathname.startsWith("/client");
  const isAgency = pathname.startsWith("/agency") || ["/dashboard", "/applicants", "/properties", "/intelligence", "/search", "/recommendations"].some((path) => pathname.startsWith(path));
  if (!isClient && !isAgency) return <>{children}</>;
  const links = isClient ? clientLinks : agencyLinks;
  return (
    <div className={`product-shell ${isClient ? "client-shell" : "agency-shell"}`}>
      <aside className="sidebar">
        <Link href={isClient ? "/client" : "/agency"} className="brand-mark">
          <span className="brand-symbol">PI</span>
          <span><strong>Property</strong><strong>Intelligence</strong></span>
        </Link>
        <div className="role-context">{isClient ? "Your property search" : "Agency workspace"}</div>
        <nav className="nav" aria-label="Primary navigation">
          {links.map(([label, href]) => <Link href={href} key={href}>{label}</Link>)}
        </nav>
        <div className="sidebar-footer"><span className="status-dot" /> Demo · Synthetic data<Link href="/" className="exit-demo">Exit demo</Link></div>
      </aside>
      <main className="content">
        <header className="topbar">
          <div><span className="topbar-title">Property Intelligence</span><span className="topbar-context">{isClient ? "A better way to find your next home" : "Decision support for property teams"}</span></div>
          <div className="topbar-actions"><span className="environment-tag">Synthetic demo</span><Link className="role-switcher" href={isClient ? "/agency" : "/client"}>{isClient ? "Agency view" : "Client view"}</Link><div className="system-status"><span><i className="status-dot" /> {isClient ? "Live search" : "Backend"}</span><span><i className="status-dot" /> RAG</span></div></div>
        </header>
        {children}
      </main>
    </div>
  );
}
