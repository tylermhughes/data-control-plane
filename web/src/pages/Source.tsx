import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router";

import { api, listAll } from "../api/client";
import type { Schemas } from "../api/client";
import { KIND_COLORS } from "../board";
import { Secret } from "../components/Secret";
import { count, day, kindLabel, money, percent } from "../format";
import { useSession } from "../session";
import { LICENSE_LABELS, sourceStats } from "../sources";
import { StatusPill } from "./Board";
import { problemText } from "./Batch";
import { STATUS_TONE } from "./Requests";
import { RightsPill, SourceForm } from "./Sources";

type Source = Schemas["DataSource"];

export function SourcePage() {
  const { sourceId = "" } = useParams();
  const source = useQuery({
    queryKey: ["data-source", sourceId],
    queryFn: () => api<Source>(`/v1/data-sources/${sourceId}`),
  });
  if (source.isPending) return <div className="panel empty">Loading the source…</div>;
  if (source.isError) {
    return (
      <>
        <Link to="/sources" className="back">← Sources & vendors</Link>
        <div className="notice bad">Couldn't load this source: {problemText(source.error)}</div>
      </>
    );
  }
  return <SourceView source={source.data} />;
}

function SourceView({ source: s }: { source: Source }) {
  const { canWrite } = useSession();
  const [editing, setEditing] = useState(false);
  const work = useQuery({
    queryKey: ["source-work", s.id],
    queryFn: async () => {
      const [allocations, batches, requests] = await Promise.all([
        listAll<Schemas["Allocation"]>("/v1/allocations", { data_source_id: s.id }),
        listAll<Schemas["Batch"]>("/v1/batches", { data_source_id: s.id }),
        listAll<Schemas["Request"]>("/v1/requests", { project_id: s.project_id }),
      ]);
      return { allocations, batches, requests };
    },
  });
  const st = work.data ? sourceStats(s.id, work.data.allocations, work.data.batches) : null;
  const requestTitle = new Map((work.data?.requests ?? []).map((r) => [r.id, r.title]));

  return (
    <>
      <Link to="/sources" className="back">← Sources & vendors</Link>
      <div className="view-head">
        <div>
          <h1 style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
            <span className="sw" style={{ background: KIND_COLORS[s.kind], width: 12, height: 12 }} />
            {s.name} <span className="pill neutral">{kindLabel(s.kind)}</span> <RightsPill expires={s.rights_expires_at} />
          </h1>
          <div className="sub">{s.description || `Delivers ${s.default_unit}.`}</div>
        </div>
        {canWrite && (
          <button type="button" className="btn" onClick={() => setEditing(true)}>
            Edit
          </button>
        )}
      </div>

      <div className="stats" role="group" aria-label="Track record">
        <div className="stat">
          <div className="k">Active allocations</div>
          <div className="v">{st ? st.activeAllocations : "—"}</div>
        </div>
        <div className="stat">
          <div className="k">Spend</div>
          <div className="v">{st?.spend.size ? [...st.spend].map(([c, a]) => money(a, c)).join(" + ") : "$0"}</div>
        </div>
        <div className="stat">
          <div className="k">Accept rate</div>
          <div className="v">
            {percent(st?.acceptRate, 1)} <small>{st ? `${count(st.accepted)} of ${count(st.delivered)}` : ""}</small>
          </div>
        </div>
        <div className="stat">
          <div className="k">Cost per usable</div>
          <div className="v">{st?.costPerUsable ? money(st.costPerUsable.amount, st.costPerUsable.currency) : "—"}</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="stack">
          <div className="panel" role="region" aria-label="Work">
            <h2>Allocations</h2>
            {!work.data ? (
              <div className="muted">Loading…</div>
            ) : work.data.allocations.length === 0 ? (
              <div className="muted">No work allocated to this source yet.</div>
            ) : (
              <div className="stack" style={{ gap: 6 }}>
                {work.data.allocations.map((a) => (
                  <Link key={a.id} to={`/requests/${a.request_id}`} className="rowlink">
                    <span>
                      {requestTitle.get(a.request_id) ?? a.request_id}
                      <span className="muted"> · {count(a.accepted_count)} of {count(a.quantity)} {a.unit}</span>
                    </span>
                    <span className={`pill ${STATUS_TONE[a.status]}`}>{a.status}</span>
                  </Link>
                ))}
              </div>
            )}
            <h2 style={{ marginTop: 16 }}>Deliveries</h2>
            {!work.data ? (
              <div className="muted">Loading…</div>
            ) : work.data.batches.length === 0 ? (
              <div className="muted">Nothing delivered yet.</div>
            ) : (
              <div className="stack" style={{ gap: 6 }}>
                {work.data.batches.map((b) => (
                  <Link key={b.id} to={`/batches/${b.id}`} className="rowlink">
                    <span>
                      {day(b.received_at)}
                      <span className="muted"> · {count(b.delivered_count)} delivered · {money(b.spend, b.currency)}</span>
                    </span>
                    <StatusPill status={b.status} />
                  </Link>
                ))}
              </div>
            )}
          </div>
          <InboundPanel source={s} />
          <ConnectorsPanel source={s} allocations={work.data?.allocations ?? []} />
        </div>
        <div className="stack">
          <div className="panel" role="region" aria-label="Rights">
            <h2>Rights and data handling</h2>
            <dl className="kv">
              <dt>Rights basis</dt><dd>{LICENSE_LABELS[s.license_type]}</dd>
              <dt>Rights end</dt><dd>{s.rights_expires_at ? day(s.rights_expires_at) : "No end date"}</dd>
              <dt>Unit</dt><dd>{s.default_unit}</dd>
              <dt>Added</dt><dd>{day(s.created_at)}</dd>
            </dl>
            {[["What contributors agreed to", s.consent_scope], ["Personal data handling", s.pii_handling], ["Notes", s.notes]].map(
              ([label, text]) =>
                text && (
                  <div key={label} style={{ marginTop: 12 }}>
                    <div className="section-label">{label}</div>
                    <div style={{ whiteSpace: "pre-wrap" }}>{text}</div>
                  </div>
                ),
            )}
          </div>
        </div>
      </div>
      {editing && <SourceForm source={s} onClose={() => setEditing(false)} />}
    </>
  );
}

