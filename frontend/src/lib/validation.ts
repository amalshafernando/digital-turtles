// Client-side validation. The server validates again (never trust the browser); both use the same limits.
export const LIMITS = { nameMax: 100, emailMax: 254, msgMin: 10, msgMax: 2000 } as const;

export type FormValues = { name: string; email: string; message: string };
export type FormErrors = Partial<Record<keyof FormValues, string>>;

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export function validateField(key: keyof FormValues, raw: string): string | undefined {
  const v = raw.trim();
  switch (key) {
    case "name":
      if (!v) return "Please enter your name.";
      if (v.length > LIMITS.nameMax) return `Name must be at most ${LIMITS.nameMax} characters.`;
      return undefined;
    case "email":
      if (!v) return "Please enter your email address.";
      if (v.length > LIMITS.emailMax || !EMAIL.test(v)) return "Enter a valid email address, e.g. name@example.com.";
      return undefined;
    case "message":
      if (!v) return "Please describe how we can help.";
      if (v.length < LIMITS.msgMin) return `Message is too short: at least ${LIMITS.msgMin} characters (now ${v.length}).`;
      if (v.length > LIMITS.msgMax) return `Message is too long: at most ${LIMITS.msgMax} characters (now ${v.length}).`;
      return undefined;
  }
}

export function validateAll(values: FormValues): FormErrors {
  const errors: FormErrors = {};
  (Object.keys(values) as (keyof FormValues)[]).forEach((k) => {
    const e = validateField(k, values[k]);
    if (e) errors[k] = e;
  });
  return errors;
}
