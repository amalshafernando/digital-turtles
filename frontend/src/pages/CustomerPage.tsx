import { FormEvent, useRef, useState } from "react";
import Alert from "../components/Alert";
import Field from "../components/Field";
import { api, ApiError } from "../lib/api";
import type { Receipt } from "../lib/types";
import { LIMITS, validateAll, validateField, type FormErrors, type FormValues } from "../lib/validation";

const EMPTY: FormValues = { name: "", email: "", message: "" };
const KEYS: (keyof FormValues)[] = ["name", "email", "message"];

export default function CustomerPage() {
  const [values, setValues] = useState<FormValues>(EMPTY);
  const [errors, setErrors] = useState<FormErrors>({});
  const [banner, setBanner] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [sentTo, setSentTo] = useState("");
  const formRef = useRef<HTMLFormElement>(null);

  const set = (k: keyof FormValues) => (v: string) => {
    setValues((p) => ({ ...p, [k]: v }));
    if (errors[k]) setErrors((p) => ({ ...p, [k]: validateField(k, v) }));   // re-validate live once an error is shown
  };
  const blur = (k: keyof FormValues) => () => setErrors((p) => ({ ...p, [k]: validateField(k, values[k]) }));

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setBanner(null);
    const clientErrors = validateAll(values);                 // 1) client-side validation
    setErrors(clientErrors);
    const first = KEYS.find((k) => clientErrors[k]);
    if (first) {
      setBanner("Please fix the highlighted fields and try again.");
      formRef.current?.querySelector<HTMLElement>(`#${first}`)?.focus();
      return;
    }
    setSubmitting(true);
    try {
      const body = { name: values.name.trim(), email: values.email.trim(), message: values.message.trim() };
      const r = await api.submitTicket(body);
      setSentTo(body.email);
      setReceipt(r);
      setValues(EMPTY); setErrors({});
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.fields.length) {                              // 2) server-side validation errors -> next to the fields
          const next: FormErrors = {};
          for (const f of err.fields) if ((KEYS as string[]).includes(f.field)) next[f.field as keyof FormValues] = f.message;
          setErrors(next);
          setBanner(err.message);
          const firstSrv = KEYS.find((k) => next[k]);
          if (firstSrv) formRef.current?.querySelector<HTMLElement>(`#${firstSrv}`)?.focus();
        } else {
          setBanner(err.message);                              // other errors (400, 500, network) -> banner
        }
      } else setBanner("Unexpected error. Please try again.");
    } finally { setSubmitting(false); }
  };

  return (
    <main className="customer">
      <section className="hero">
        <span className="pill">24/7 support · AI-assisted</span>
        <h1>How can we <span className="grad">help</span> you today?</h1>
        <p className="lead">Send us a message and our team will get back to you. Most questions are answered within one business day.</p>
        <ul className="perks">
          <li><b>⚡</b> Smart routing to the right specialist</li>
          <li><b>🔒</b> Your details are only used to reply to you</li>
          <li><b>🎯</b> Clear answers based on our official FAQ</li>
        </ul>
      </section>

      <section className="card form-card">
        {receipt ? (
          <div className="success" role="status">
            <div className="check">✓</div>
            <h2>Message received</h2>
            <p className="muted">{receipt.message}</p>
            <div className="ticket-id"><span>Your ticket ID</span><strong>#{receipt.id}</strong></div>
            <p className="hint">Keep this number for reference. We’ll reply to <b>{sentTo}</b>.</p>
            <button className="btn btn-primary" onClick={() => { setReceipt(null); setBanner(null); }}>Send another message</button>
          </div>
        ) : (
          <form ref={formRef} onSubmit={onSubmit} noValidate>
            <h2>Contact support</h2>
            {banner && <Alert kind="error" onClose={() => setBanner(null)}>{banner}</Alert>}
            <Field id="name" label="Your name" value={values.name} error={errors.name} placeholder="Jane Perera"
                   autoComplete="name" onChange={set("name")} onBlur={blur("name")} />
            <Field id="email" label="Email" type="email" value={values.email} error={errors.email} placeholder="jane@example.com"
                   autoComplete="email" onChange={set("email")} onBlur={blur("email")} />
            <Field id="message" label="Message" multiline value={values.message} error={errors.message}
                   placeholder="Tell us what happened…" counter={{ min: LIMITS.msgMin, max: LIMITS.msgMax }}
                   onChange={set("message")} onBlur={blur("message")} />
            <button className="btn btn-primary wide" type="submit" disabled={submitting}>
              {submitting ? <><span className="spinner" /> Sending…</> : "Send message"}
            </button>
          </form>
        )}
      </section>
    </main>
  );
}
