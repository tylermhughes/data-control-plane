import { useState } from "react";

/** A secret shown once (API key, signing secret), with a copy button. */
export function Secret({ label, value, note }: { label: string; value: string; note?: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <div className="notice warn" role="status" aria-label={label}>
      <div style={{ fontWeight: 500, marginBottom: 6 }}>{label}</div>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <code className="mono" style={{ wordBreak: "break-all", color: "var(--fg)" }}>{value}</code>
        <button
          type="button"
          className="btn"
          onClick={() => {
            void navigator.clipboard?.writeText(value).then(() => setCopied(true));
          }}
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      {note && <div style={{ marginTop: 6 }}>{note}</div>}
    </div>
  );
}
