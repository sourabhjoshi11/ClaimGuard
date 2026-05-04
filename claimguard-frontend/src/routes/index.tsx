import { createFileRoute } from "@tanstack/react-router";
import { Link } from "@tanstack/react-router";
import { Shield, Sparkles, FileSearch, DollarSign, ArrowRight } from "lucide-react";
import { Header } from "@/components/Header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export const Route = createFileRoute("/")({
  component: Index,
});

function Index() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main>
        {/* Hero */}
        <section className="relative isolate overflow-hidden">
          <img
            src="/claim-samples/damaged-car.png"
            alt=""
            className="absolute inset-0 -z-20 h-full w-full object-cover"
          />
          <div className="absolute inset-0 -z-10 bg-background/85 backdrop-blur-[1px]" />
          <div className="container mx-auto max-w-5xl px-4 py-20 text-center sm:py-24">
            <div className="mx-auto inline-flex items-center gap-2 rounded-full border border-border bg-background/75 px-3 py-1 text-xs font-medium text-muted-foreground backdrop-blur">
              <Sparkles className="h-3.5 w-3.5 text-primary" />
              AI-powered damage assessment
            </div>
            <h1 className="mt-6 text-4xl font-semibold tracking-tight text-foreground sm:text-6xl">
              Insurance claims,{" "}
              <span className="bg-[image:var(--gradient-primary)] bg-clip-text text-transparent">
                reviewed in seconds
              </span>
            </h1>
            <p className="mx-auto mt-5 max-w-xl text-base text-muted-foreground sm:text-lg">
              Upload a before-and-after photo or video. ClaimGuard AI detects damages, scores severity, and estimates repair cost — instantly.
            </p>
            <div className="mt-8 flex items-center justify-center gap-3">
              <Button asChild size="lg">
                <Link to="/register">
                  Get started <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <Link to="/login">Sign in</Link>
              </Button>
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="container mx-auto max-w-5xl px-4 py-20">
          <div className="grid gap-6 md:grid-cols-3">
            {[
              { icon: Shield, title: "Validated uploads", body: "Files are checked for type, size, and integrity before analysis." },
              { icon: FileSearch, title: "Vision comparison", body: "A multimodal LLM compares before/after media to spot damage." },
              { icon: DollarSign, title: "Cost estimates", body: "Severity is mapped to repair cost — totalled per claim." },
            ].map(({ icon: Icon, title, body }) => (
              <Card key={title} className="border-border/60 p-6 shadow-[var(--shadow-card)]">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent">
                  <Icon className="h-5 w-5 text-primary" />
                </div>
                <h3 className="mt-4 text-base font-semibold text-foreground">{title}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{body}</p>
              </Card>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
