import { useState } from "react";
import type { FormEvent } from "react";

import { ApiError, api } from "../api/client";
import type { Schemas } from "../api/client";
import { useSession } from "../session";

export function SignIn() {
  const { signIn } = useSession();
  const [key, setKey] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const me = await api<Schemas["ApiKey"]>("/v1/me", { key: key.trim() });
      signIn(key.trim(), me);
    } catch (err) {
      setError(err instanceof ApiError ? err.problem.detail : "Can't reach Data Control Plane.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="signin">
      <div className="panel">
        <div className="brand" style={{ color: "var(--fg)" }}>
          <span className="logo" style={{ background: "var(--band)" }} aria-hidden="true" />
          Data Control Plane
        </div>
        <h1>Sign in</h1>
        <p className="sub">
          Paste an API key. It's kept only in this browser tab and forgotten when you close it.
        </p>
        <form onSubmit={submit}>
          <label className="field">
            API key
            <input
              type="password"
              autoComplete="off"
              placeholder="dcp_…"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              required
            />
          </label>
          {error && (
            <div className="notice bad" role="alert">
              {error}
            </div>
          )}
          <button className="btn primary" type="submit" disabled={busy || !key.trim()}>
            {busy ? "Checking…" : "Sign in"}
          </button>
        </form>
        <p className="muted" style={{ fontSize: 12.5, margin: 0 }}>
          No key yet? On the server, run{" "}
          <span className="mono">docker compose exec api python -m app.cli create-admin-key</span>
        </p>
      </div>
    </div>
  );
}
