import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import Alert from "../components/Alert";
import TicketDrawer from "../components/TicketDrawer";
import TicketTable from "../components/TicketTable";
import { api, ApiError, clearToken, getToken, setToken } from "../lib/api";
import { STATUSES, STATUS_LABEL, type Ticket } from "../lib/types";

function LoginCard({ onLoggedIn }: { onLoggedIn: () => void }) {
  const [u, setU] = useState("");
  const [p, setP] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!u.trim() || !p) return setErr("Enter your username and password.");
    setBusy(true); setErr(null);
    try {
      const r = await api.login(u.trim(), p);
      setToken(r.access_token);
      onLoggedIn();
    } catch (x) { setErr(x instanceof Error ? x.message : "Login failed."); }
    finally { setBusy(false); }
  };

  return (
    <main className="center-note">
      <form className="card login" onSubmit={submit} noValidate>
        <div className="lock">🔐</div>
        <h2>Team sign in</h2>
        <p className="muted">Sign in to manage support tickets.</p>
        {err && <Alert kind="error" onClose={() => setErr(null)}>{err}</Alert>}
        <div className="field"><label htmlFor="u">Username</label>
          <input id="u" className="input" value={u} onChange={(e) => setU(e.target.value)} autoComplete="username" /></div>
        <div className="field"><label htmlFor="p">Password</label>
          <input id="p" className="input" type="password" value={p} onChange={(e) => setP(e.target.value)} autoComplete="current-password" /></div>
        <button className="btn btn-primary wide" disabled={busy}>{busy ? <><span className="spinner" /> Signing in…</> : "Sign in"}</button>
      </form>
    </main>
  );
}

function Dashboard({ onLogout }: { onLogout: () => void }) {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<number | null>(null);

  const guard = useCallback((e: unknown) => {
    if (e instanceof ApiError && e.status === 401) return onLogout();
    setError(e instanceof Error ? e.message : "Something went wrong.");
  }, [onLogout]);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try { setTickets(await api.listTickets({ category: category || undefined, status: status || undefined })); }
    catch (e) { guard(e); } finally { setLoading(false); }
  }, [category, status, guard]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => { api.categories().then(setCategories).catch(guard); }, [guard]);

  const merge = useCallback((t: Ticket) => setTickets((prev) => prev.map((x) => (x.id === t.id ? t : x))), []);
  const stats = useMemo(() => {
    const c = (s: string) => tickets.filter((t) => t.status === s).length;
    return [
      { label: "Showing", value: tickets.length, tone: "indigo" },
      { label: "Open", value: c("open"), tone: "amber" },
      { label: "In progress", value: c("in_progress"), tone: "cyan" },
      { label: "Resolved", value: c("resolved") + c("closed"), tone: "green" },
    ];
  }, [tickets]);

  return (
    <main className="dash">
      <div className="dash-head">
        <div><h1>Tickets</h1><p className="muted">Review, triage and respond to customer messages.</p></div>
        <button className="btn btn-ghost" onClick={onLogout}>Sign out</button>
      </div>

      <div className="stats">
        {stats.map((s) => (
          <div key={s.label} className={`stat tone-${s.tone}`}><span>{s.label}</span><strong>{s.value}</strong></div>
        ))}
      </div>

      <div className="card toolbar">
        <label>Category
          <select className="input select" value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">All categories</option>
            {categories.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
        <label>Status
          <select className="input select" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">All statuses</option>
            {STATUSES.map((s) => <option key={s} value={s}>{STATUS_LABEL[s]}</option>)}
          </select>
        </label>
        <button className="btn btn-ghost" onClick={load} disabled={loading}>{loading ? "Refreshing…" : "Refresh"}</button>
      </div>

      {error && <Alert kind="error" onClose={() => setError(null)}>{error}</Alert>}
      <div className="card flush">
        {loading && tickets.length === 0 ? <div className="skeleton-lines pad"><i /><i /><i /><i /></div>
          : <TicketTable tickets={tickets} selectedId={selected} onSelect={setSelected} />}
      </div>

      {selected !== null && (
        <TicketDrawer ticketId={selected} onClose={() => setSelected(null)} onUpdated={merge} onUnauthorized={onLogout} />
      )}
    </main>
  );
}

export default function TeamPage() {
  const [authed, setAuthed] = useState(!!getToken());
  const logout = useCallback(() => { clearToken(); setAuthed(false); }, []);
  return authed ? <Dashboard onLogout={logout} /> : <LoginCard onLoggedIn={() => setAuthed(true)} />;
}
