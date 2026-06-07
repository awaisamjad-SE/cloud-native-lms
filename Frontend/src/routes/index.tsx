import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { lmsApi } from "@/lib/lms-api";
import { AppShell } from "@/components/AppShell";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { BookOpen, Search, Shield, Lock, Sparkles } from "lucide-react";
import { resolveMediaUrl } from "@/lib/media";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Mini LMS · Premium courses" },
      { name: "description", content: "Browse and enroll in premium courses. Secure video and document delivery powered by AWS S3." },
      { property: "og:title", content: "Mini LMS" },
      { property: "og:description", content: "Premium learning, secure content delivery." },
    ],
  }),
  component: Index,
});

interface Course {
  id: number | string;
  title: string;
  slug: string;
  description: string;
  thumbnail?: string | null;
  thumbnail_url?: string | null;
  price: string | number;
  category?: any;
  status?: string;
}

function normalize(data: any): Course[] {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;
  return [];
}

function Index() {
  const nav = useNavigate();
  const [q, setQ] = useState("");
  const { data, isLoading, error } = useQuery({
    queryKey: ["courses", q],
    queryFn: () => lmsApi.courses.list(q),
  });
  const courses = normalize(data);

  return (
    <AppShell>
      <section className="relative overflow-hidden border-b border-border">
        <div className="absolute inset-0 -z-10 bg-gradient-to-br from-primary/5 via-background to-accent/10" />
        <div className="max-w-7xl mx-auto px-4 py-20 grid md:grid-cols-2 gap-10 items-center">
          <div>
            <span className="inline-flex items-center gap-2 text-xs uppercase tracking-widest text-accent-foreground bg-accent/30 px-3 py-1 rounded-full border border-accent/40">
              <Sparkles className="size-3" /> Premium learning
            </span>
            <h1 className="font-serif text-5xl md:text-6xl mt-4 leading-[1.05] text-primary">
              Learn deeply.<br />
              <span className="text-accent">Own the craft.</span>
            </h1>
            <p className="mt-5 text-muted-foreground max-w-md">
              A curated catalog of in-depth courses. Buy once, stream privately, track every lesson — secured end-to-end with AWS S3 presigned delivery.
            </p>
            <div className="mt-7 flex gap-3">
              <Button size="lg" onClick={() => document.getElementById("catalog")?.scrollIntoView({ behavior: "smooth" })}>
                <BookOpen className="size-4 mr-2" /> Browse courses
              </Button>
              <Link to="/register"><Button size="lg" variant="outline">Create account</Button></Link>
            </div>
            <div className="mt-8 flex gap-6 text-xs text-muted-foreground">
              <span className="flex items-center gap-1.5"><Shield className="size-3.5 text-primary" /> JWT auth</span>
              <span className="flex items-center gap-1.5"><Lock className="size-3.5 text-primary" /> Presigned URLs</span>
              <span className="flex items-center gap-1.5"><Sparkles className="size-3.5 text-primary" /> Lesson progress</span>
            </div>
          </div>
          <div className="relative">
            <div className="aspect-[4/3] rounded-2xl bg-gradient-to-br from-primary to-primary/70 p-6 shadow-2xl shadow-primary/20 border border-primary/50">
              <div className="h-full rounded-xl bg-card/95 p-5 flex flex-col">
                <div className="text-xs text-muted-foreground">Course preview</div>
                <div className="font-serif text-2xl text-primary mt-1">Introduction to S3 Delivery</div>
                <div className="flex-1 mt-4 rounded-lg bg-gradient-to-br from-accent/40 to-accent/10 grid place-items-center text-accent-foreground">
                  <BookOpen className="size-12 opacity-70" />
                </div>
                <div className="mt-4 flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">12 lessons · 3h 40m</span>
                  <span className="font-semibold text-primary">$49</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="catalog" className="max-w-7xl mx-auto px-4 py-14">
        <div className="flex items-end justify-between gap-4 mb-6">
          <div>
            <h2 className="font-serif text-3xl text-primary">Course catalog</h2>
            <p className="text-sm text-muted-foreground">Browse all published courses.</p>
          </div>
          <div className="relative w-full max-w-xs">
            <Search className="size-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <Input className="pl-9" placeholder="Search courses…" value={q} onChange={(e) => setQ(e.target.value)} />
          </div>
        </div>

        {isLoading && <div className="text-muted-foreground">Loading catalog…</div>}
        {error && (
          <div className="rounded-lg border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
            Could not load courses: {(error as Error).message}. Check the API base URL in the top-right gear icon.
          </div>
        )}
        {!isLoading && !error && courses.length === 0 && (
          <div className="rounded-lg border border-border bg-card p-10 text-center text-muted-foreground">
            No courses yet.
          </div>
        )}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {courses.map((c) => (
            <button
              key={c.id}
              onClick={() => nav({ to: "/courses/$slug", params: { slug: c.slug } })}
              className="group text-left bg-card border border-border rounded-xl overflow-hidden hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5 transition-all"
            >
              <div className="aspect-video bg-gradient-to-br from-primary/20 to-accent/20 relative overflow-hidden">
                {(c.thumbnail_url || c.thumbnail) ? (
                  <img src={resolveMediaUrl(c.thumbnail_url || c.thumbnail)} alt={c.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform" />
                ) : (
                  <div className="w-full h-full grid place-items-center text-primary/60"><BookOpen className="size-12" /></div>
                )}
                {c.status && c.status !== "published" && (
                  <Badge variant="secondary" className="absolute top-3 right-3">{c.status}</Badge>
                )}
              </div>
              <div className="p-5">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="font-serif text-lg text-primary line-clamp-2 group-hover:text-primary/80">{c.title}</h3>
                  <span className="font-semibold text-accent-foreground bg-accent/40 px-2 py-0.5 rounded text-sm shrink-0">${c.price}</span>
                </div>
                <p className="mt-2 text-sm text-muted-foreground line-clamp-2">{c.description}</p>
                {c.category && (
                  <div className="mt-3 text-xs text-muted-foreground">
                    {typeof c.category === "string" ? c.category : c.category?.name}
                  </div>
                )}
              </div>
            </button>
          ))}
        </div>
      </section>
    </AppShell>
  );
}
