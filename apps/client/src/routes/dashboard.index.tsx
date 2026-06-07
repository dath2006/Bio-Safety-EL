import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Plus,
  Search,
  Database,
  Sparkles,
  CheckCircle2,
  FileText,
  Layout,
  Loader2,
  TrendingUp,
  ShieldCheck,
  Zap,
} from "lucide-react";
import { api } from "@/lib/haccp/api";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/dashboard/")({
  component: DashboardOverview,
});

function DashboardOverview() {
  const [stats, setStats] = useState({
    total_plans: 0,
    active_plans: 0,
    completed_plans: 0,
    rag_chunks: 0,
    categories_covered: 11,
  });
  const [recentPlans, setRecentPlans] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [ingestResult, setIngestResult] = useState<string | null>(null);

  async function loadData() {
    setLoading(true);
    try {
      const statsData = await api.stats();
      setStats(statsData);
      
      const plansList = await api.listPlans();
      setRecentPlans(plansList.slice(0, 5));
    } catch (e) {
      console.error("Failed to load dashboard data:", e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleIngest() {
    setIngesting(true);
    setIngestResult(null);
    try {
      const res = await api.ingest();
      setIngestResult(
        `Ingested ${res.documents_processed} documents (${res.chunks_created} chunks successfully)`
      );
      // Reload stats to reflect new chunks
      const statsData = await api.stats();
      setStats(statsData);
    } catch (e) {
      setIngestResult("Ingestion failed: " + (e as Error).message);
    } finally {
      setIngesting(false);
    }
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-primary to-teal-500 bg-clip-text text-transparent">
            HACCP Control Center
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Real-time compliance intelligence, hazard analysis, and RAG-grounded regulatory checks.
          </p>
        </div>
        <div className="flex gap-2">
          <Button asChild className="cursor-pointer">
            <Link to="/dashboard/plan-builder">
              <Plus className="h-4 w-4 mr-2" /> New HACCP Plan
            </Link>
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Plans */}
        <div className="rounded-xl border border-border bg-card p-5 relative overflow-hidden transition-all hover:shadow-md hover:border-primary/40 group">
          <div className="absolute right-3 top-3 h-12 w-12 rounded-lg bg-primary/5 flex items-center justify-center text-primary transition-colors group-hover:bg-primary/10">
            <Layout className="h-6 w-6" />
          </div>
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Total Plans
          </div>
          <div className="text-3xl font-bold mt-2">
            {loading ? <Loader2 className="h-8 w-8 animate-spin" /> : stats.total_plans}
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            {stats.active_plans} active · {stats.completed_plans} completed
          </p>
        </div>

        {/* Active Plans */}
        <div className="rounded-xl border border-border bg-card p-5 relative overflow-hidden transition-all hover:shadow-md hover:border-teal-500/40 group">
          <div className="absolute right-3 top-3 h-12 w-12 rounded-lg bg-teal-500/5 flex items-center justify-center text-teal-500 transition-colors group-hover:bg-teal-500/10">
            <TrendingUp className="h-6 w-6" />
          </div>
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Active Drafts
          </div>
          <div className="text-3xl font-bold mt-2">
            {loading ? <Loader2 className="h-8 w-8 animate-spin" /> : stats.active_plans}
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Awaiting human-in-the-loop review
          </p>
        </div>

        {/* Completed Plans */}
        <div className="rounded-xl border border-border bg-card p-5 relative overflow-hidden transition-all hover:shadow-md hover:border-success/40 group">
          <div className="absolute right-3 top-3 h-12 w-12 rounded-lg bg-success/5 flex items-center justify-center text-success transition-colors group-hover:bg-success/10">
            <CheckCircle2 className="h-6 w-6" />
          </div>
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Completed Plans
          </div>
          <div className="text-3xl font-bold mt-2">
            {loading ? <Loader2 className="h-8 w-8 animate-spin" /> : stats.completed_plans}
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Fully certified and ready for audit
          </p>
        </div>

        {/* RAG Chunks */}
        <div className="rounded-xl border border-border bg-card p-5 relative overflow-hidden transition-all hover:shadow-md hover:border-indigo-500/40 group">
          <div className="absolute right-3 top-3 h-12 w-12 rounded-lg bg-indigo-500/5 flex items-center justify-center text-indigo-500 transition-colors group-hover:bg-indigo-500/10">
            <Database className="h-6 w-6" />
          </div>
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Regulatory Knowledge
          </div>
          <div className="text-3xl font-bold mt-2">
            {loading ? <Loader2 className="h-8 w-8 animate-spin" /> : stats.rag_chunks}
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Across {stats.categories_covered} food categories
          </p>
        </div>
      </div>

      <div className="grid lg:grid-cols-[1fr_360px] gap-6">
        {/* Recent Plans Table */}
        <div className="rounded-xl border border-border bg-card p-5 space-y-4">
          <div>
            <h3 className="font-semibold text-base">Recent HACCP Plans</h3>
            <p className="text-xs text-muted-foreground">
              Overview of recently created process evaluations.
            </p>
          </div>

          {recentPlans.length === 0 ? (
            <div className="h-[200px] flex flex-col items-center justify-center text-center p-4">
              <FileText className="h-8 w-8 text-muted-foreground mb-2" />
              <p className="text-sm font-medium">No plans found</p>
              <p className="text-xs text-muted-foreground mt-1">
                Get started by generating your first plan.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b border-border text-xs text-muted-foreground uppercase font-medium">
                    <th className="pb-3">Business</th>
                    <th className="pb-3">Category</th>
                    <th className="pb-3">Status</th>
                    <th className="pb-3">Current Stage</th>
                    <th className="pb-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {recentPlans.map((p) => (
                    <tr key={p.plan_id} className="hover:bg-muted/30 transition-colors">
                      <td className="py-3.5 font-medium">{p.business_name}</td>
                      <td className="py-3.5 text-muted-foreground">{p.product_category}</td>
                      <td className="py-3.5">
                        <span
                          className={cn(
                            "inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium border",
                            p.status === "complete"
                              ? "bg-success/15 text-success border-success/30"
                              : p.status === "in_progress"
                              ? "bg-warning/15 text-warning-foreground border-warning/30"
                              : "bg-muted text-muted-foreground border-border"
                          )}
                        >
                          {p.status === "complete" ? "Complete" : p.status === "in_progress" ? "In Progress" : "Draft"}
                        </span>
                      </td>
                      <td className="py-3.5 text-xs text-muted-foreground">{p.current_stage}</td>
                      <td className="py-3.5 text-right">
                        <Button variant="ghost" size="sm" asChild className="cursor-pointer">
                          <Link to="/dashboard/plan-builder">
                            Open
                          </Link>
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Quick Actions Panel */}
        <div className="space-y-4">
          <div className="rounded-xl border border-border bg-card p-5 space-y-4">
            <div>
              <h3 className="font-semibold text-base">Quick Actions</h3>
              <p className="text-xs text-muted-foreground">
                Speed up your compliance workflows.
              </p>
            </div>

            <div className="flex flex-col gap-2.5">
              {/* Build Plan */}
              <Button variant="outline" asChild className="w-full justify-start cursor-pointer group">
                <Link to="/dashboard/plan-builder">
                  <Plus className="h-4 w-4 mr-3 text-primary transition-transform group-hover:scale-110" />
                  <div className="text-left">
                    <div className="font-medium text-xs">Plan Generator</div>
                    <div className="text-[10px] text-muted-foreground">Run interactive HACCP intake</div>
                  </div>
                </Link>
              </Button>

              {/* Chat */}
              <Button variant="outline" asChild className="w-full justify-start cursor-pointer group">
                <Link to="/dashboard/chat">
                  <Search className="h-4 w-4 mr-3 text-teal-500 transition-transform group-hover:scale-110" />
                  <div className="text-left">
                    <div className="font-medium text-xs">Search Regulations</div>
                    <div className="text-[10px] text-muted-foreground">Ask questions about FSSAI standards</div>
                  </div>
                </Link>
              </Button>

              {/* Ingest */}
              <Button
                variant="outline"
                className="w-full justify-start cursor-pointer group"
                disabled={ingesting}
                onClick={handleIngest}
              >
                {ingesting ? (
                  <Loader2 className="h-4 w-4 mr-3 animate-spin text-indigo-500" />
                ) : (
                  <Database className="h-4 w-4 mr-3 text-indigo-500 transition-transform group-hover:scale-110" />
                )}
                <div className="text-left">
                  <div className="font-medium text-xs">Run Document Ingest</div>
                  <div className="text-[10px] text-muted-foreground">Populate vector database from sources</div>
                </div>
              </Button>
            </div>

            {ingestResult && (
              <div
                className={cn(
                  "rounded-md border p-3 text-[11px]",
                  ingestResult.includes("failed")
                    ? "border-destructive/20 bg-destructive/5 text-destructive"
                    : "border-success/20 bg-success/5 text-success"
                )}
              >
                {ingestResult}
              </div>
            )}
          </div>

          {/* RAG Feed Banner */}
          <div className="rounded-xl border border-primary/20 bg-gradient-to-br from-primary/5 to-teal-500/5 p-5 relative overflow-hidden">
            <div className="absolute -right-6 -bottom-6 opacity-10">
              <ShieldCheck className="h-32 w-32" />
            </div>
            <h4 className="font-bold text-sm flex items-center gap-1.5 text-primary">
              <Zap className="h-4 w-4 text-teal-500" /> Grounded compliance
            </h4>
            <p className="text-xs text-muted-foreground mt-2 leading-relaxed">
              Every critical limit and corrective action is retrieved directly from our RAG vector storage index of active Codex and FSSAI standards.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}