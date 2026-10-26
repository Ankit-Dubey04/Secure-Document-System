import { useState, type FormEvent } from "react";
import { LockKeyhole, ShieldCheck } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { ApiError } from "../services/api";
import { Button, Notice } from "../components/ui";

export function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState(""); const [password, setPassword] = useState("");
  const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault(); setError(""); setBusy(true);
    try { await login(email, password); } catch (err) { setError(err instanceof ApiError ? err.message : "Unable to sign in."); } finally { setBusy(false); }
  }
  return <main className="grid min-h-screen place-items-center bg-slate-950 px-5 text-slate-100">
    <form onSubmit={submit} className="w-full max-w-md rounded-2xl border border-slate-700 bg-slate-900 p-8 shadow-2xl shadow-cyan-950/30">
      <div className="mb-8 flex items-center gap-3"><div className="rounded-xl bg-cyan-400 p-3 text-slate-950"><ShieldCheck /></div><div><h1 className="text-xl font-bold">SENTINEL VAULT</h1><p className="text-sm text-slate-400">Secure Document Integrity Monitor</p></div></div>
      <h2 className="mb-5 text-2xl font-semibold">Secure sign in</h2>
      {error && <div className="mb-4"><Notice>{error}</Notice></div>}
      <label className="mb-4 block text-sm font-medium">Email<input required type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} className="mt-1.5 w-full rounded-lg border border-slate-600 bg-slate-950 px-3 py-2.5 outline-none focus:border-cyan-400" /></label>
      <label className="mb-6 block text-sm font-medium">Password<input required type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} className="mt-1.5 w-full rounded-lg border border-slate-600 bg-slate-950 px-3 py-2.5 outline-none focus:border-cyan-400" /></label>
      <Button disabled={busy} className="flex w-full items-center justify-center gap-2">{busy ? "Signing in…" : <><LockKeyhole size={17} /> Sign in</>}</Button>
      <p className="mt-5 text-xs leading-relaxed text-slate-500">Tokens are retained only for this browser session. Backend authorization remains authoritative.</p>
    </form>
  </main>;
}
