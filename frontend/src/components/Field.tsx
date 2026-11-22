import type { ChangeEvent, FocusEvent } from "react";

interface Props {
  id: string;
  label: string;
  value: string;
  error?: string;
  type?: string;
  multiline?: boolean;
  placeholder?: string;
  maxLength?: number;
  counter?: { min: number; max: number };
  autoComplete?: string;
  onChange: (v: string) => void;
  onBlur?: () => void;
}

export default function Field({ id, label, value, error, type = "text", multiline, placeholder, counter, autoComplete, onChange, onBlur }: Props) {
  const common = {
    id, value, placeholder, autoComplete,
    "aria-invalid": !!error, "aria-describedby": error ? `${id}-err` : undefined,
    className: `input${error ? " has-error" : ""}`,
    onChange: (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => onChange(e.target.value),
    onBlur: (_: FocusEvent) => onBlur?.(),
  };
  const len = value.trim().length;
  const counterBad = counter && (len > counter.max || (len > 0 && len < counter.min));
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      {multiline ? <textarea rows={6} {...common} /> : <input type={type} {...common} />}
      <div className="field-foot">
        <span id={`${id}-err`} className="field-error" aria-live="polite">{error}</span>
        {counter && <span className={`counter${counterBad ? " bad" : ""}`}>{len}/{counter.max}</span>}
      </div>
    </div>
  );
}