// --- automatic intake ------------------------------------------------------------------------

function InboundPanel({ source: s }: { source: Source }) {
  const { canWrite } = useSession();
  const queryClient = useQueryClient();
  const [secret, setSecret] = useState<{ id: string; value: string } | null>(null); // shown once, after create or rotate
  const endpoints = useQuery({
    queryKey: ["inbound", s.id],
    queryFn: () => listAll<Schemas["InboundEndpoint"]>("/v1/inbound-webhooks", { data_source_id: s.id }),
  });
  const refresh = () => queryClient.invalidateQueries({ queryKey: ["inbound", s.id] });
  const create = useMutation({
    mutationFn: () =>
      api<Schemas["InboundEndpointCreated"]>("/v1/inbound-webhooks", {
        method: "POST",
        body: { data_source_id: s.id, description: `${s.name} delivery notifications` },
      }),
    onSuccess: (ep) => {
      setSecret({ id: ep.id, value: ep.secret });
      void refresh();
    },
  });
  const toggle = useMutation({
    mutationFn: (ep: Schemas["InboundEndpoint"]) =>
      api(`/v1/inbound-webhooks/${ep.id}`, { method: "PATCH", body: { enabled: !ep.enabled } }),
    onSuccess: refresh,
  });
  const rotate = useMutation({
    mutationFn: (id: string) => api<Schemas["WebhookSecret"]>(`/v1/inbound-webhooks/${id}/rotate-secret`, { method: "POST" }),
    onSuccess: (out, id) => {
      setSecret({ id, value: out.secret });
      void refresh();
    },
  });

  return (
    <div className="panel" role="region" aria-label="Inbound webhooks">
      <div className="spec-head">
        <h2 style={{ margin: 0 }}>Delivery notifications (inbound webhook)</h2>
        {canWrite && (
          <button type="button" className="btn" disabled={create.isPending} onClick={() => create.mutate()}>
            Add a webhook URL
          </button>
        )}
      </div>
      <p className="muted" style={{ margin: "8px 0 12px" }}>
        The source posts a signed message here when it delivers, and DCP registers the delivery and checks it.
      </p>
      {secret && (
        <div style={{ marginBottom: 12 }}>
          <Secret label="Signing secret: give it to the source" value={secret.value} note="It's shown in full only now. You can rotate it any time." />
        </div>
      )}
      {endpoints.isPending ? (
        <div className="muted">Loading…</div>
      ) : endpoints.isError ? (
        <div className="notice bad">{problemText(endpoints.error)}</div>
      ) : endpoints.data.length === 0 ? (
        <div className="muted">None set up.</div>
      ) : (
        <div className="stack" style={{ gap: 10 }}>
          {endpoints.data.map((ep) => (
            <div key={ep.id} className="check">
              <div className="check-head">
                <code className="mono" style={{ wordBreak: "break-all" }}>{window.location.origin + ep.url_path}</code>
                <span className={`pill ${ep.enabled ? "good" : "neutral"}`}>{ep.enabled ? "on" : "paused"}</span>
              </div>
              <div className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>
                {ep.last_received_at ? `Last message ${new Date(ep.last_received_at).toLocaleString()}` : "No messages yet"}
              </div>
              {canWrite && (
                <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
                  <button type="button" className="btn" onClick={() => toggle.mutate(ep)}>
                    {ep.enabled ? "Pause" : "Turn on"}
                  </button>
                  <button type="button" className="btn" onClick={() => rotate.mutate(ep.id)}>
                    Rotate secret
                  </button>
                </div>
              )}
              <InboundMessages endpointId={ep.id} />
            </div>
          ))}
        </div>
      )}
      {[create, toggle, rotate].map((m, i) => m.isError && <div key={i} className="notice bad" role="alert" style={{ marginTop: 8 }}>{problemText(m.error)}</div>)}
    </div>
  );
}

