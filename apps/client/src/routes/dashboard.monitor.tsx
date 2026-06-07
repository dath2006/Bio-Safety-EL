import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  AlertTriangle,
  CheckCircle2,
  Plus,
  Loader2,
  Download,
  Activity,
  ThermometerSun,
} from "lucide-react";
import { api } from "@/lib/haccp/api";
import type { MonitoringLog } from "@/lib/haccp/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export const Route = createFileRoute("/dashboard/monitor")({
  component: MonitorPage,
});

function MonitorPage() {
  const [plans, setPlans] = useState<any[]>([]);
  const [planId, setPlanId] = useState<string>("");
  const [ccps, setCcps] = useState<any[]>([]);
  const [selected, setSelected] = useState<any | null>(null);
  const [logs, setLogs] = useState<MonitoringLog[]>([]);
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [lastDeviation, setLastDeviation] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // 1. Fetch plans list on mount
  useEffect(() => {
    async function loadPlans() {
      setLoading(true);
      try {
        const list = await api.listPlans();
        setPlans(list);
        if (list.length > 0) {
          setPlanId(list[0].plan_id);
        }
      } catch (e) {
        console.error("Failed to load plans:", e);
      } finally {
        setLoading(false);
      }
    }
    loadPlans();
  }, []);

  // 2. Fetch plan state (CCPs) and logs when planId changes
  useEffect(() => {
    if (!planId) return;
    async function loadPlanData() {
      setLoading(true);
      try {
        const planState = await api.getPlan(planId);
        const builtCcps = planState.ccps_approved.map((c: any) => {
          const key = `${c.process_step} - ${c.hazard_name}`;
          const lim = planState.critical_limits[key] || {};
          return {
            hazard: key,
            parameter: lim.parameter || "Control Parameter",
            unit: lim.unit || "",
            min: lim.min_value ?? null,
            max: lim.max_value ?? null,
          };
        });
        setCcps(builtCcps);
        if (builtCcps.length > 0) {
          setSelected(builtCcps[0]);
        } else {
          setSelected(null);
        }
        const logsRes = await api.getLogs(planId);
        setLogs(logsRes.logs);
      } catch (e) {
        console.error("Failed to load plan details:", e);
      } finally {
        setLoading(false);
      }
    }
    loadPlanData();
  }, [planId]);

  async function refresh() {
    if (!planId) return;
    const r = await api.getLogs(planId);
    setLogs(r.logs);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!value || !selected || !planId) return;
    setBusy(true);
    try {
      const r = await api.logMonitoring(
        planId,
        {
          ccp_hazard: selected.hazard,
          parameter: selected.parameter,
          value: Number(value),
          unit: selected.unit,
          monitored_by: "QA",
        },
        { min: selected.min, max: selected.max },
      );
      setLastDeviation(r.corrective_action_required);
      setValue("");
      await refresh();
    } catch (err) {
      alert("Failed to submit reading: " + (err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  function exportCsv() {
    const header = "CCP Hazard,Parameter,Value,Unit,Timestamp,Deviation\n";
    const rows = logs
      .map(
        (l) =>
          `"${l.ccp_hazard}","${l.parameter}",${l.value},"${l.unit ?? ""}","${l.timestamp}",${l.is_deviation}`,
      )
      .join("\n");
    const blob = new Blob([header + rows], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ccp_monitoring_${planId}_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const chartData = useMemo(
    () =>
      logs
        .filter((l) => selected && l.ccp_hazard === selected.hazard)
        .map((l) => ({
          time: new Date(l.timestamp).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
          value: l.value,
        })),
    [logs, selected],
  );

  // Per-CCP status summary
  const ccpStatus = useMemo(() => {
    return ccps.map((c) => {
      const ccpLogs = [...logs].filter((l) => l.ccp_hazard === c.hazard);
      const last = ccpLogs[ccpLogs.length - 1];
      return {
        ...c,
        isDeviating: last?.is_deviation ?? false,
        lastValue: last ? `${last.value} ${c.unit}` : "—",
        readingCount: ccpLogs.length,
      };
    });
  }, [ccps, logs]);

  if (loading && plans.length === 0) {
    return (
      <div className="h-[400px] flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (plans.length === 0) {
    return (
      <div className="h-[400px] flex flex-col items-center justify-center text-center p-6 bg-card rounded-xl border border-border">
        <AlertTriangle className="h-12 w-12 text-warning-foreground mb-4" />
        <h3 className="font-semibold text-lg">No active plans found</h3>
        <p className="text-sm text-muted-foreground max-w-sm mt-1">
          Please complete your first plan in the Plan Builder before starting CCP monitoring.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-primary to-teal-500 bg-clip-text text-transparent">
            CCP Monitoring Dashboard
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Real-time operational tracking for each Critical Control Point.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={exportCsv}
          disabled={logs.length === 0}
          className="gap-2 cursor-pointer"
          id="export-csv-btn"
        >
          <Download className="h-4 w-4" />
          Export CSV
        </Button>
      </div>

      {/* Plan Selector */}
      <div className="flex items-center gap-4 bg-card p-4 rounded-xl border border-border">
        <label className="text-sm font-medium text-muted-foreground">Active Plan:</label>
        <Select value={planId} onValueChange={setPlanId}>
          <SelectTrigger className="w-72 bg-background border-border">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {plans.map((p) => (
              <SelectItem key={p.plan_id} value={p.plan_id}>
                {p.business_name} ({p.product_category})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {loading && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
      </div>

      {/* Multi-CCP Overview Summary */}
      {ccpStatus.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="h-4 w-4 text-primary" />
            <h3 className="font-semibold text-sm">All CCPs at a Glance</h3>
            <span className="ml-auto text-xs text-muted-foreground">
              {ccpStatus.filter((c) => c.isDeviating).length} deviating ·{" "}
              {ccpStatus.filter((c) => !c.isDeviating).length} in control
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {ccpStatus.map((c) => (
              <button
                key={c.hazard}
                onClick={() => setSelected(c)}
                className={cn(
                  "flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-medium transition-all cursor-pointer",
                  c.isDeviating
                    ? "border-destructive/40 bg-destructive/5 text-destructive"
                    : "border-success/30 bg-success/5 text-success",
                  selected?.hazard === c.hazard && "ring-2 ring-primary/30",
                )}
              >
                {c.isDeviating ? (
                  <AlertTriangle className="h-3 w-3 animate-pulse" />
                ) : (
                  <CheckCircle2 className="h-3 w-3" />
                )}
                {c.hazard.split(" - ")[0]}
                <span className="text-muted-foreground font-normal ml-1">
                  {c.lastValue}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      {planId && ccps.length === 0 && !loading && (
        <div className="h-[200px] flex flex-col items-center justify-center text-center p-6 bg-card rounded-xl border border-border">
          <CheckCircle2 className="h-10 w-10 text-muted-foreground mb-3 opacity-40" />
          <h3 className="font-semibold">No CCPs defined for this plan</h3>
          <p className="text-sm text-muted-foreground max-w-sm mt-1">
            This plan does not have any approved Critical Control Points.
          </p>
        </div>
      )}

      {/* CCP Cards */}
      {ccps.length > 0 && (
        <div className="grid md:grid-cols-2 gap-4">
          {ccpStatus.map((c) => {
            const deviating = c.isDeviating;
            return (
              <button
                key={c.hazard}
                onClick={() => setSelected(c)}
                className={cn(
                  "text-left rounded-xl border bg-card p-5 transition-all cursor-pointer",
                  selected && selected.hazard === c.hazard
                    ? "border-primary ring-2 ring-primary/20"
                    : "border-border hover:border-primary/40",
                )}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-xs text-muted-foreground">{c.parameter}</div>
                    <div className="font-semibold mt-1 text-sm">{c.hazard}</div>
                  </div>
                  <span
                    className={cn(
                      "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] border",
                      deviating
                        ? "bg-destructive/15 text-destructive border-destructive/30 animate-pulse"
                        : "bg-success/15 text-success border-success/30",
                    )}
                  >
                    {deviating ? (
                      <AlertTriangle className="h-3 w-3" />
                    ) : (
                      <CheckCircle2 className="h-3 w-3" />
                    )}
                    {deviating ? "Deviation" : "In control"}
                  </span>
                </div>
                <div className="mt-3 text-sm flex items-center gap-3 flex-wrap">
                  <span>
                    Last:{" "}
                    <span className="font-medium">{c.lastValue}</span>
                  </span>
                  <span className="text-muted-foreground text-xs">
                    Limit: {c.min != null ? `≥ ${c.min}` : ""}
                    {c.max != null ? ` ≤ ${c.max}` : ""} {c.unit}
                  </span>
                  <span className="ml-auto text-xs text-muted-foreground">
                    {c.readingCount} readings
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      )}

      {selected && (
        <div className="grid lg:grid-cols-[1fr_320px] gap-6">
          {/* Trend Chart */}
          <div className="rounded-xl border border-border bg-card p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-semibold flex items-center gap-2">
                  <ThermometerSun className="h-4 w-4 text-primary" />
                  {selected.parameter} trend
                </h3>
                <p className="text-xs text-muted-foreground">{selected.hazard}</p>
              </div>
              {chartData.length === 0 && (
                <span className="text-xs text-muted-foreground">No readings yet</span>
              )}
            </div>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                  <XAxis dataKey="time" stroke="var(--color-muted-foreground)" />
                  <YAxis stroke="var(--color-muted-foreground)" />
                  <Tooltip />
                  <Legend />
                  {selected.min != null && (
                    <ReferenceLine
                      y={selected.min}
                      stroke="var(--color-destructive)"
                      strokeDasharray="4 4"
                      label={{
                        value: `Min ${selected.min}`,
                        fill: "var(--color-destructive)",
                        fontSize: 11,
                      }}
                    />
                  )}
                  {selected.max != null && (
                    <ReferenceLine
                      y={selected.max}
                      stroke="var(--color-destructive)"
                      strokeDasharray="4 4"
                      label={{
                        value: `Max ${selected.max}`,
                        fill: "var(--color-destructive)",
                        fontSize: 11,
                      }}
                    />
                  )}
                  <Line
                    type="monotone"
                    dataKey="value"
                    name={`${selected.parameter} (${selected.unit})`}
                    stroke="var(--color-primary)"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    activeDot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="space-y-4">
            {/* Record Measurement */}
            <form
              onSubmit={submit}
              className="rounded-xl border border-border bg-card p-5 space-y-3"
            >
              <h3 className="font-semibold flex items-center gap-2">
                <Plus className="h-4 w-4" /> Record measurement
              </h3>
              <div className="text-xs text-muted-foreground">
                {selected.parameter} ({selected.unit})
              </div>
              <Input
                type="number"
                step="0.1"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder="e.g. 73.5"
                required
                id="ccp-value-input"
              />
              <Button type="submit" disabled={busy} className="w-full" id="submit-reading-btn">
                {busy && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
                Submit reading
              </Button>
            </form>

            {lastDeviation && (
              <div className="rounded-xl border border-destructive/40 bg-destructive/10 p-4 text-sm">
                <div className="flex items-center gap-2 font-medium text-destructive">
                  <AlertTriangle className="h-4 w-4" /> Deviation triggered
                </div>
                <p className="mt-2 text-destructive/90">{lastDeviation}</p>
                <Button
                  size="sm"
                  variant="outline"
                  className="mt-3"
                  onClick={() => setLastDeviation(null)}
                >
                  Close out corrective action
                </Button>
              </div>
            )}

            {/* Recent Logs */}
            <div className="rounded-xl border border-border bg-card p-5">
              <h3 className="font-semibold mb-3">Recent logs</h3>
              <div className="space-y-2 max-h-72 overflow-y-auto pr-1 text-xs">
                {[...logs]
                  .reverse()
                  .slice(0, 12)
                  .map((l, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between border-b border-border pb-1 last:border-0"
                    >
                      <span className="text-muted-foreground">
                        {new Date(l.timestamp).toLocaleString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                          month: "short",
                          day: "numeric",
                        })}
                      </span>
                      <span
                        className={cn(
                          "font-medium",
                          l.is_deviation ? "text-destructive" : "text-foreground",
                        )}
                      >
                        {l.value} {l.unit ?? ""}
                        {l.is_deviation && (
                          <AlertTriangle className="h-3 w-3 inline ml-1" />
                        )}
                      </span>
                    </div>
                  ))}
                {logs.length === 0 && (
                  <p className="text-muted-foreground text-center py-4">No readings recorded yet.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}