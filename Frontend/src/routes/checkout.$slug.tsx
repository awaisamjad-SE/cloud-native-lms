import { createFileRoute, Link, useNavigate, useParams } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { Building2 } from "lucide-react";
import { lmsApi } from "@/lib/lms-api";

export const Route = createFileRoute("/checkout/$slug")({
  component: CheckoutPage,
});

function CheckoutPage() {
  const { slug } = useParams({ from: "/checkout/$slug" });
  const nav = useNavigate();
  const course = useQuery({ queryKey: ["course", slug], queryFn: () => lmsApi.courses.detail(slug) });
  const banks = useQuery({ queryKey: ["banks"], queryFn: () => lmsApi.payments.publicBankAccounts() });
  const bankList: any[] = Array.isArray(banks.data) ? banks.data : banks.data?.results || [];

  const [bankId, setBankId] = useState<string | number | null>(null);
  const [ref, setRef] = useState("");
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!bankId) return toast.error("Pick a bank account");
    if (!course.data?.id) return toast.error("Course not loaded");
    if (fileError) return toast.error(fileError);
    setLoading(true);
    try {
      await lmsApi.payments.submitOffline({
        course_id: course.data.id,
        bank_account_id: bankId,
        transaction_reference: ref,
        proof_note: note,
        proof_receipt: file ?? undefined,
      });
      toast.success("Payment submitted! Awaiting admin approval.");
      nav({ to: "/dashboard" });
    } catch (e: any) { toast.error(e.message); }
    finally { setLoading(false); }
  }

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto px-4 py-10">
        <Link to="/courses/$slug" params={{ slug }} className="text-sm text-muted-foreground hover:text-primary">&larr; Back to course</Link>
        <h1 className="font-serif text-3xl text-primary mt-2">Checkout</h1>
        {course.data && (
          <div className="mt-2 text-muted-foreground">
            <strong className="text-foreground">{course.data.title}</strong> · ${course.data.price}
          </div>
        )}

        <form onSubmit={submit} className="mt-8 space-y-6">
          <div>
            <h2 className="font-serif text-xl text-primary mb-3">1. Transfer to one of these accounts</h2>
            <div className="grid sm:grid-cols-2 gap-3">
              {bankList.length === 0 && <div className="text-muted-foreground text-sm col-span-2">No bank accounts configured.</div>}
              {bankList.map((b) => (
                <button
                  type="button"
                  key={b.id}
                  onClick={() => setBankId(b.id)}
                  className={`text-left p-4 rounded-lg border transition-colors ${bankId === b.id ? "border-primary bg-primary/5" : "border-border bg-card hover:border-primary/40"}`}
                >
                  <div className="flex items-center gap-2 text-primary"><Building2 className="size-4" /><span className="font-medium">{b.bank_name}</span></div>
                  <div className="text-sm mt-1">{b.account_title}</div>
                  <div className="text-xs text-muted-foreground mt-1">Acct: {b.account_number}</div>
                  {b.iban && <div className="text-xs text-muted-foreground">IBAN: {b.iban}</div>}
                  {b.instructions && <div className="text-xs text-muted-foreground mt-2">{b.instructions}</div>}
                </button>
              ))}
            </div>
          </div>

          <div>
            <h2 className="font-serif text-xl text-primary mb-3">2. Submit your proof</h2>
            <div className="space-y-3 bg-card border border-border rounded-xl p-5">
              <div className="space-y-2"><Label>Transaction reference</Label><Input value={ref} onChange={(e) => setRef(e.target.value)} placeholder="TXN-123456" required /></div>
              <div className="space-y-2"><Label>Note (optional)</Label><Textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="Any notes for the admin…" /></div>
              <div className="space-y-2">
                <Label>Upload proof (image or PDF, max 2 MB)</Label>
                <input
                  type="file"
                  accept="image/*,application/pdf"
                  onChange={(e) => {
                    const f = e.target.files?.[0] ?? null;
                    if (!f) { setFile(null); setFileError(null); return; }
                    const max = 2 * 1024 * 1024; // 2 MB
                    if (f.size > max) {
                      setFile(null);
                      setFileError("File is too large. Maximum size is 2 MB.");
                      return;
                    }
                    setFileError(null);
                    setFile(f);
                  }}
                  className="w-full"
                />
                {file && <div className="text-sm text-muted-foreground">Selected: {file.name} ({(file.size/1024).toFixed(0)} KB)</div>}
                {fileError && <div className="text-sm text-destructive">{fileError}</div>}
              </div>
              <Button type="submit" className="w-full" disabled={loading}>{loading ? "Submitting…" : "Submit payment"}</Button>
              <p className="text-xs text-muted-foreground">Your enrollment will activate after admin approval.</p>
            </div>
          </div>
        </form>
      </div>
    </AppShell>
  );
}