function InboundMessages({ endpointId }: { endpointId: string }) {
  const messages = useQuery({
    queryKey: ["inbound-messages", endpointId],
    queryFn: () => api<Schemas["Page_InboundMessageLog_"]>(`/v1/inbound-webhooks/${endpointId}/messages`, { query: { limit: 5 } }),
  });
  const list = messages.data?.data ?? [];
  if (list.length === 0) return null;
  return (
    <ul className="muted" style={{ fontSize: 12.5, margin: "8px 0 0", paddingLeft: 18 }}>
      {list.map((m) => (
        <li key={m.id}>
          {new Date(m.received_at).toLocaleString()}: {m.status}
          {m.error ? ` (${m.error})` : ""}
          {m.batch_id && (
            <>
              {" · "}
              <Link to={`/batches/${m.batch_id}`}>delivery</Link>
            </>
          )}
        </li>
      ))}
    </ul>
  );
}

function ConnectorsPanel({ source: s, allocations }: { source: Source; allocations: Schemas["Allocation"][] }) {
  const { canWrite } = useSession();
  const queryClient = useQueryClient();
  const [adding, setAdding] = useState(false);
  const [polled, setPolled] = useState<Record<string, Schemas["PollResult"]>>({});
  const connectors = useQuery({
    queryKey: ["connectors", s.id],
    queryFn: () => listAll<Schemas["Connector"]>("/v1/connectors", { data_source_id: s.id }),
  });
  const refresh = () => {
    void queryClient.invalidateQueries({ queryKey: ["connectors", s.id] });
    void queryClient.invalidateQueries({ queryKey: ["source-work", s.id] });
  };
  const poll = useMutation({
    mutationFn: (id: string) => api<Schemas["PollResult"]>(`/v1/connectors/${id}/poll`, { method: "POST" }),
    onSuccess: (out, id) => {
      setPolled((p) => ({ ...p, [id]: out }));
      refresh();
    },
  });
  const toggle = useMutation({
    mutationFn: (c: Schemas["Connector"]) => api(`/v1/connectors/${c.id}`, { method: "PATCH", body: { enabled: !c.enabled } }),
    onSuccess: refresh,
  });

  return (
    <div className="panel" role="region" aria-label="Bucket watchers">
      <div className="spec-head">
        <h2 style={{ margin: 0 }}>Bucket watcher (S3)</h2>
        {canWrite && !adding && (
          <button type="button" className="btn" onClick={() => setAdding(true)}>
            Watch a bucket
          </button>
        )}
      </div>
      <p className="muted" style={{ margin: "8px 0 12px" }}>
        DCP checks a storage bucket on a schedule. Each new file becomes a delivery from this source and is checked automatically.
      </p>
      {adding && <ConnectorForm source={s} allocations={allocations} onDone={() => { setAdding(false); refresh(); }} />}
      {connectors.isPending ? (
        <div className="muted">Loading…</div>
      ) : connectors.isError ? (
        <div className="notice bad">{problemText(connectors.error)}</div>
      ) : connectors.data.length === 0 ? (
        !adding && <div className="muted">None set up.</div>
      ) : (
        <div className="stack" style={{ gap: 10 }}>
          {connectors.data.map((c) => {
            const result = polled[c.id];
            return (
              <div key={c.id} className="check">
                <div className="check-head">
                  <code className="mono">s3://{c.bucket}/{c.prefix}</code>
                  <span className={`pill ${c.last_error ? "bad" : c.enabled ? "good" : "neutral"}`}>
                    {c.last_error ? "error" : c.enabled ? "on" : "paused"}
                  </span>
                </div>
                <div className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>
                  Every {c.poll_interval_seconds}s
                  {c.endpoint_url ? ` · ${c.endpoint_url}` : ""}
                  {c.last_polled_at ? ` · last checked ${new Date(c.last_polled_at).toLocaleString()}` : " · not checked yet"}
                  {c.has_credentials ? ` · keys stored (${c.access_key_hint})` : " · uses DCP's own access"}
                </div>
                {c.last_error && <div className="notice bad" style={{ marginTop: 6 }}>{c.last_error}</div>}
                {result && (
                  <div className="notice info" role="status" style={{ marginTop: 6 }}>
                    Found {result.files_listed} file(s); {result.new_batches.length} new deliver{result.new_batches.length === 1 ? "y" : "ies"}.
                    {result.errors.length > 0 && ` Problems: ${result.errors.join("; ")}`}
                  </div>
                )}
                {canWrite && (
                  <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
                    <button type="button" className="btn" disabled={poll.isPending} onClick={() => poll.mutate(c.id)}>
                      {poll.isPending && poll.variables === c.id ? "Checking…" : "Check now"}
                    </button>
                    <button type="button" className="btn" onClick={() => toggle.mutate(c)}>
                      {c.enabled ? "Pause" : "Turn on"}
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
      {[poll, toggle].map((m, i) => m.isError && <div key={i} className="notice bad" role="alert" style={{ marginTop: 8 }}>{problemText(m.error)}</div>)}
    </div>
  );
}

function ConnectorForm({ source: s, allocations, onDone }: { source: Source; allocations: Schemas["Allocation"][]; onDone: () => void }) {
  const [form, setForm] = useState({ bucket: "", prefix: "", endpoint_url: "", region: "", allocation_id: "", access_key_id: "", secret_access_key: "", poll_interval_seconds: "60" });
  const set = (name: keyof typeof form) => (e: { target: { value: string } }) => setForm((f) => ({ ...f, [name]: e.target.value }));
  const create = useMutation({
    mutationFn: () =>
      api<Schemas["Connector"]>("/v1/connectors", {
        method: "POST",
        body: {
          data_source_id: s.id,
          description: `${s.name} delivery bucket`,
          bucket: form.bucket.trim(),
          prefix: form.prefix.trim(),
          endpoint_url: form.endpoint_url.trim() || null,
          region: form.region.trim() || null,
          allocation_id: form.allocation_id || null,
          poll_interval_seconds: Number(form.poll_interval_seconds),
          credentials: form.access_key_id
            ? { access_key_id: form.access_key_id.trim(), secret_access_key: form.secret_access_key }
            : null,
        },
      }),
    onSuccess: onDone,
  });
  const active = allocations.filter((a) => a.status === "active");
  return (
    <form
      className="form"
      style={{ marginBottom: 12 }}
      onSubmit={(e) => {
        e.preventDefault();
        if (form.bucket.trim()) create.mutate();
      }}
    >
      <div className="pair">
        <label className="field">
          <span>Bucket</span>
          <input type="text" value={form.bucket} onChange={set("bucket")} placeholder="intake" />
        </label>
        <label className="field">
          <span>Folder (prefix)</span>
          <input type="text" value={form.prefix} onChange={set("prefix")} placeholder="surge/" />
        </label>
      </div>
      <div className="pair">
        <label className="field">
          <span>Storage address (S3-compatible only)</span>
          <input type="text" value={form.endpoint_url} onChange={set("endpoint_url")} placeholder="Empty for AWS S3" />
        </label>
        <label className="field">
          <span>Region</span>
          <input type="text" value={form.region} onChange={set("region")} placeholder="us-east-1" />
        </label>
      </div>
      <div className="pair">
        <label className="field">
          <span>Access key ID</span>
          <input type="text" value={form.access_key_id} onChange={set("access_key_id")} placeholder="Empty: use DCP's own access" autoComplete="off" />
        </label>
        <label className="field">
          <span>Secret access key</span>
          <input type="password" value={form.secret_access_key} onChange={set("secret_access_key")} autoComplete="new-password" />
        </label>
      </div>
      <div className="pair">
        <label className="field">
          <span>Deliveries count toward</span>
          <select className="input" value={form.allocation_id} onChange={set("allocation_id")}>
            <option value="">The source's active allocation</option>
            {active.map((a) => (
              <option key={a.id} value={a.id}>{a.id.slice(0, 16)}… ({a.quantity} {a.unit})</option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Check every (seconds)</span>
          <input type="number" min={15} value={form.poll_interval_seconds} onChange={set("poll_interval_seconds")} />
        </label>
      </div>
      <div className="hint">Keys are stored encrypted and never shown again.</div>
      {create.isError && <div className="notice bad" role="alert">{problemText(create.error)}</div>}
      <div className="actions">
        <button type="button" className="btn" onClick={onDone}>
          Cancel
        </button>
        <button type="submit" className="btn primary" disabled={!form.bucket.trim() || create.isPending}>
          {create.isPending ? "Saving…" : "Start watching"}
        </button>
      </div>
    </form>
  );
}
