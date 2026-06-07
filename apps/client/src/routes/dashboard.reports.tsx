import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Download, FileText, Loader2 } from "lucide-react";
import { api } from "@/lib/haccp/api";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/dashboard/reports")({
  component: ReportsPage,
});

function ReportsPage() {
  const [plans, setPlans] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [ready, setReady] = useState<Record<string, boolean>>({});

  async function loadPlans() {
    setLoading(true);
    try {
      const list = await api.listPlans();
      setPlans(list);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPlans();
  }, []);

  async function generate(id: string) {
    setBusy(id);
    try {
      await api.generatePdf(id);
      setReady((r) => ({ ...r, [id]: true }));
    } catch (e) {
      alert("Failed to generate PDF: " + (e as Error).message);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-border bg-card p-5">
        <h3 className="font-semibold">Generated plans</h3>
        <p className="text-xs text-muted-foreground">
          Audit-ready PDFs and JSON exports for every HACCP plan you've built.
        </p>
      </div>

      {loading && plans.length === 0 ? (
        <div className="flex items-center justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : plans.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border bg-card p-10 text-center text-sm text-muted-foreground">
          No plans yet. Build one in the <strong>Plan Builder</strong> first.
        </div>
      ) : null}

      <div className="space-y-3">
        {plans.map((p) => (
          <div
            key={p.plan_id}
            className="rounded-xl border border-border bg-card p-5 flex items-center gap-4"
          >
            <div className="h-10 w-10 rounded-md bg-accent text-accent-foreground flex items-center justify-center">
              <FileText className="h-5 w-5" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-medium truncate">
                {p.business_name} · {p.product_category}
              </div>
              <div className="text-xs text-muted-foreground">
                Stage: {p.current_stage} · {p.ccps_approved.length} CCPs
              </div>
            </div>
            <span className="text-[11px] px-2 py-0.5 rounded-full border border-border bg-background text-muted-foreground">
              {p.current_stage === "completed" ? "complete" : "in progress"}
            </span>
            {ready[p.plan_id] ? (
              <a href={api.pdfUrl(p.plan_id)} target="_blank" rel="noreferrer">
                <Button size="sm">
                  <Download className="h-4 w-4 mr-1" /> Download PDF
                </Button>
              </a>
            ) : (
              <Button
                size="sm"
                variant="outline"
                disabled={busy === p.plan_id}
                onClick={() => generate(p.plan_id)}
              >
                {busy === p.plan_id ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-1" />
                ) : null}
                Generate PDF
              </Button>
            )}
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                const blob = new Blob([JSON.stringify(p, null, 2)], {
                  type: "application/json",
                });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `${p.plan_id}.json`;
                a.click();
                URL.revokeObjectURL(url);
              }}
            >
              JSON
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}