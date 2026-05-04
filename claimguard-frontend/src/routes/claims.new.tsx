import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState, type FormEvent } from "react";
import { UploadCloud, ArrowLeft, Sparkles, AlertCircle, CheckCircle2, Download, Eye } from "lucide-react";
import { Header } from "@/components/Header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/lib/auth-context";
import { api, getWorkflowAnomalies, type UploadResponse } from "@/lib/api";
import { formatRupees } from "@/lib/currency";
import { claimFromUpload, downloadClaimPdf } from "@/lib/report";
import { toast } from "sonner";

export const Route = createFileRoute("/claims/new")({
  component: NewClaimPage,
  head: () => ({ meta: [{ title: "New Claim — ClaimGuard AI" }] }),
});

function severityColor(sev: string) {
  const s = sev.toLowerCase();
  if (s === "high") return "bg-destructive/10 text-destructive border-destructive/30";
  if (s === "medium") return "bg-warning/15 text-foreground border-warning/40";
  return "bg-success/15 text-foreground border-success/40";
}

function FileDrop({
  label,
  file,
  onFile,
  accept,
}: {
  label: string;
  file: File | null;
  onFile: (f: File | null) => void;
  accept: string;
}) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    if (file && file.type.startsWith('image/')) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      return () => URL.revokeObjectURL(url);
    } else if (file && file.type.startsWith('video/')) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      return () => URL.revokeObjectURL(url);
    } else {
      setPreviewUrl(null);
    }
  }, [file]);

  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <label className="group flex min-h-44 cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-border bg-muted/30 px-4 py-8 text-center transition hover:border-primary hover:bg-accent/40">
        <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-background shadow-sm">
          <UploadCloud className="h-5 w-5 text-muted-foreground group-hover:text-primary" />
        </div>
        {file ? (
          <div>
            <p className="text-sm font-medium text-foreground">{file.name}</p>
            <p className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(1)} KB</p>
          </div>
        ) : (
          <div>
            <p className="text-sm font-medium text-foreground">Click to upload</p>
            <p className="text-xs text-muted-foreground">{accept}</p>
          </div>
        )}
        <input
          type="file"
          accept={accept}
          className="hidden"
          onChange={(e) => onFile(e.target.files?.[0] ?? null)}
        />
      </label>
      {previewUrl && file?.type.startsWith('image/') && (
        <div className="mt-4">
          <img src={previewUrl} alt="Preview" className="max-w-full h-auto rounded-lg border border-border" />
        </div>
      )}
      {previewUrl && file?.type.startsWith('video/') && (
        <div className="mt-4">
          <video src={previewUrl} controls className="max-w-full h-auto rounded-lg border border-border" />
        </div>
      )}
    </div>
  );
}

