import { Link, useNavigate, useRouterState } from "@tanstack/react-router";
import { GraduationCap, LogOut, Shield, User as UserIcon } from "lucide-react";
import { useState, type ReactNode } from "react";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { resolveMediaUrl } from "@/lib/media";

export function AppShell({ children }: { children: ReactNode }) {
  const { user, isAdmin, logout } = useAuth();
  const nav = useNavigate();
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  const NavLink = ({ to, label }: { to: string; label: string }) => (
    <Link
      to={to}
      className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
        pathname === to || (to !== "/" && pathname.startsWith(to))
          ? "text-primary bg-secondary"
          : "text-muted-foreground hover:text-foreground hover:bg-secondary/60"
      }`}
    >
      {label}
    </Link>
  );

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <header className="border-b border-border bg-card/60 backdrop-blur sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-2 group">
            <span className="size-9 rounded-lg bg-primary text-primary-foreground grid place-items-center shadow-sm">
              <GraduationCap className="size-5" />
            </span>
            <span className="font-serif text-xl tracking-tight">
              <span className="text-primary">Mini</span>
              <span className="text-accent ml-1">LMS</span>
            </span>
          </Link>
          <nav className="hidden md:flex items-center gap-1">
            <NavLink to="/" label="Catalog" />
            {user && <NavLink to="/dashboard" label="Dashboard" />}
            {isAdmin && <NavLink to="/admin" label="Admin" />}
          </nav>
          <div className="flex items-center gap-2">
            {user ? (
              <>
                {isAdmin && (
                  <span className="hidden sm:inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-accent/30 text-accent-foreground border border-accent/50">
                    <Shield className="size-3" /> Admin
                  </span>
                )}
                <Link to={isAdmin ? "/admin" : "/dashboard"} className="flex items-center gap-2 text-sm font-medium hover:text-primary">
                  <span className="w-14 h-14 rounded-full bg-secondary grid place-items-center overflow-hidden border border-border shrink-0">
                    {user?.profile_image ? (
                      <img src={resolveMediaUrl(user.profile_image)} alt={user.username} className="w-full h-full object-cover" loading="eager" decoding="async" />
                    ) : (
                      <UserIcon className="size-6" />
                    )}
                  </span>
                  <span className="hidden sm:inline">{user.username}</span>
                </Link>
                <Button variant="ghost" size="icon" onClick={() => { logout(); nav({ to: "/" }); }} title="Sign out">
                  <LogOut className="size-4" />
                </Button>
              </>
            ) : (
              <>
                <Link to="/login"><Button variant="ghost">Sign in</Button></Link>
                <Link to="/register"><Button>Get started</Button></Link>
              </>
            )}
          </div>
        </div>
      </header>
      <main className="flex-1">{children}</main>
      <footer className="border-t border-border py-8 text-center text-xs text-muted-foreground">
        Mini LMS · Django + DRF · AWS S3 · JWT
      </footer>
    </div>
  );
}