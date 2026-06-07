import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { AppShell } from "@/components/AppShell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

export const Route = createFileRoute("/register")({
  head: () => ({ meta: [{ title: "Create account · Mini LMS" }] }),
  component: RegisterPage,
});

function RegisterPage() {
  const { register } = useAuth();
  const nav = useNavigate();
  const [form, setForm] = useState({ username: "", email: "", password: "", first_name: "", last_name: "" });
  const [loading, setLoading] = useState(false);

  const upd = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await register(form);
      toast.success("Account created!");
      nav({ to: "/" });
    } catch (err: any) {
      toast.error(err.message || "Registration failed");
    } finally { setLoading(false); }
  }

  return (
    <AppShell>
      <div className="max-w-md mx-auto px-4 py-16">
        <h1 className="font-serif text-3xl text-primary">Create account</h1>
        <p className="text-muted-foreground text-sm mt-1">Join Mini LMS and start learning.</p>
        <form onSubmit={submit} className="mt-8 space-y-4 bg-card border border-border rounded-xl p-6">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2"><Label>First name</Label><Input value={form.first_name} onChange={upd("first_name")} /></div>
            <div className="space-y-2"><Label>Last name</Label><Input value={form.last_name} onChange={upd("last_name")} /></div>
          </div>
          <div className="space-y-2"><Label>Username</Label><Input value={form.username} onChange={upd("username")} required /></div>
          <div className="space-y-2"><Label>Email</Label><Input type="email" value={form.email} onChange={upd("email")} required /></div>
          <div className="space-y-2"><Label>Password</Label><Input type="password" value={form.password} onChange={upd("password")} required minLength={6} /></div>
          <Button type="submit" className="w-full" disabled={loading}>{loading ? "Creating…" : "Create account"}</Button>
          <p className="text-sm text-muted-foreground text-center">
            Already have an account? <Link to="/login" className="text-primary hover:underline">Sign in</Link>
          </p>
        </form>
      </div>
    </AppShell>
  );
}