import { createFileRoute, Link } from "@tanstack/react-router";
import {
  Activity,
  ArrowRight,
  Bot,
  ClipboardCheck,
  Globe,
  ShieldCheck,
} from "lucide-react";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      {
        title: "HACCP AI — Audit-ready food safety, automated",
      },
      {
        name: "description",
        content:
          "AI-powered HACCP documentation and FSSAI / Codex compliance. Build audit-ready plans, monitor CCPs in real time, and stay ahead of regulatory change.",
      },
      { property: "og:title", content: "HACCP AI — Food safety, automated" },
      {
        property: "og:description",
        content:
          "Build audit-ready HACCP plans with human-in-the-loop review, real-time CCP monitoring, and proactive regulatory alerts.",
      },
    ],
  }),
  component: Landing,
});

const FEATURES = [
  {
    icon: Bot,
    title: "Automated hazard trees",
    body: "AI generates hazard matrices for your exact process, scored on likelihood × severity, with FSSAI citations.",
  },
  {
    icon: ClipboardCheck,
    title: "Codex-based CCPs",
    body: "Step-by-step decision tree determines critical control points. You stay in control with one-click overrides.",
  },
  {
    icon: Globe,
    title: "FSSAI live monitoring",
    body: "A web-search agent tracks Indian regulatory changes and flags plans affected by amendments.",
  },
];

function Landing() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border">
        <div className="mx-auto max-w-6xl flex items-center justify-between px-6 h-16">
          <div className="flex items-center gap-2">
            <div className="h-9 w-9 rounded-md bg-primary text-primary-foreground flex items-center justify-center">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <span className="font-semibold tracking-tight">HACCP AI</span>
          </div>
          <nav className="hidden sm:flex items-center gap-6 text-sm text-muted-foreground">
            <a href="#features" className="hover:text-foreground">Features</a>
            <a href="#how" className="hover:text-foreground">How it works</a>
          </nav>
          <Link to="/dashboard/chat">
            <Button size="sm">
              Open dashboard <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
          </Link>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-6 pt-20 pb-16 text-center">
        <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs text-muted-foreground">
          <span className="h-1.5 w-1.5 rounded-full bg-success" />
          FSSAI Schedule 4 · Codex Alimentarius
        </span>
        <h1 className="mt-6 text-4xl sm:text-5xl font-semibold tracking-tight">
          Audit-ready HACCP plans,
          <span className="block text-primary">co-authored with AI.</span>
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-muted-foreground">
          Generate hazard analyses, determine CCPs via the Codex decision tree,
          and monitor critical limits in real time — with human-in-the-loop
          review at every regulated gate.
        </p>
        <div className="mt-8 flex items-center justify-center gap-3">
          <Link to="/dashboard/plan-builder">
            <Button size="lg">Start a HACCP plan</Button>
          </Link>
          <Link to="/dashboard/chat">
            <Button size="lg" variant="outline">
              Try regulatory chat
            </Button>
          </Link>
        </div>
      </section>

      <section id="features" className="mx-auto max-w-6xl px-6 pb-24">
        <div className="grid gap-5 sm:grid-cols-3">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="rounded-xl border border-border bg-card p-6 transition hover:shadow-md hover:-translate-y-0.5"
            >
              <div className="h-10 w-10 rounded-md bg-accent text-accent-foreground flex items-center justify-center">
                <f.icon className="h-5 w-5" />
              </div>
              <h3 className="mt-4 font-semibold">{f.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="how" className="border-t border-border bg-card">
        <div className="mx-auto max-w-6xl px-6 py-16 grid gap-8 sm:grid-cols-2">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight">
              Built for food business operators
            </h2>
            <p className="mt-3 text-muted-foreground">
              Map your process steps, let the agent draft a complete HACCP plan,
              and approve each principle through a guided review. Every claim is
              grounded in FSSAI or Codex citations.
            </p>
          </div>
          <div className="rounded-xl border border-border bg-background p-6">
            <div className="flex items-center gap-3 text-sm">
              <Activity className="h-4 w-4 text-success" />
              CCP-1 · Pasteurizer temperature
              <span className="ml-auto text-success">≥ 72°C</span>
            </div>
            <div className="mt-3 h-1.5 w-full rounded-full bg-muted overflow-hidden">
              <div className="h-full w-[88%] bg-success" />
            </div>
            <div className="mt-4 text-xs text-muted-foreground">
              Compliance score · 88%
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t border-border">
        <div className="mx-auto max-w-6xl px-6 py-6 text-xs text-muted-foreground flex justify-between">
          <span>© {new Date().getFullYear()} HACCP AI</span>
          <span>Indian FSSAI · Codex Alimentarius aligned</span>
        </div>
      </footer>
    </div>
  );
}
