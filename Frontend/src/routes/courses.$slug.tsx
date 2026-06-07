import { createFileRoute, Link, useNavigate, useParams } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { BookOpen, CheckCircle2, FileText, Lock, PlayCircle, ShoppingCart } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { lmsApi } from "@/lib/lms-api";
import { resolveMediaUrl } from "@/lib/media";

export const Route = createFileRoute("/courses/$slug")({
  component: CoursePage,
});

function CoursePage() {
  const { slug } = useParams({ from: "/courses/$slug" });
  const { user, isAdmin } = useAuth();
  const nav = useNavigate();
  const [activeLessonId, setActiveLessonId] = useState<string | null>(null);

  const course = useQuery({ queryKey: ["course", slug], queryFn: () => lmsApi.courses.detail(slug) });
  const lessons = useQuery({
    queryKey: ["course-lessons", slug, isAdmin ? "admin" : "public"],
    queryFn: async () => {
      if (!course.data) return [];
      if (isAdmin) {
        try {
          const adminLessons = await lmsApi.courses.adminLessons(course.data.id);
          if (Array.isArray(adminLessons)) return adminLessons;
          return adminLessons?.results || [];
        } catch {
          // Fall back to the public endpoint if admin listing is not available.
        }
      }
      return lmsApi.courses.lessons(slug);
    },
    enabled: !!slug && !!course.data,
  });
  const enrollments = useQuery({
    queryKey: ["my-enrollments"],
    queryFn: () => lmsApi.enrollments.my(),
    enabled: !!user,
  });
  const progress = useQuery({
    queryKey: ["course-progress", slug],
    queryFn: () => lmsApi.courses.progress(slug),
    enabled: !!user,
    retry: false,
  });

  const lessonList: any[] = Array.isArray(lessons.data) ? lessons.data : lessons.data?.results || [];
  const enrollmentList: any[] = Array.isArray(enrollments.data) ? enrollments.data : enrollments.data?.results || [];
  const enrolled = !!course.data?.is_enrolled || enrollmentList.some((enrollment) => {
    const enrollmentCourse = enrollment.course || {};
    return enrollmentCourse.slug === slug || enrollment.course_slug === slug || enrollmentCourse.id === course.data?.id || enrollment.course_id === course.data?.id;
  });
  const completedIds = new Set<any>(
    (progress.data?.completed_lessons || progress.data?.lessons || [])
      .map((x: any) => (typeof x === "object" ? x.lesson || x.id : x))
  );
  const pct = progress.data?.percentage ?? progress.data?.progress ??
    (lessonList.length ? Math.round((completedIds.size / lessonList.length) * 100) : 0);

  const lessonAccess = useQuery({
    queryKey: ["lesson-access", activeLessonId],
    queryFn: () => lmsApi.courses.lessonAccess(activeLessonId as string),
    enabled: !!activeLessonId,
    retry: false,
  });

  function getLessonAccessUrl(data: any): string {
    const raw = data?.url || data?.presigned_url || data?.download_url || "";
    return resolveMediaUrl(raw);
  }

  function isVideoLesson(lesson: any, url: string): boolean {
    const t = String(lesson?.lesson_type || "").toLowerCase();
    if (t.includes("video")) return true;
    return /\.(mp4|webm|ogg|m3u8)(\?|$)/i.test(url);
  }

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto px-4 py-10">
        {course.isLoading && <div className="text-muted-foreground">Loading…</div>}
        {course.error && <div className="text-destructive">{(course.error as Error).message}</div>}
        {course.data && (
          <>
            <Link to="/" className="text-sm text-muted-foreground hover:text-primary">&larr; Back to catalog</Link>
            <div className="mt-4 grid md:grid-cols-3 gap-8">
              <div className="md:col-span-2">
                <div className="aspect-video rounded-xl overflow-hidden bg-gradient-to-br from-primary/20 to-accent/20 border border-border">
                  {(course.data.thumbnail_url || course.data.thumbnail) ? (
                    <img src={resolveMediaUrl(course.data.thumbnail_url || course.data.thumbnail)} alt={course.data.title} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full grid place-items-center text-primary/60"><BookOpen className="size-16" /></div>
                  )}
                </div>
                <h1 className="font-serif text-4xl text-primary mt-6">{course.data.title}</h1>
                <p className="mt-3 text-muted-foreground whitespace-pre-wrap">{course.data.description}</p>

                {enrolled && (
                  <div className="mt-6 bg-card border border-border rounded-xl p-4">
                    <div className="flex justify-between text-sm mb-2"><span>Your progress</span><span className="font-medium text-primary">{pct}%</span></div>
                    <Progress value={pct} />
                  </div>
                )}

                <h2 className="font-serif text-2xl text-primary mt-10">Lessons</h2>
                <div className="mt-4">
                  {lessons.isLoading && <div className="text-muted-foreground">Loading lessons…</div>}
                  {lessonList.length === 0 && !lessons.isLoading && (
                    <div className="text-muted-foreground text-sm">No lessons yet.</div>
                  )}
                  {lessonList.length > 0 && (
                    <Accordion
                      type="single"
                      collapsible
                      value={activeLessonId || ""}
                      onValueChange={(value) => setActiveLessonId(value || null)}
                      className="rounded-xl border border-border bg-card px-4"
                    >
                      {lessonList.map((l, i) => {
                        const canAccess = enrolled || l.is_preview;
                        const done = completedIds.has(l.id);
                        const isActive = String(l.id) === activeLessonId;
                        const mediaUrl = isActive ? getLessonAccessUrl(lessonAccess.data) : "";
                        const showVideo = isActive && mediaUrl && isVideoLesson(l, mediaUrl);

                        return (
                          <AccordionItem key={l.id} value={String(l.id)} className="border-border">
                            <AccordionTrigger className="hover:no-underline">
                              <div className="flex items-center gap-3 w-full pr-3">
                                <span className="text-muted-foreground text-sm w-6">{l.order ?? i + 1}</span>
                                {done ? <CheckCircle2 className="size-5 text-primary" /> :
                                  l.lesson_type === "video" ? <PlayCircle className="size-5 text-primary" /> : <FileText className="size-5 text-primary" />}
                                <div className="flex-1 text-left">
                                  <div className="font-medium">{l.title}</div>
                                  {l.duration ? <div className="text-xs text-muted-foreground">{l.duration} min</div> : null}
                                </div>
                                {l.is_preview && <Badge variant="secondary">Preview</Badge>}
                                {!canAccess && <Lock className="size-4 text-muted-foreground" />}
                              </div>
                            </AccordionTrigger>
                            <AccordionContent>
                              {!canAccess ? (
                                <div className="rounded-lg border border-border bg-secondary/20 p-4 text-sm text-muted-foreground">
                                  This lesson is locked. Enroll to view the content.
                                </div>
                              ) : isActive && lessonAccess.isLoading ? (
                                <div className="rounded-lg border border-border bg-secondary/20 p-4 text-sm text-muted-foreground">Loading lesson content…</div>
                              ) : isActive && lessonAccess.error ? (
                                <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
                                  Could not load this lesson content.
                                </div>
                              ) : isActive && mediaUrl ? (
                                showVideo ? (
                                  <video className="w-full rounded-lg border border-border bg-black" controls preload="metadata" src={mediaUrl} />
                                ) : (
                                  <iframe
                                    title={`Lesson ${l.title}`}
                                    src={mediaUrl}
                                    className="w-full h-[560px] rounded-lg border border-border bg-background"
                                  />
                                )
                              ) : (
                                <div className="rounded-lg border border-border bg-secondary/20 p-4 text-sm text-muted-foreground">
                                  No media URL available for this lesson.
                                </div>
                              )}
                            </AccordionContent>
                          </AccordionItem>
                        );
                      })}
                    </Accordion>
                  )}
                </div>
              </div>

              <aside className="md:col-span-1">
                <div className="sticky top-20 bg-card border border-border rounded-xl p-6">
                  <div className="text-3xl font-serif text-primary">${course.data.price}</div>
                  <div className="text-xs text-muted-foreground">One-time purchase · lifetime access</div>
                  <div className="mt-6 space-y-2">
                    {enrolled ? (
                      <Badge className="w-full justify-center py-2">Enrolled</Badge>
                    ) : user ? (
                      <Button className="w-full" onClick={() => nav({ to: "/checkout/$slug", params: { slug } })}>
                        <ShoppingCart className="size-4 mr-2" /> Purchase course
                      </Button>
                    ) : (
                      <Link to="/login"><Button className="w-full"><ShoppingCart className="size-4 mr-2" /> Sign in to enroll</Button></Link>
                    )}
                  </div>
                  <ul className="mt-6 space-y-2 text-sm text-muted-foreground">
                    <li>· {lessonList.length} lessons</li>
                    <li>· Secure S3 streaming</li>
                    <li>· Progress tracking</li>
                  </ul>
                </div>
              </aside>
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}