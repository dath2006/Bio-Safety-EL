import { createFileRoute, Link } from "@tanstack/react-router";
import {
  Activity,
  ArrowRight,
  Bot,
  ClipboardCheck,
  Globe,
  ShieldCheck,
  Truck,
  Utensils,
  Beef,
  Milk,
  Store,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useEffect, useState } from "react";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "HACCP AI — Audit-ready food safety, automated" },
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

const CATEGORIES = [
  { icon: Milk, label: "Dairy & Pasteurised", color: "text-blue-500", bg: "bg-blue-500/10", border: "border-blue-500/20" },
  { icon: Beef, label: "Meat & Poultry", color: "text-red-500", bg: "bg-red-500/10", border: "border-red-500/20" },
  { icon: Utensils, label: "Ready-to-Eat (RTE)", color: "text-amber-500", bg: "bg-amber-500/10", border: "border-amber-500/20" },
  { icon: Store, label: "Street Food & Catering", color: "text-emerald-500", bg: "bg-emerald-500/10", border: "border-emerald-500/20" },
  { icon: Truck, label: "Cold Chain Storage", color: "text-cyan-500", bg: "bg-cyan-500/10", border: "border-cyan-500/20" },
];

function Landing() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  return (
    <div className="min-h-screen bg-background text-foreground overflow-hidden">
      {/* Decorative background gradients */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[500px] opacity-30 pointer-events-none">
        <div className="absolute top-[-10%] left-[20%] w-[40%] h-[60%] rounded-full bg-primary/20 blur-[100px]" />
        <div className="absolute top-[10%] right-[20%] w-[30%] h-[50%] rounded-full bg-teal-500/20 blur-[100px]" />
      </div>

      <header className="relative z-10 border-b border-border/40 bg-background/60 backdrop-blur-md sticky top-0">
        <div className="mx-auto max-w-6xl flex items-center justify-between px-6 h-16">
          <div className="flex items-center gap-2">
            <div className="h-9 w-9 rounded-md bg-gradient-to-br from-primary to-teal-500 text-primary-foreground flex items-center justify-center shadow-lg shadow-primary/20">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <span className="font-semibold tracking-tight text-lg">HACCP AI</span>
          </div>
          <nav className="hidden sm:flex items-center gap-8 text-sm font-medium text-muted-foreground">
            <a href="#features" className="hover:text-foreground transition-colors">Features</a>
            <a href="#categories" className="hover:text-foreground transition-colors">Supported Categories</a>
            <a href="#how" className="hover:text-foreground transition-colors">How it works</a>
          </nav>
          <Link to="/dashboard/chat">
            <Button size="sm" className="rounded-full px-5 shadow-lg shadow-primary/20 transition-transform hover:scale-105">
              Open dashboard <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
          </Link>
        </div>
      </header>

      <main className="relative z-10">
        {/* Hero Section */}
        <section className="mx-auto max-w-6xl px-6 pt-24 pb-20 text-center">
          <div className={cn("transition-all duration-700 delay-100", mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4")}>
            <span className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-xs font-medium text-primary shadow-sm">
              <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
              FSSAI Schedule 4 · Codex Alimentarius
            </span>
          </div>
          
          <h1 className={cn("mt-8 text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-balance transition-all duration-700 delay-200", mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4")}>
            Audit-ready HACCP plans,
            <span className="block mt-2 bg-gradient-to-r from-primary via-teal-500 to-emerald-400 bg-clip-text text-transparent pb-2">
              co-authored with AI.
            </span>
          </h1>
          
          <p className={cn("mx-auto mt-6 max-w-2xl text-lg text-muted-foreground leading-relaxed transition-all duration-700 delay-300", mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4")}>
            Generate hazard analyses, determine CCPs via the Codex decision tree,
            and monitor critical limits in real time — with human-in-the-loop
            review at every regulated gate.
          </p>
          
          <div className={cn("mt-10 flex flex-col sm:flex-row items-center justify-center gap-4 transition-all duration-700 delay-400", mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4")}>
            <Link to="/dashboard/plan-builder">
              <Button size="lg" className="h-12 px-8 rounded-full text-base shadow-xl shadow-primary/20 hover:scale-105 transition-transform w-full sm:w-auto">
                Start a HACCP plan
              </Button>
            </Link>
            <Link to="/dashboard/chat">
              <Button size="lg" variant="outline" className="h-12 px-8 rounded-full text-base border-border/60 bg-background/50 backdrop-blur-sm hover:bg-muted w-full sm:w-auto">
                Try regulatory chat
              </Button>
            </Link>
          </div>
        </section>

        {/* Categories Grid */}
        <section id="categories" className="mx-auto max-w-6xl px-6 py-12">
          <div className="text-center mb-10">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Supported Product Categories</h2>
          </div>
          <div className="flex flex-wrap justify-center gap-4">
            {CATEGORIES.map((cat, i) => (
              <div 
                key={cat.label}
                className={cn(
                  "flex items-center gap-3 px-5 py-3 rounded-2xl border transition-all duration-500 hover:-translate-y-1 hover:shadow-lg",
                  cat.bg, cat.border, mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
                )}
                style={{ transitionDelay: `${500 + i * 100}ms` }}
              >
                <cat.icon className={cn("h-5 w-5", cat.color)} />
                <span className="font-medium text-sm">{cat.label}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="mx-auto max-w-6xl px-6 py-24">
          <div className="grid gap-6 sm:grid-cols-3">
            {FEATURES.map((f, i) => (
              <div
                key={f.title}
                className={cn(
                  "group rounded-2xl border border-border/50 bg-card/50 backdrop-blur-sm p-8 transition-all duration-500 hover:shadow-xl hover:shadow-primary/5 hover:border-primary/20",
                  mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
                )}
                style={{ transitionDelay: `${700 + i * 150}ms` }}
              >
                <div className="h-12 w-12 rounded-xl bg-primary/10 text-primary flex items-center justify-center mb-6 group-hover:scale-110 group-hover:bg-primary group-hover:text-primary-foreground transition-all duration-300">
                  <f.icon className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-semibold tracking-tight">{f.title}</h3>
                <p className="mt-3 text-sm text-muted-foreground leading-relaxed">{f.body}</p>
              </div>
            ))}
          </div>
        </section>

        {/* How It Works Mini-dashboard */}
        <section id="how" className="border-t border-border/40 bg-gradient-to-b from-card/30 to-background">
          <div className="mx-auto max-w-6xl px-6 py-24 grid gap-12 lg:grid-cols-2 items-center">
            <div className={cn("transition-all duration-700 delay-300", mounted ? "opacity-100 translate-x-0" : "opacity-0 -translate-x-8")}>
              <h2 className="text-3xl font-bold tracking-tight">
                Built for modern food operators
              </h2>
              <p className="mt-4 text-lg text-muted-foreground leading-relaxed">
                Map your process steps, let the agent draft a complete HACCP plan,
                and approve each principle through a guided review. Every claim is
                grounded in FSSAI or Codex citations.
              </p>
              
              <ul className="mt-8 space-y-4">
                {["Human-in-the-loop review gates", "Automatic PDF report generation", "Live compliance scoring"].map((item, i) => (
                  <li key={item} className="flex items-center gap-3 text-sm font-medium">
                    <div className="h-6 w-6 rounded-full bg-success/15 text-success flex items-center justify-center">
                      <ShieldCheck className="h-3.5 w-3.5" />
                    </div>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            
            <div className={cn("relative rounded-2xl border border-border/50 bg-background/80 backdrop-blur-xl p-8 shadow-2xl transition-all duration-700 delay-500", mounted ? "opacity-100 translate-x-0" : "opacity-0 translate-x-8")}>
              {/* Decorative browser dots */}
              <div className="flex gap-1.5 mb-6">
                <div className="w-3 h-3 rounded-full bg-destructive/50" />
                <div className="w-3 h-3 rounded-full bg-warning/50" />
                <div className="w-3 h-3 rounded-full bg-success/50" />
              </div>
              
              <div className="space-y-6">
                <div className="flex items-center justify-between border-b border-border/50 pb-4">
                  <div>
                    <h4 className="font-semibold">CCP-1 · Pasteurizer</h4>
                    <p className="text-xs text-muted-foreground mt-1">Biological hazard control</p>
                  </div>
                  <div className="px-3 py-1 rounded-full bg-success/10 text-success text-xs font-semibold border border-success/20">
                    In Control
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Current Temperature</span>
                    <span className="font-medium text-success flex items-center gap-1">
                      73.5°C <Activity className="h-3 w-3" />
                    </span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-muted overflow-hidden relative">
                    <div className="absolute left-0 top-0 bottom-0 w-[85%] bg-gradient-to-r from-success/80 to-success rounded-full" />
                    <div className="absolute left-[75%] top-0 bottom-0 w-0.5 bg-foreground/20" /> {/* Critical limit marker */}
                  </div>
                  <div className="flex justify-between text-[10px] text-muted-foreground">
                    <span>Target: 72.0°C</span>
                    <span>Limit: ≥ 72.0°C</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-border/40 bg-card/30">
        <div className="mx-auto max-w-6xl px-6 py-8 text-xs text-muted-foreground flex flex-col sm:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4" />
            <span>© {new Date().getFullYear()} HACCP AI System</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="hover:text-foreground cursor-pointer transition-colors">Privacy</span>
            <span className="hover:text-foreground cursor-pointer transition-colors">Terms</span>
            <span className="px-2 py-1 rounded-md bg-muted text-[10px] font-medium">Indian FSSAI · Codex Aligned</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
