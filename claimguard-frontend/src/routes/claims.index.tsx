import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ArrowRight, FileImage, Plus, Inbox } from "lucide-react";
import { Header } from "@/components/Header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/lib/auth-context";
import { api, resolveMediaUrl, type Claim } from "@/lib/api";
import { toast } from "sonner";

export const Route = createFileRoute("/claims/")({
  component: ClaimsListPage,
  head: () => ({ meta: [{ title: "My Claims — ClaimGuard AI" }] }),
});

function statusVariant(status: string): "default" | "secondary" | "destructive" {
  const s = status.toLowerCase();
  if (s.includes("complete")) return "default";
  if (s.includes("invalid") || s.includes("error") || s.includes("fail")) return "destructive";
  return "secondary";
}

function ClaimsListPage() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [claims, setClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate({ to: "/login" });
      return;
    }
    api
      .listClaims()
      .then((data) => {
        const list = Array.isArray(data) ? data : data.results ?? data.claims ?? [];
        setClaims(list.slice(0, 2));
      })
      .catch((err) => toast.error(err instanceof Error ? err.message : "Failed to load claims"))
      .finally(() => setLoading(false));
  }, [isAuthenticated, navigate]);

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container mx-auto max-w-5xl px-4 py-10">
        <div className="mb-8 flex items-end justify-between">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-foreground">My Claims</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Review your two most recent submitted claims and their AI assessments.
            </p>
          </div>
          <Button asChild>
            <Link to="/claims/new">
              <Plus className="mr-1 h-4 w-4" /> New Claim
            </Link>
          </Button>
        </div>

        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-44 animate-pulse rounded-xl bg-muted/60" />
            ))}
          </div>
        ) : claims.length === 0 ? (
          <Card className="flex flex-col items-center justify-center gap-3 border-dashed p-16 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
              <Inbox className="h-6 w-6 text-muted-foreground" />
            </div>
            <h2 className="text-lg font-medium">No claims yet</h2>
            <p className="max-w-sm text-sm text-muted-foreground">
              Upload a reference and incident file to generate your first AI assessment.
            </p>
            <Button asChild>
              <Link to="/claims/new">Submit a claim</Link>
            </Button>
          </Card>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {claims.map((c) => (
              <Card key={c.id} className="overflow-hidden border-border/60 shadow-[var(--shadow-card)]">
                  <div className="aspect-video w-full bg-muted">
                  {c.image_url && c.media_type?.toLowerCase() === "video" ? (
                      <video src={resolveMediaUrl(c.image_url)} className="h-full w-full object-contain" />
                  ) : c.image_url ? (
                      <img src={resolveMediaUrl(c.image_url)} alt={`Claim ${c.id}`} className="h-full w-full object-cover" />
                  ) : (
                      <div className="flex h-full items-center justify-center text-muted-foreground">
                        <FileImage className="h-8 w-8" />
                      </div>
                  )}
                  </div>
                  <div className="space-y-2 p-4">
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-sm font-medium">Claim #{c.id}</span>
                      <Badge variant={statusVariant(c.status)} className="max-w-36 break-words text-center">{c.status}</Badge>
                    </div>
                    {c.created_at && (
                      <p className="text-xs text-muted-foreground">
                        {new Date(c.created_at).toLocaleString()}
                      </p>
                    )}
                    <Button asChild variant="outline" size="sm" className="w-full">
                      <Link to="/claims/$claimId" params={{ claimId: String(c.id) }}>
                        View report <ArrowRight className="h-4 w-4" />
                      </Link>
                    </Button>
                  </div>
                </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
