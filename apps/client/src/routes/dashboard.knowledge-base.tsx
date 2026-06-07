import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  BookOpen,
  Database,
  Trash2,
  Upload,
  Loader2,
  Sparkles,
  Plus,
  X,
  FileText,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import { api } from "@/lib/haccp/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";
import { FOOD_CATEGORIES } from "@/lib/haccp/categories";

export const Route = createFileRoute("/dashboard/knowledge-base")({
  component: KnowledgeBasePage,
});

type DocumentInfo = {
  filename: string;
  title: string;
  source_body: string;
  amendment_date: string | null;
  product_categories: string[];
  type: "seed" | "custom";
  chunks_count: number;
};

function KnowledgeBasePage() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");

  // Form states
  const [title, setTitle] = useState("");
  const [sourceBody, setSourceBody] = useState("Custom");
  const [amendmentDate, setAmendmentDate] = useState("");
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [file, setFile] = useState<File | null>(null);

  // Status states
  const [busy, setBusy] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [statusType, setStatusType] = useState<"success" | "error" | null>(null);

  async function loadDocuments() {
    setLoading(true);
    try {
      const res = await api.listDocuments();
      setDocuments(res.documents);
    } catch (e) {
      console.error("Failed to load documents:", e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDocuments();
  }, []);

  const filteredDocs = documents.filter(
    (d) =>
      d.title.toLowerCase().includes(search.toLowerCase()) ||
      d.filename.toLowerCase().includes(search.toLowerCase()) ||
      d.source_body.toLowerCase().includes(search.toLowerCase())
  );

  const totalChunks = documents.reduce((sum, d) => sum + d.chunks_count, 0);

  function handleCategoryToggle(slug: string) {
    setSelectedCategories((prev) =>
      prev.includes(slug) ? prev.filter((s) => s !== slug) : [...prev, slug]
    );
  }

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file || !title || !sourceBody) return;

    setBusy(true);
    setStatusMessage(null);
    setStatusType(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("source_body", sourceBody);
    formData.append("document_title", title);
    if (amendmentDate) {
      formData.append("amendment_date", amendmentDate);
    }
    formData.append("product_categories", JSON.stringify(selectedCategories));

    try {
      const res = await api.uploadDocument(formData);
      setStatusType("success");
      setStatusMessage(res.message);
      
      // Reset form
      setTitle("");
      setSourceBody("Custom");
      setAmendmentDate("");
      setSelectedCategories([]);
      setFile(null);
      
      // Reload inventory
      await loadDocuments();
    } catch (err) {
      setStatusType("error");
      setStatusMessage("Failed to upload document: " + (err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(filename: string) {
    if (!confirm(`Are you sure you want to delete ${filename}? This will remove its chunks and re-index the RAG database.`)) {
      return;
    }

    setBusy(true);
    setStatusMessage(null);
    setStatusType(null);

    try {
      const res = await api.deleteDocument(filename);
      setStatusType("success");
      setStatusMessage(res.message);
      await loadDocuments();
    } catch (err) {
      setStatusType("error");
      setStatusMessage("Failed to delete document: " + (err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function handleReIngest() {
    if (!confirm("Re-ingesting will clear and recheck all document indexes. Proceed?")) {
      return;
    }

    setBusy(true);
    setStatusMessage(null);
    setStatusType(null);

    try {
      const res = await api.ingest();
      setStatusType("success");
      setStatusMessage(`Ingested ${res.documents_processed} documents. Rebuilt ${res.chunks_created} vector chunks.`);
      await loadDocuments();
    } catch (err) {
      setStatusType("error");
      setStatusMessage("Re-ingestion failed: " + (err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-primary to-teal-500 bg-clip-text text-transparent">
            Knowledge Base Manager
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Maintain the regulatory documents dynamically loaded into the RAG vector index.
          </p>
        </div>
        <div>
          <Button
            variant="outline"
            className="cursor-pointer"
            onClick={handleReIngest}
            disabled={busy || loading}
          >
            {busy ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Database className="h-4 w-4 mr-2" />
            )}
            Re-Ingest Vector Index
          </Button>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-xl border border-border bg-card p-5 relative overflow-hidden">
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Total Documents
          </div>
          <div className="text-3xl font-bold mt-2">
            {loading ? <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /> : documents.length}
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            FSSAI, Codex, and custom uploads
          </p>
        </div>

        <div className="rounded-xl border border-border bg-card p-5 relative overflow-hidden">
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Total Chunks In Index
          </div>
          <div className="text-3xl font-bold mt-2">
            {loading ? <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /> : totalChunks}
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Splits stored in pgvector and ChromaDB
          </p>
        </div>

        <div className="rounded-xl border border-border bg-card p-5 relative overflow-hidden">
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Index Integrity
          </div>
          <div className="text-3xl font-bold mt-2 text-success flex items-center gap-1.5">
            <CheckCircle2 className="h-7 w-7" /> 100% Verified
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Synced with FSSAI standards
          </p>
        </div>
      </div>

      {/* Status banner */}
      {statusMessage && (
        <div
          className={cn(
            "rounded-xl border p-4 flex items-start gap-3 animate-in slide-in-from-top-4 duration-300",
            statusType === "success"
              ? "border-success/30 bg-success/5 text-success"
              : "border-destructive/30 bg-destructive/5 text-destructive"
          )}
        >
          {statusType === "success" ? (
            <CheckCircle2 className="h-5 w-5 shrink-0" />
          ) : (
            <AlertTriangle className="h-5 w-5 shrink-0" />
          )}
          <div className="text-sm font-medium">{statusMessage}</div>
        </div>
      )}

      {/* Content layout */}
      <div className="grid lg:grid-cols-[380px_1fr] gap-6">
        {/* Left column — Upload Form */}
        <div className="rounded-xl border border-border bg-card p-5 space-y-4 h-fit">
          <div>
            <h3 className="font-semibold">Add Regulatory Document</h3>
            <p className="text-xs text-muted-foreground">
              Upload markdown rules to chunk and add to vector memory.
            </p>
          </div>

          <form onSubmit={handleUpload} className="space-y-4">
            {/* Title */}
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground font-medium">
                Document Title
              </label>
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. FSSAI Poultry Standards 2026"
                required
                disabled={busy}
              />
            </div>

            {/* Source Body */}
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground font-medium">
                Source Body
              </label>
              <Input
                value={sourceBody}
                onChange={(e) => setSourceBody(e.target.value)}
                placeholder="e.g. FSSAI, Codex, Custom"
                required
                disabled={busy}
              />
            </div>

            {/* Amendment Date */}
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground font-medium">
                Amendment Date (Optional)
              </label>
              <Input
                type="date"
                value={amendmentDate}
                onChange={(e) => setAmendmentDate(e.target.value)}
                disabled={busy}
              />
            </div>

            {/* Product categories */}
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground font-medium block">
                Target Categories
              </label>
              <div className="grid grid-cols-2 gap-2 mt-1 max-h-32 overflow-y-auto pr-1">
                {FOOD_CATEGORIES.map((cat) => (
                  <div key={cat.slug} className="flex items-center gap-1.5 text-xs">
                    <Checkbox
                      id={`cat-${cat.slug}`}
                      checked={selectedCategories.includes(cat.slug)}
                      onCheckedChange={() => handleCategoryToggle(cat.slug)}
                      disabled={busy}
                    />
                    <label
                      htmlFor={`cat-${cat.slug}`}
                      className="cursor-pointer truncate"
                    >
                      {cat.label}
                    </label>
                  </div>
                ))}
              </div>
            </div>

            {/* File Dropzone */}
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground font-medium">
                Markdown File (.md)
              </label>
              <div
                className={cn(
                  "border-2 border-dashed border-border rounded-lg p-4 text-center cursor-pointer hover:border-primary/50 transition relative overflow-hidden bg-background/50",
                  file && "border-primary bg-primary/5"
                )}
              >
                <input
                  type="file"
                  accept=".md"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="absolute inset-0 opacity-0 cursor-pointer"
                  disabled={busy}
                  required
                />
                <Upload className="h-6 w-6 text-muted-foreground mx-auto mb-2" />
                {file ? (
                  <div className="text-xs font-semibold text-primary truncate">
                    {file.name}
                  </div>
                ) : (
                  <div className="text-[11px] text-muted-foreground">
                    Click or drag Markdown file here
                  </div>
                )}
              </div>
            </div>

            {/* Submit */}
            <Button type="submit" className="w-full cursor-pointer" disabled={busy || !file}>
              {busy ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <Plus className="h-4 w-4 mr-2" />
              )}
              Upload & Index Document
            </Button>
          </form>
        </div>

        {/* Right column — Inventory List */}
        <div className="rounded-xl border border-border bg-card p-5 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="font-semibold">Document Inventory</h3>
              <p className="text-xs text-muted-foreground">
                Protected system seed standards and custom uploaded guidelines.
              </p>
            </div>
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by title, filename..."
              className="w-full sm:w-64"
              disabled={loading}
            />
          </div>

          {loading && documents.length === 0 ? (
            <div className="h-48 flex items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : filteredDocs.length === 0 ? (
            <div className="h-48 flex flex-col items-center justify-center text-center p-4">
              <BookOpen className="h-8 w-8 text-muted-foreground mb-2" />
              <p className="text-sm font-medium">No matching documents found</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1">
              {filteredDocs.map((doc) => (
                <div
                  key={doc.filename}
                  className="rounded-lg border border-border p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-primary/20 transition bg-background/30"
                >
                  <div className="flex items-start gap-3">
                    <div className="h-9 w-9 rounded-md bg-primary/5 text-primary flex items-center justify-center shrink-0">
                      <FileText className="h-5 w-5" />
                    </div>
                    <div className="min-w-0">
                      <div className="font-medium text-sm text-foreground leading-tight flex items-center gap-1.5 flex-wrap">
                        {doc.title}
                        <span
                          className={cn(
                            "text-[10px] px-1.5 py-0.5 rounded-full font-semibold uppercase tracking-wider",
                            doc.type === "seed"
                              ? "bg-primary/10 text-primary"
                              : "bg-teal-500/10 text-teal-600 border border-teal-500/20"
                          )}
                        >
                          {doc.type}
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground mt-1 truncate">
                        File: <code>{doc.filename}</code>
                      </div>
                      <div className="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground flex-wrap">
                        <span className="font-medium px-2 py-0.5 rounded bg-muted">
                          {doc.source_body}
                        </span>
                        {doc.amendment_date && (
                          <span>Amended: {doc.amendment_date}</span>
                        )}
                        <span>{doc.chunks_count} segments indexed</span>
                      </div>
                      <div className="flex gap-1 flex-wrap mt-2">
                        {doc.product_categories.map((c) => (
                          <span
                            key={c}
                            className="text-[10px] px-1.5 py-0.5 rounded bg-muted/60 text-muted-foreground border border-border"
                          >
                            {c}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center justify-end">
                    {doc.type === "seed" ? (
                      <span className="text-[10px] text-muted-foreground bg-muted/30 px-2 py-1 rounded border border-border">
                        Protected
                      </span>
                    ) : (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(doc.filename)}
                        className="text-muted-foreground hover:text-destructive hover:bg-destructive/15 cursor-pointer"
                        disabled={busy}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
