import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { useAuth } from "@/lib/auth";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Check, Plus, ShieldOff, Shield as ShieldOn, X } from "lucide-react";
import { lmsApi } from "@/lib/lms-api";
import { resolveMediaUrl } from "@/lib/media";

export const Route = createFileRoute("/admin")({
  head: () => ({ meta: [{ title: "Admin · Mini LMS" }] }),
  component: AdminPage,
});

function asList(d: any): any[] {
  return Array.isArray(d) ? d : d?.results || [];
}

function makeCourseSlug(title: string): string {
  const base = title
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 48);
  const shortId = Math.random().toString(36).slice(2, 7);
  return `${base || "course"}-${shortId}`;
}

function AdminPage() {
  const { user, isAdmin, loading } = useAuth();
  const nav = useNavigate();
  useEffect(() => {
    if (!loading && (!user || !isAdmin)) nav({ to: "/" });
  }, [user, isAdmin, loading, nav]);

  if (!isAdmin) return null;

  return (
    <AppShell>
      <div className="max-w-7xl mx-auto px-4 py-10">
        <h1 className="font-serif text-3xl text-primary">Admin console</h1>
        <p className="text-muted-foreground text-sm mt-1">Manage users, courses, lessons, enrollments, payments and banks.</p>

        <Tabs defaultValue="payments" className="mt-8">
          <TabsList className="flex-wrap h-auto">
            <TabsTrigger value="payments">Payments</TabsTrigger>
            <TabsTrigger value="courses">Courses</TabsTrigger>
            <TabsTrigger value="lessons">Lessons</TabsTrigger>
            <TabsTrigger value="enrollments">Enrollments</TabsTrigger>
            <TabsTrigger value="users">Users</TabsTrigger>
            <TabsTrigger value="banks">Bank accounts</TabsTrigger>
          </TabsList>
          <TabsContent value="payments" className="mt-6"><AdminPayments /></TabsContent>
          <TabsContent value="courses" className="mt-6"><AdminCourses /></TabsContent>
          <TabsContent value="lessons" className="mt-6"><AdminLessons /></TabsContent>
          <TabsContent value="enrollments" className="mt-6"><AdminEnrollments /></TabsContent>
          <TabsContent value="users" className="mt-6"><AdminUsers /></TabsContent>
          <TabsContent value="banks" className="mt-6"><AdminBanks /></TabsContent>
        </Tabs>
      </div>
    </AppShell>
  );
}