function NewClaimPage() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [mediaType, setMediaType] = useState<"image" | "video">("image");
  const [reference, setReference] = useState<File | null>(null);
  const [incident, setIncident] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<UploadResponse | null>(null);

  useEffect(() => {
    if (!isAuthenticated) navigate({ to: "/login" });
  }, [isAuthenticated, navigate]);

  const accept =
    mediaType === "image"
      ? ".jpg,.jpeg,.png,.webp"
      : ".mp4,.mov,.avi,.mkv,.webm";
  const anomalies = getWorkflowAnomalies(result?.workflow_result);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!incident) {
      toast.error("Please select the incident file");
      return;
    }
    const fd = new FormData();
    fd.append(mediaType === "image" ? "image" : "media", incident);
    if (reference) {
      fd.append(mediaType === "image" ? "reference_image" : "reference_media", reference);
    }
    fd.append("media_type", mediaType);

    setSubmitting(true);
    setResult(null);
    try {
      const data = await api.uploadClaim(fd);
      setResult(data);
      toast.success("Claim processed");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container mx-auto max-w-4xl px-4 py-10">
        <Link to="/claims" className="mb-6 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> Back to claims
        </Link>

        <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-foreground">New Claim</h1>
            <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
              Upload incident media, add a reference file when available, and generate a structured assessment.
            </p>
          </div>
          <Badge variant="secondary" className="w-fit">AI assessment</Badge>
        </div>

        <Card className="mt-6 border-border/60 p-6 shadow-[var(--shadow-card)]">
          <form onSubmit={onSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label>Media type</Label>
              <div className="inline-flex rounded-lg border border-border bg-muted/40 p-1">
                {(["image", "video"] as const).map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => {
                      setMediaType(t);
                      setReference(null);
                      setIncident(null);
                    }}
                    className={`rounded-md px-4 py-1.5 text-sm font-medium capitalize transition ${
                      mediaType === t
                        ? "bg-background text-foreground shadow-sm"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <FileDrop label="Reference (before)" file={reference} onFile={setReference} accept={accept} />
              <FileDrop label="Incident (after)" file={incident} onFile={setIncident} accept={accept} />
            </div>

            <div className="flex flex-col gap-3 border-t border-border pt-5 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-muted-foreground">
                The incident file is required. Reference media improves comparison accuracy.
              </p>
              <Button type="submit" disabled={submitting || !incident} className="w-full sm:w-auto">
                <Sparkles className="mr-2 h-4 w-4" />
                {submitting ? "Analyzing..." : "Run AI assessment"}
              </Button>
            </div>
          </form>
        </Card>

        {result && (
          <Card className="mt-6 overflow-hidden border-border/60 shadow-[var(--shadow-card)]">
            <div className="border-b border-border bg-[image:var(--gradient-subtle)] p-6">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div className="flex min-w-0 items-start gap-2">
                  {result.workflow_result.status.toLowerCase().includes("complete") ? (
                    <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-success" />
                  ) : (
                    <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-warning" />
                  )}
                  <div className="min-w-0">
                    <h2 className="text-lg font-semibold">Assessment report</h2>
                    <p className="mt-1 break-words text-sm text-muted-foreground">{result.workflow_result.status}</p>
                  </div>
                </div>
                <div className="flex flex-col gap-2 sm:flex-row">
                  <Button variant="outline" size="sm" onClick={() => downloadClaimPdf(claimFromUpload(result))}>
                    <Download className="mr-2 h-4 w-4" />
                    Download PDF
                  </Button>
                  <Button asChild variant="secondary" size="sm" className="w-full">
                    <Link to="/claims/$claimId" params={{ claimId: String(result.claim_id) }}>
                      <Eye className="mr-2 h-4 w-4" />
                      Open claim
                    </Link>
                  </Button>
                </div>
              </div>
              <div className="mt-4 grid grid-cols-3 gap-4">
                <Stat label="Claim ID" value={`#${result.claim_id}`} />
                <Stat label="Media type" value={result.media_type} />
                <Stat
                  label="Total estimate"
                  value={formatRupees(result.workflow_result.total_claim_value)}
                  accent
                />
              </div>
            </div>

            <div className="p-6">
              <h3 className="mb-3 text-sm font-medium text-muted-foreground">Detected anomalies</h3>
              {anomalies.length === 0 ? (
                <p className="text-sm text-muted-foreground">No anomalies were detected.</p>
              ) : (
                <div className="space-y-2">
                  {anomalies.map((a, i) => (
                    <div
                      key={i}
                      className="flex items-start justify-between gap-3 rounded-lg border border-border bg-card p-4"
                    >
                      <div className="flex-1">
                        <p className="font-medium text-foreground">{a.item}</p>
                        <p className="mt-0.5 text-sm text-muted-foreground">{a.issue}</p>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        <span className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${severityColor(a.severity)}`}>
                          {a.severity}
                        </span>
                        {typeof a.estimated_cost === "number" && (
                          <span className="text-sm font-semibold text-foreground">
                            {formatRupees(a.estimated_cost)}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Card>
        )}
      </main>
    </div>
  );
}

function Stat({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wider text-muted-foreground">{label}</p>
      <p className={`mt-1 text-lg font-semibold ${accent ? "text-primary" : "text-foreground"}`}>{value}</p>
    </div>
  );
}
