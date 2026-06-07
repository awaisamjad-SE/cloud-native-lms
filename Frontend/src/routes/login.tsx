import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { AppShell } from "@/components/AppShell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

export const Route = createFileRoute("/login")({
  head: () => ({ meta: [{ title: "Sign in · Mini LMS" }] }),
  component: LoginPage,
});

function LoginPage() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [username, setU] = useState("");
  const [password, setP] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const loggedInUser = await login(username, password);
      const isAdmin = !!(
        loggedInUser?.staff_member ||
        loggedInUser?.is_staff ||
        loggedInUser?.is_superuser ||
        loggedInUser?.role === "admin"
      );
      toast.success("Welcome back!");
      nav({ to: isAdmin ? "/admin" : "/dashboard" });
    } catch (err: any) {
      toast.error(err.message || "Login failed");
    } finally { setLoading(false); }
  }

  return (
    <AppShell>
      <div className="max-w-md mx-auto px-4 py-16">
        <h1 className="font-serif text-3xl text-primary">Sign in</h1>
        <p className="text-muted-foreground text-sm mt-1">Access your enrolled courses and progress.</p>
        <form onSubmit={submit} className="mt-8 space-y-4 bg-card border border-border rounded-xl p-6">
          <div className="space-y-2">
            <Label>Username</Label>
            <Input value={username} onChange={(e) => setU(e.target.value)} required autoFocus />
          </div>
          <div className="space-y-2">
            <Label>Password</Label>
            <Input type="password" value={password} onChange={(e) => setP(e.target.value)} required />
          </div>
          <Button type="submit" className="w-full" disabled={loading}>{loading ? "Signing in…" : "Sign in"}</Button>
          <p className="text-sm text-muted-foreground text-center">
            New here? <Link to="/register" className="text-primary hover:underline">Create an account</Link>
          </p>
        </form>
      </div>
    </AppShell>
  );
}