/* ------------ Payments ------------ */
function AdminPayments() {
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["admin-payments"], queryFn: () => lmsApi.payments.adminList() });
  const list = asList(q.data);
  const [rejectPaymentId, setRejectPaymentId] = useState<any>(null);
  const [previewPayment, setPreviewPayment] = useState<any>(null);
  const [rejectionReason, setRejectionReason] = useState("");

  function getReceiptUrl(payment: any): string {
    return resolveMediaUrl(payment?.proof_receipt_url || payment?.proof_receipt || "");
  }

  const approve = useMutation({
    mutationFn: (id: any) => lmsApi.payments.adminApprove(id),
    onSuccess: () => { toast.success("Payment approved"); qc.invalidateQueries({ queryKey: ["admin-payments"] }); },
    onError: (e: any) => toast.error(e.message),
  });
  const reject = useMutation({
    mutationFn: ({ id, reason }: { id: any; reason: string }) => lmsApi.payments.adminReject(id, reason),
    onSuccess: () => {
      toast.success("Payment rejected");
      setRejectPaymentId(null);
      setRejectionReason("");
      qc.invalidateQueries({ queryKey: ["admin-payments"] });
    },
    onError: (e: any) => toast.error(e.message),
  });
  return (
    <Section title="All payments" loading={q.isLoading} empty={!list.length}>
      <table className="w-full text-sm">
        <thead className="bg-secondary/60 text-left"><tr>
          <th className="p-3">Student</th><th className="p-3">Course</th><th className="p-3">Amount</th>
          <th className="p-3">Reference</th><th className="p-3">Status</th><th className="p-3">Action</th>
        </tr></thead>
        <tbody>{list.map((p) => (
          <tr key={p.id} className="border-t border-border">
            <td className="p-3">{p.student?.username || p.student_username || p.student}</td>
            <td className="p-3">{p.course?.title || p.course_title || p.course}</td>
            <td className="p-3">${p.amount}</td>
            <td className="p-3 font-mono text-xs">{p.transaction_reference}</td>
            <td className="p-3"><Badge variant={p.status === "approved" || p.status === "completed" ? "default" : p.status === "rejected" || p.status === "failed" ? "destructive" : "secondary"}>{p.status}</Badge></td>
            <td className="p-3">
              {getReceiptUrl(p) ? (
                <button
                  type="button"
                  onClick={() => setPreviewPayment(p)}
                  className="group flex items-center gap-3 text-left"
                  title="Open receipt preview"
                >
                  <img
                    src={getReceiptUrl(p)}
                    alt="Payment receipt"
                    className="h-16 w-16 rounded-md border border-border object-cover bg-secondary/20"
                  />
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-primary group-hover:underline">View receipt</div>
                    <div className="text-xs text-muted-foreground truncate max-w-[160px]">Click to inspect before approving</div>
                  </div>
                </button>
              ) : (
                <div className="text-xs text-muted-foreground">No receipt uploaded</div>
              )}
            </td>
            <td className="p-3 flex gap-2">
              <Button size="sm" variant="outline" onClick={() => approve.mutate(p.id)} disabled={approve.isPending}><Check className="size-3 mr-1" />Approve</Button>
              <Dialog open={rejectPaymentId === p.id} onOpenChange={(open) => setRejectPaymentId(open ? p.id : null)}>
                <DialogTrigger asChild>
                  <Button size="sm" variant="outline"><X className="size-3 mr-1" />Reject</Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader><DialogTitle>Reject payment</DialogTitle></DialogHeader>
                  <div className="space-y-2">
                    <Label>Reason</Label>
                    <Textarea value={rejectionReason} onChange={(e) => setRejectionReason(e.target.value)} placeholder="Invalid proof" />
                  </div>
                  <DialogFooter>
                    <Button
                      variant="destructive"
                      onClick={() => reject.mutate({ id: p.id, reason: rejectionReason || "Rejected by admin" })}
                      disabled={reject.isPending}
                    >
                      Confirm reject
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </td>
          </tr>
        ))}</tbody>
      </table>

      <Dialog open={!!previewPayment} onOpenChange={(open) => !open && setPreviewPayment(null)}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Receipt preview</DialogTitle>
          </DialogHeader>
          {previewPayment && (
            <div className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2 text-sm">
                <div className="space-y-1">
                  <div className="text-muted-foreground">Student</div>
                  <div className="font-medium">{previewPayment.student?.username || previewPayment.student_username || previewPayment.student}</div>
                </div>
                <div className="space-y-1">
                  <div className="text-muted-foreground">Course</div>
                  <div className="font-medium">{previewPayment.course?.title || previewPayment.course_title || previewPayment.course}</div>
                </div>
                <div className="space-y-1">
                  <div className="text-muted-foreground">Reference</div>
                  <div className="font-mono text-xs">{previewPayment.transaction_reference}</div>
                </div>
                <div className="space-y-1">
                  <div className="text-muted-foreground">Amount</div>
                  <div className="font-medium">${previewPayment.amount}</div>
                </div>
              </div>

              {getReceiptUrl(previewPayment) ? (
                <a href={getReceiptUrl(previewPayment)} target="_blank" rel="noreferrer" className="block">
                  <img
                    src={getReceiptUrl(previewPayment)}
                    alt="Payment receipt"
                    className="max-h-[70vh] w-full rounded-lg border border-border object-contain bg-black/5"
                  />
                </a>
              ) : (
                <div className="rounded-lg border border-border bg-secondary/20 p-6 text-sm text-muted-foreground">
                  No receipt available for this payment.
                </div>
              )}

              <DialogFooter>
                <Button variant="outline" onClick={() => setPreviewPayment(null)}>Close</Button>
                <Button onClick={() => approve.mutate(previewPayment.id)} disabled={approve.isPending}>
                  <Check className="size-3 mr-1" />Approve payment
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </Section>
  );
}

/* ------------ Courses ------------ */
function AdminCourses() {
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["courses"], queryFn: () => lmsApi.courses.list() });
  const list = asList(q.data);
  const [open, setOpen] = useState(false);
  const [editingCourseId, setEditingCourseId] = useState<any>(null);
  const [form, setForm] = useState({ title: "", description: "", price: 0, category: "", status: "draft" });
  const [editForm, setEditForm] = useState({ title: "", description: "", price: 0, category: "", status: "draft" });
  const create = useMutation({
    mutationFn: () => lmsApi.courses.adminCreate({
      ...form,
      slug: makeCourseSlug(form.title),
    }),
    onSuccess: () => { toast.success("Course created"); setOpen(false); setForm({ title: "", description: "", price: 0, category: "", status: "draft" }); qc.invalidateQueries({ queryKey: ["courses"] }); },
    onError: (e: any) => toast.error(e.message),
  });
  const update = useMutation({
    mutationFn: ({ id, payload }: { id: any; payload: any }) => lmsApi.courses.adminUpdate(id, payload),
    onSuccess: () => {
      toast.success("Course updated");
      setEditingCourseId(null);
      qc.invalidateQueries({ queryKey: ["courses"] });
    },
    onError: (e: any) => toast.error(e.message),
  });
  const publish = useMutation({
    mutationFn: (id: any) => lmsApi.courses.adminPublish(id),
    onSuccess: () => { toast.success("Published"); qc.invalidateQueries({ queryKey: ["courses"] }); },
    onError: (e: any) => toast.error(e.message),
  });
  async function uploadThumb(id: any, file: File) {
    try { await lmsApi.courses.adminUploadThumbnail(id, file); toast.success("Thumbnail updated"); qc.invalidateQueries({ queryKey: ["courses"] }); }
    catch (e: any) { toast.error(e.message); }
  }

  return (
    <Section title="Courses" loading={q.isLoading} empty={!list.length} action={
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild><Button><Plus className="size-4 mr-1" />New course</Button></DialogTrigger>
        <DialogContent>
          <DialogHeader><DialogTitle>Create course</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <div className="space-y-2"><Label>Title</Label><Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></div>
            <div className="space-y-2"><Label>Description</Label><Textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2"><Label>Price</Label><Input type="number" value={form.price} onChange={(e) => setForm({ ...form, price: Number(e.target.value) })} /></div>
              <div className="space-y-2"><Label>Category</Label><Input value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} /></div>
            </div>
            <div className="space-y-2">
              <Label>Status</Label>
              <Select value={form.status} onValueChange={(v) => setForm({ ...form, status: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="draft">Draft</SelectItem>
                  <SelectItem value="published">Published</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter><Button onClick={() => create.mutate()} disabled={create.isPending}>Create</Button></DialogFooter>
        </DialogContent>
      </Dialog>
    }>
      <table className="w-full text-sm">
        <thead className="bg-secondary/60 text-left"><tr>
          <th className="p-3">Title</th><th className="p-3">Price</th><th className="p-3">Status</th><th className="p-3">Actions</th>
        </tr></thead>
        <tbody>{list.map((c) => (
          <tr key={c.id} className="border-t border-border">
            <td className="p-3">
              <div className="font-medium">{c.title}</div>
              <div className="text-xs text-muted-foreground">{c.slug}</div>
            </td>
            <td className="p-3">${c.price}</td>
            <td className="p-3"><Badge variant={c.status === "published" ? "default" : "secondary"}>{c.status}</Badge></td>
            <td className="p-3 flex gap-2 items-center">
              <Dialog
                open={editingCourseId === c.id}
                onOpenChange={(open) => {
                  if (!open) return setEditingCourseId(null);
                  setEditingCourseId(c.id);
                  setEditForm({
                    title: c.title || "",
                    description: c.description || "",
                    price: Number(c.price || 0),
                    category: typeof c.category === "string" ? c.category : c.category?.name || "",
                    status: c.status || "draft",
                  });
                }}
              >
                <DialogTrigger asChild><Button size="sm" variant="outline">Edit</Button></DialogTrigger>
                <DialogContent>
                  <DialogHeader><DialogTitle>Update course</DialogTitle></DialogHeader>
                  <div className="space-y-3">
                    <div className="space-y-2"><Label>Title</Label><Input value={editForm.title} onChange={(e) => setEditForm({ ...editForm, title: e.target.value })} /></div>
                    <div className="space-y-2"><Label>Description</Label><Textarea value={editForm.description} onChange={(e) => setEditForm({ ...editForm, description: e.target.value })} /></div>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-2"><Label>Price</Label><Input type="number" value={editForm.price} onChange={(e) => setEditForm({ ...editForm, price: Number(e.target.value) })} /></div>
                      <div className="space-y-2"><Label>Category</Label><Input value={editForm.category} onChange={(e) => setEditForm({ ...editForm, category: e.target.value })} /></div>
                    </div>
                    <div className="space-y-2">
                      <Label>Status</Label>
                      <Select value={editForm.status} onValueChange={(v) => setEditForm({ ...editForm, status: v })}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="draft">Draft</SelectItem>
                          <SelectItem value="published">Published</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button onClick={() => update.mutate({ id: c.id, payload: editForm })} disabled={update.isPending}>Save changes</Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
              {c.status !== "published" && <Button size="sm" variant="outline" onClick={() => publish.mutate(c.id)}>Publish</Button>}
              <label className="text-xs px-2 py-1 border border-border rounded cursor-pointer hover:bg-secondary">
                Thumbnail
                <input type="file" accept="image/*" className="hidden" onChange={(e) => e.target.files?.[0] && uploadThumb(c.id, e.target.files[0])} />
              </label>
            </td>
          </tr>
        ))}</tbody>
      </table>
    </Section>
  );
}

/* ------------ Lessons ------------ */
function AdminLessons() {
  const qc = useQueryClient();
  const courses = useQuery({ queryKey: ["courses"], queryFn: () => lmsApi.courses.list() });
  const courseList = asList(courses.data);
  const [form, setForm] = useState({ course: "", title: "", lesson_type: "video", is_preview: false, order: 1, duration: 0 });
  const [lessonFile, setLessonFile] = useState<File | null>(null);
  const [open, setOpen] = useState(false);
  const create = useMutation({
    mutationFn: () =>
      lmsApi.courses.adminCreateLesson({
        course: Number(form.course) || form.course,
        title: form.title,
        lesson_type: form.lesson_type,
        is_preview: form.is_preview,
        order: Number(form.order),
        duration: Number(form.duration) || undefined,
        file: lessonFile,
      }),
    onSuccess: () => {
      toast.success("Lesson created");
      setOpen(false);
      setLessonFile(null);
      setForm({ course: "", title: "", lesson_type: "video", is_preview: false, order: 1, duration: 0 });
      qc.invalidateQueries();
    },
    onError: (e: any) => toast.error(e.message),
  });

  return (
    <Section title="Lessons" loading={courses.isLoading} empty={false} action={
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild><Button><Plus className="size-4 mr-1" />New lesson</Button></DialogTrigger>
        <DialogContent>
          <DialogHeader><DialogTitle>Create lesson</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <div className="space-y-2">
              <Label>Course</Label>
              <Select value={form.course} onValueChange={(v) => setForm({ ...form, course: v })}>
                <SelectTrigger><SelectValue placeholder="Pick a course" /></SelectTrigger>
                <SelectContent>{courseList.map((c) => <SelectItem key={c.id} value={String(c.id)}>{c.title}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="space-y-2"><Label>Title</Label><Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Type</Label>
                <Select value={form.lesson_type} onValueChange={(v) => setForm({ ...form, lesson_type: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="video">Video</SelectItem>
                    <SelectItem value="document">Document</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2"><Label>Order</Label><Input type="number" value={form.order} onChange={(e) => setForm({ ...form, order: Number(e.target.value) })} /></div>
            </div>
            <div className="space-y-2"><Label>Duration (minutes)</Label><Input type="number" value={form.duration} onChange={(e) => setForm({ ...form, duration: Number(e.target.value) })} /></div>
            <div className="space-y-2"><Label>Lesson file</Label><Input type="file" onChange={(e) => setLessonFile(e.target.files?.[0] || null)} /></div>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_preview} onChange={(e) => setForm({ ...form, is_preview: e.target.checked })} /> Preview lesson</label>
          </div>
          <DialogFooter><Button onClick={() => create.mutate()} disabled={create.isPending}>Create</Button></DialogFooter>
        </DialogContent>
      </Dialog>
    }>
      <p className="text-sm text-muted-foreground p-4">Open a course in the catalog to view its lessons. Use the button above to add new lessons.</p>
    </Section>
  );
}

/* ------------ Enrollments ------------ */
function AdminEnrollments() {
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["admin-enrollments"], queryFn: () => lmsApi.enrollments.adminList() });
  const list = asList(q.data);
  const [form, setForm] = useState({ student_id: "", course_id: "" });
  const [open, setOpen] = useState(false);
  const create = useMutation({
    mutationFn: () => lmsApi.enrollments.adminCreate({ student_id: form.student_id, course_id: Number(form.course_id) || form.course_id }),
    onSuccess: () => { toast.success("Enrolled"); setOpen(false); qc.invalidateQueries({ queryKey: ["admin-enrollments"] }); },
    onError: (e: any) => toast.error(e.message),
  });
  const act = useMutation({
    mutationFn: (id: any) => lmsApi.enrollments.adminActivate(id),
    onSuccess: () => { toast.success("activated"); qc.invalidateQueries({ queryKey: ["admin-enrollments"] }); },
    onError: (e: any) => toast.error(e.message),
  });
  const deact = useMutation({
    mutationFn: (id: any) => lmsApi.enrollments.adminDeactivate(id),
    onSuccess: () => { toast.success("deactivated"); qc.invalidateQueries({ queryKey: ["admin-enrollments"] }); },
    onError: (e: any) => toast.error(e.message),
  });

  return (
    <Section title="Enrollments" loading={q.isLoading} empty={!list.length} action={
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild><Button><Plus className="size-4 mr-1" />Grant enrollment</Button></DialogTrigger>
        <DialogContent>
          <DialogHeader><DialogTitle>Grant enrollment</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <div className="space-y-2"><Label>Student ID</Label><Input value={form.student_id} onChange={(e) => setForm({ ...form, student_id: e.target.value })} /></div>
            <div className="space-y-2"><Label>Course ID</Label><Input value={form.course_id} onChange={(e) => setForm({ ...form, course_id: e.target.value })} /></div>
          </div>
          <DialogFooter><Button onClick={() => create.mutate()} disabled={create.isPending}>Grant</Button></DialogFooter>
        </DialogContent>
      </Dialog>
    }>
      <table className="w-full text-sm">
        <thead className="bg-secondary/60 text-left"><tr>
          <th className="p-3">Student</th><th className="p-3">Course</th><th className="p-3">Enrolled</th><th className="p-3">Active</th><th className="p-3">Actions</th>
        </tr></thead>
        <tbody>{list.map((e) => (
          <tr key={e.id} className="border-t border-border">
            <td className="p-3">{e.student?.username || e.student_username || e.student}</td>
            <td className="p-3">{e.course?.title || e.course_title || e.course}</td>
            <td className="p-3 text-muted-foreground">{e.enrolled_at?.slice(0, 10)}</td>
            <td className="p-3">{e.is_active === false ? <Badge variant="destructive">No</Badge> : <Badge>Yes</Badge>}</td>
            <td className="p-3 flex gap-2">
              <Button size="sm" variant="outline" onClick={() => act.mutate(e.id)}>Activate</Button>
              <Button size="sm" variant="outline" onClick={() => deact.mutate(e.id)}>Deactivate</Button>
            </td>
          </tr>
        ))}</tbody>
      </table>
    </Section>
  );
}

/* ------------ Users ------------ */
function AdminUsers() {
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["admin-users"], queryFn: () => lmsApi.auth.adminListUsers() });
  const list = asList(q.data);
  const [selectedUserId, setSelectedUserId] = useState<any>(null);
  const userDetail = useQuery({
    queryKey: ["admin-user-detail", selectedUserId],
    queryFn: () => lmsApi.auth.adminUserDetail(selectedUserId),
    enabled: !!selectedUserId,
  });
  const act = useMutation({
    mutationFn: (id: any) => lmsApi.auth.adminActivateUser(id),
    onSuccess: () => { toast.success("activated"); qc.invalidateQueries({ queryKey: ["admin-users"] }); },
    onError: (e: any) => toast.error(e.message),
  });
  const deact = useMutation({
    mutationFn: (id: any) => lmsApi.auth.adminDeactivateUser(id),
    onSuccess: () => { toast.success("deactivated"); qc.invalidateQueries({ queryKey: ["admin-users"] }); },
    onError: (e: any) => toast.error(e.message),
  });
  return (
    <Section title="Users" loading={q.isLoading} empty={!list.length}>
      <table className="w-full text-sm">
        <thead className="bg-secondary/60 text-left"><tr>
          <th className="p-3">Username</th><th className="p-3">Email</th><th className="p-3">Name</th><th className="p-3">Active</th><th className="p-3">Actions</th>
        </tr></thead>
        <tbody>{list.map((u) => (
          <tr key={u.id} className="border-t border-border">
            <td className="p-3 font-medium">{u.username}</td>
            <td className="p-3 text-muted-foreground">{u.email}</td>
            <td className="p-3">{[u.first_name, u.last_name].filter(Boolean).join(" ")}</td>
            <td className="p-3">{u.is_active === false ? <Badge variant="destructive">No</Badge> : <Badge>Yes</Badge>}</td>
            <td className="p-3 flex gap-2">
              <Dialog open={selectedUserId === u.id} onOpenChange={(open) => setSelectedUserId(open ? u.id : null)}>
                <DialogTrigger asChild><Button size="sm" variant="outline">Detail</Button></DialogTrigger>
                <DialogContent>
                  <DialogHeader><DialogTitle>User detail</DialogTitle></DialogHeader>
                  {userDetail.isLoading && <p className="text-sm text-muted-foreground">Loading…</p>}
                  {!userDetail.isLoading && (
                    <pre className="text-xs bg-secondary/40 p-3 rounded-md overflow-auto max-h-72">{JSON.stringify(userDetail.data, null, 2)}</pre>
                  )}
                </DialogContent>
              </Dialog>
              <Button size="sm" variant="outline" onClick={() => act.mutate(u.id)}><ShieldOn className="size-3 mr-1" />Activate</Button>
              <Button size="sm" variant="outline" onClick={() => deact.mutate(u.id)}><ShieldOff className="size-3 mr-1" />Deactivate</Button>
            </td>
          </tr>
        ))}</tbody>
      </table>
    </Section>
  );
}

/* ------------ Banks ------------ */
function AdminBanks() {
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["admin-banks"], queryFn: () => lmsApi.payments.adminBankAccounts() });
  const list = asList(q.data);
  const [open, setOpen] = useState(false);
  const [selectedBankId, setSelectedBankId] = useState<any>(null);
  const bankDetail = useQuery({
    queryKey: ["admin-bank-detail", selectedBankId],
    queryFn: () => lmsApi.payments.adminBankAccountDetail(selectedBankId),
    enabled: !!selectedBankId,
  });
  const [form, setForm] = useState({ bank_name: "", account_title: "", account_number: "", iban: "", instructions: "", is_active: true });
  const create = useMutation({
    mutationFn: () => lmsApi.payments.adminCreateBankAccount(form),
    onSuccess: () => { toast.success("Bank account added"); setOpen(false); qc.invalidateQueries({ queryKey: ["admin-banks"] }); },
    onError: (e: any) => toast.error(e.message),
  });
  return (
    <Section title="Bank accounts" loading={q.isLoading} empty={!list.length} action={
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild><Button><Plus className="size-4 mr-1" />New bank</Button></DialogTrigger>
        <DialogContent>
          <DialogHeader><DialogTitle>Add bank account</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <div className="space-y-2"><Label>Bank name</Label><Input value={form.bank_name} onChange={(e) => setForm({ ...form, bank_name: e.target.value })} /></div>
            <div className="space-y-2"><Label>Account title</Label><Input value={form.account_title} onChange={(e) => setForm({ ...form, account_title: e.target.value })} /></div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2"><Label>Account #</Label><Input value={form.account_number} onChange={(e) => setForm({ ...form, account_number: e.target.value })} /></div>
              <div className="space-y-2"><Label>IBAN</Label><Input value={form.iban} onChange={(e) => setForm({ ...form, iban: e.target.value })} /></div>
            </div>
            <div className="space-y-2"><Label>Instructions</Label><Textarea value={form.instructions} onChange={(e) => setForm({ ...form, instructions: e.target.value })} /></div>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} /> Active</label>
          </div>
          <DialogFooter><Button onClick={() => create.mutate()} disabled={create.isPending}>Create</Button></DialogFooter>
        </DialogContent>
      </Dialog>
    }>
      <table className="w-full text-sm">
        <thead className="bg-secondary/60 text-left"><tr>
          <th className="p-3">Bank</th><th className="p-3">Title</th><th className="p-3">Account</th><th className="p-3">IBAN</th><th className="p-3">Active</th><th className="p-3">Action</th>
        </tr></thead>
        <tbody>{list.map((b) => (
          <tr key={b.id} className="border-t border-border">
            <td className="p-3 font-medium">{b.bank_name}</td>
            <td className="p-3">{b.account_title}</td>
            <td className="p-3 font-mono text-xs">{b.account_number}</td>
            <td className="p-3 font-mono text-xs">{b.iban}</td>
            <td className="p-3">{b.is_active ? <Badge>Yes</Badge> : <Badge variant="secondary">No</Badge>}</td>
            <td className="p-3">
              <Dialog open={selectedBankId === b.id} onOpenChange={(open) => setSelectedBankId(open ? b.id : null)}>
                <DialogTrigger asChild><Button size="sm" variant="outline">Detail</Button></DialogTrigger>
                <DialogContent>
                  <DialogHeader><DialogTitle>Bank account detail</DialogTitle></DialogHeader>
                  {bankDetail.isLoading && <p className="text-sm text-muted-foreground">Loading…</p>}
                  {!bankDetail.isLoading && (
                    <pre className="text-xs bg-secondary/40 p-3 rounded-md overflow-auto max-h-72">{JSON.stringify(bankDetail.data, null, 2)}</pre>
                  )}
                </DialogContent>
              </Dialog>
            </td>
          </tr>
        ))}</tbody>
      </table>
    </Section>
  );
}

/* ------------ Shared shell ------------ */
function Section({ title, action, children, loading, empty }: { title: string; action?: React.ReactNode; children: React.ReactNode; loading?: boolean; empty?: boolean }) {
  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-border">
        <h2 className="font-serif text-xl text-primary">{title}</h2>
        {action}
      </div>
      {loading ? <div className="p-6 text-muted-foreground">Loading…</div> :
        empty ? <div className="p-10 text-center text-muted-foreground">Nothing here yet.</div> :
          <div className="overflow-x-auto">{children}</div>}
    </div>
  );
}