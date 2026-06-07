import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { useAuth } from "@/lib/auth";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { lmsApi } from "@/lib/lms-api";
import { resolveMediaUrl } from "@/lib/media";

export const Route = createFileRoute("/dashboard")({
  head: () => ({ meta: [{ title: "Dashboard · Mini LMS" }] }),
  component: DashboardPage,
});

function DashboardPage() {
  const { user, loading, refresh, isAdmin } = useAuth();
  const nav = useNavigate();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      nav({ to: "/login" });
      return;
    }
    if (isAdmin) nav({ to: "/admin" });
  }, [loading, user, isAdmin, nav]);

  const enrollments = useQuery({ queryKey: ["my-enrollments"], queryFn: () => lmsApi.enrollments.my(), enabled: !!user });
  const payments = useQuery({ queryKey: ["my-payments"], queryFn: () => lmsApi.payments.my(), enabled: !!user });

  const eList: any[] = Array.isArray(enrollments.data) ? enrollments.data : enrollments.data?.results || [];
  const pList: any[] = Array.isArray(payments.data) ? payments.data : payments.data?.results || [];

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto px-4 py-10">
        <h1 className="font-serif text-3xl text-primary">Welcome, {user?.first_name || user?.username}</h1>
        <p className="text-muted-foreground text-sm mt-1">Track your learning, payments, and profile.</p>

        <Tabs defaultValue="enrollments" className="mt-8">
          <TabsList>
            <TabsTrigger value="enrollments">My courses</TabsTrigger>
            <TabsTrigger value="payments">Payments</TabsTrigger>
            <TabsTrigger value="profile">Profile</TabsTrigger>
          </TabsList>

          <TabsContent value="enrollments" className="mt-6">
            {enrollments.isLoading && <div className="text-muted-foreground">Loading…</div>}
            {eList.length === 0 && !enrollments.isLoading && (
              <div className="bg-card border border-border rounded-xl p-10 text-center text-muted-foreground">
                You're not enrolled in any course yet. <Link to="/" className="text-primary hover:underline">Browse catalog</Link>.
              </div>
            )}
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {eList.map((e) => {
                const c = e.course || {};
                const slug = c.slug || e.course_slug;
                return (
                  <div key={e.id} className="bg-card border border-border rounded-xl overflow-hidden">
                    <div className="aspect-video bg-gradient-to-br from-primary/20 to-accent/20">
                      {(c.thumbnail_url || c.thumbnail) && <img src={resolveMediaUrl(c.thumbnail_url || c.thumbnail)} alt="" className="w-full h-full object-cover" />}
                    </div>
                    <div className="p-4">
                      <div className="font-medium">{c.title || e.course_title}</div>
                      <div className="text-xs text-muted-foreground mt-1">Enrolled {e.enrolled_at?.slice(0, 10)}</div>
                      {slug && (
                        <Link to="/courses/$slug" params={{ slug }}>
                          <Button size="sm" variant="outline" className="mt-3 w-full">Continue</Button>
                        </Link>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </TabsContent>

          <TabsContent value="payments" className="mt-6">
            <PaymentTable items={pList} loading={payments.isLoading} />
          </TabsContent>

          <TabsContent value="profile" className="mt-6">
            <ProfileEditor onSaved={refresh} />
          </TabsContent>
        </Tabs>
      </div>
    </AppShell>
  );
}

function PaymentTable({ items, loading }: { items: any[]; loading: boolean }) {
  if (loading) return <div className="text-muted-foreground">Loading…</div>;
  if (!items.length) return <div className="bg-card border border-border rounded-xl p-10 text-center text-muted-foreground">No payments yet.</div>;
  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-secondary/60 text-left">
          <tr><th className="p-3">Course</th><th className="p-3">Amount</th><th className="p-3">Reference</th><th className="p-3">Status</th><th className="p-3">Date</th></tr>
        </thead>
        <tbody>
          {items.map((p) => (
            <tr key={p.id} className="border-t border-border">
              <td className="p-3">{p.course?.title || p.course_title || p.course}</td>
              <td className="p-3">${p.amount}</td>
              <td className="p-3 font-mono text-xs">{p.transaction_reference}</td>
              <td className="p-3"><Badge variant={p.status === "approved" || p.status === "completed" ? "default" : p.status === "rejected" || p.status === "failed" ? "destructive" : "secondary"}>{p.status}</Badge></td>
              <td className="p-3 text-muted-foreground">{p.created_at?.slice(0, 10)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ProfileEditor({ onSaved }: { onSaved: () => void }) {
  const { user } = useAuth();
  const [form, setForm] = useState({ first_name: "", last_name: "", phone_number: "", bio: "" });
  const [pwd, setPwd] = useState({ old_password: "", new_password: "" });
  const [busy, setBusy] = useState(false);
  const [presigned, setPresigned] = useState("");
  const [imageLoadError, setImageLoadError] = useState(false);
  const profileImageUrl = user?.profile_image ? resolveMediaUrl(user.profile_image) : "";

  useEffect(() => {
    if (user) setForm({
      first_name: user.first_name || "", last_name: user.last_name || "",
      phone_number: user.phone_number || "", bio: user.bio || "",
    });
  }, [user]);

  useEffect(() => {
    setImageLoadError(false);
  }, [user?.profile_image]);

  async function save(e: React.FormEvent) {
    e.preventDefault(); setBusy(true);
    try { await lmsApi.auth.patchProfile(form); toast.success("Profile updated"); onSaved(); }
    catch (e: any) { toast.error(e.message); } finally { setBusy(false); }
  }

  async function changePw(e: React.FormEvent) {
    e.preventDefault(); setBusy(true);
    try { await lmsApi.auth.changePassword(pwd); toast.success("Password updated"); setPwd({ old_password: "", new_password: "" }); }
    catch (e: any) { toast.error(e.message); } finally { setBusy(false); }
  }

  async function uploadImage(file: File) {
    try { await lmsApi.auth.uploadProfileImage(file); toast.success("Image uploaded"); onSaved(); }
    catch (e: any) { toast.error(e.message); }
  }

  async function loadPresigned() {
    try {
      const data = await lmsApi.auth.getProfileUploadPresigned();
      setPresigned(JSON.stringify(data, null, 2));
      toast.success("Presigned payload loaded");
    } catch (e: any) {
      toast.error(e.message);
    }
  }

  return (
    <div className="grid md:grid-cols-2 gap-6">
      <form onSubmit={save} className="bg-card border border-border rounded-xl p-6 space-y-4">
        <h3 className="font-serif text-xl text-primary">Profile</h3>
        {profileImageUrl && (
          <div className="flex items-center gap-3 rounded-lg border border-border bg-secondary/20 p-3">
            {!imageLoadError ? (
              <img
                key={profileImageUrl}
                src={profileImageUrl}
                alt={user.username}
                className="w-48 h-48 flex-none rounded-2xl object-cover border border-border bg-background p-1 shadow-sm"
                loading="eager"
                decoding="async"
                onError={() => setImageLoadError(true)}
              />
            ) : (
              <div className="w-48 h-48 flex-none rounded-2xl border border-border bg-background grid place-items-center text-3xl font-semibold text-muted-foreground">
                X
              </div>
            )}
            <div>
              <div className="text-sm font-medium">{user.username}</div>
              <div className="text-xs text-muted-foreground">Current profile image</div>
            </div>
          </div>
        )}
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2"><Label>First name</Label><Input value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} /></div>
          <div className="space-y-2"><Label>Last name</Label><Input value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} /></div>
        </div>
        <div className="space-y-2"><Label>Phone</Label><Input value={form.phone_number} onChange={(e) => setForm({ ...form, phone_number: e.target.value })} /></div>
        <div className="space-y-2"><Label>Bio</Label><Textarea value={form.bio} onChange={(e) => setForm({ ...form, bio: e.target.value })} /></div>
        <div className="space-y-2">
          <Label>Profile image</Label>
          <Input type="file" accept="image/*" onChange={(e) => e.target.files?.[0] && uploadImage(e.target.files[0])} />
          <Button type="button" variant="ghost" size="sm" className="px-0" onClick={loadPresigned}>Get presigned upload data</Button>
          {presigned && <Textarea value={presigned} readOnly className="font-mono text-xs h-32" />}
        </div>
        <Button type="submit" disabled={busy}>{busy ? "Saving…" : "Save profile"}</Button>
      </form>

      <form onSubmit={changePw} className="bg-card border border-border rounded-xl p-6 space-y-4">
        <h3 className="font-serif text-xl text-primary">Change password</h3>
        <div className="space-y-2"><Label>Current password</Label><Input type="password" value={pwd.old_password} onChange={(e) => setPwd({ ...pwd, old_password: e.target.value })} required /></div>
        <div className="space-y-2"><Label>New password</Label><Input type="password" value={pwd.new_password} onChange={(e) => setPwd({ ...pwd, new_password: e.target.value })} required minLength={6} /></div>
        <Button type="submit" variant="outline" disabled={busy}>Update password</Button>
      </form>
    </div>
  );
}