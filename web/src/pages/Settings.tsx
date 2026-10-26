import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { NavLink, Navigate, useParams } from "react-router";

import { api, listAll } from "../api/client";
import type { Schemas } from "../api/client";
import { Drawer } from "../components/Drawer";
import { ProjectField } from "../components/ProjectField";
import { Secret } from "../components/Secret";
import { day, money } from "../format";
import { useSession } from "../session";
import { problemText } from "./Batch";
import { useCapabilities } from "./Requests";

const TABS = [
  { key: "capabilities", label: "Capabilities", admin: false },
  { key: "webhooks", label: "Webhooks", admin: false },
  { key: "projects", label: "Projects", admin: true },
  { key: "keys", label: "API keys", admin: true },
];

export function Settings() {
  const { tab } = useParams();
  const { me } = useSession();
  if (!me) return <div className="panel empty">Loading…</div>; // admin tabs depend on the key
  const isAdmin = me.role === "admin";
  const tabs = TABS.filter((t) => isAdmin || !t.admin);
  if (!tab || !tabs.some((t) => t.key === tab)) return <Navigate to="/settings/capabilities" replace />;
  return (
    <>
      <div className="view-head">
        <div>
          <h1>Settings</h1>
          <div className="sub">What your models should get better at, who can use DCP, and where it sends updates.</div>
        </div>
      </div>
      <nav className="tabs" aria-label="Settings">
        {tabs.map((t) => (
          <NavLink key={t.key} to={`/settings/${t.key}`}>{t.label}</NavLink>
        ))}
      </nav>
      {tab === "capabilities" && <Capabilities />}
      {tab === "webhooks" && <Webhooks />}
      {tab === "projects" && <Projects />}
      {tab === "keys" && <ApiKeys />}
    </>
  );
}

function WriteButton({ children, onClick }: { children: string; onClick: () => void }) {
  const { canWrite } = useSession();
  return (
    <button type="button" className="btn primary" disabled={!canWrite} title={canWrite ? undefined : "Needs an API key with write access"} onClick={onClick}>
      {children}
    </button>
  );
}

// --- capabilities ----------------------------------------------------------------------------

function Capabilities() {
  const { projectId, canWrite } = useSession();
  const capabilities = useCapabilities(projectId);
  const [editing, setEditing] = useState<Schemas["Capability"] | "new" | null>(null);
  return (
    <div className="panel" role="region" aria-label="Capabilities">
      <div className="spec-head">
        <div>
          <h2 style={{ marginBottom: 4 }}>Capabilities</h2>
          <div className="sub">Each capability is something a model should get better at, with the eval metric that measures it and what one point of improvement is worth.</div>
        </div>
        <WriteButton onClick={() => setEditing("new")}>New capability</WriteButton>
      </div>
      {capabilities.isPending ? (
        <div className="muted">Loading…</div>
      ) : capabilities.isError ? (
        <div className="notice bad">{problemText(capabilities.error)}</div>
      ) : capabilities.data.length === 0 ? (
        <div className="muted" style={{ marginTop: 12 }}>None yet. Requests and datasets belong to a capability, so start here.</div>
      ) : (
        <div className="tablewrap" style={{ marginTop: 12 }}>
          <table>
            <thead>
              <tr>
                <th>Capability</th>
                <th>Eval metric</th>
                <th className="r">One point is</th>
                <th className="r">Value per point</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {capabilities.data.map((c) => (
                <tr key={c.id}>
                  <td>
                    <div style={{ fontWeight: 500 }}>{c.name}</div>
                    {c.description && <div className="muted" style={{ fontSize: 12 }}>{c.description}</div>}
                  </td>
                  <td>
                    {c.eval_metric} <span className="muted">({c.higher_is_better ? "higher" : "lower"} is better)</span>
                  </td>
                  <td className="r">{c.point_size}</td>
                  <td className="r">{money(c.value_per_point, c.currency)}</td>
                  <td className="r">
                    {canWrite && (
                      <button type="button" className="btn" onClick={() => setEditing(c)} aria-label={`Edit ${c.name}`}>
                        Edit
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {editing && <CapabilityForm capability={editing === "new" ? undefined : editing} onClose={() => setEditing(null)} />}
    </div>
  );
}

function CapabilityForm({ capability: c, onClose }: { capability?: Schemas["Capability"]; onClose: () => void }) {
  const { projectId } = useSession();
  const queryClient = useQueryClient();
  const [project, setProject] = useState(projectId ?? "");
  const [form, setForm] = useState({
    name: c?.name ?? "",
    description: c?.description ?? "",
    eval_metric: c?.eval_metric ?? "",
    higher_is_better: c ? String(c.higher_is_better) : "true",
    value_per_point: c?.value_per_point ?? "",
    currency: c?.currency ?? "USD",
    point_size: c ? String(c.point_size) : "1",
    flattening_threshold: c ? String(c.flattening_threshold) : "0.5",
  });
  const set = (name: keyof typeof form) => (e: { target: { value: string } }) => setForm((f) => ({ ...f, [name]: e.target.value }));
  const save = useMutation({
    mutationFn: () => {
      const body = {
        name: form.name.trim(),
        description: form.description,
        eval_metric: form.eval_metric.trim(),
        higher_is_better: form.higher_is_better === "true",
        value_per_point: form.value_per_point.trim(),
        currency: form.currency.trim().toUpperCase(),
        point_size: Number(form.point_size),
        flattening_threshold: Number(form.flattening_threshold),
      };
      return c
        ? api<Schemas["Capability"]>(`/v1/capabilities/${c.id}`, { method: "PATCH", body })
        : api<Schemas["Capability"]>("/v1/capabilities", { method: "POST", body: { ...body, project_id: project || undefined } });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["capabilities"] });
      void queryClient.invalidateQueries({ queryKey: ["portfolio"] });
      onClose();
    },
  });
  const ready = form.name.trim() && form.eval_metric.trim() && form.value_per_point.trim() && (c || projectId || project);
  return (
    <Drawer label={c ? "Edit capability" : "New capability"} title={c ? `Edit ${c.name}` : "New capability"} onClose={onClose}>
      <form
        className="form"
        onSubmit={(e) => {
          e.preventDefault();
          if (ready) save.mutate();
        }}
      >
        {!c && <ProjectField value={project} onChange={setProject} />}
        <label className="field">
          <span>Name</span>
          <input type="text" value={form.name} onChange={set("name")} placeholder="e.g. Package damage detection" />
        </label>
        <label className="field">
          <span>Description</span>
          <input type="text" value={form.description} onChange={set("description")} />
        </label>
        <div className="pair">
          <label className="field">
            <span>Eval metric</span>
            <input type="text" value={form.eval_metric} onChange={set("eval_metric")} placeholder="e.g. recall@0.5" />
          </label>
          <label className="field">
            <span>Better is</span>
            <select className="input" value={form.higher_is_better} onChange={set("higher_is_better")}>
              <option value="true">Higher (accuracy, recall…)</option>
              <option value="false">Lower (error rate…)</option>
            </select>
          </label>
        </div>
        <div className="pair">
          <label className="field">
            <span>Value of one point</span>
            <input type="text" inputMode="decimal" value={form.value_per_point} onChange={set("value_per_point")} placeholder="25000" />
          </label>
          <label className="field">
            <span>Currency</span>
            <input type="text" maxLength={3} value={form.currency} onChange={set("currency")} />
          </label>
        </div>
        <div className="pair">
          <label className="field">
            <span>One point is this much of the metric</span>
            <input type="number" step="any" min={0} value={form.point_size} onChange={set("point_size")} />
          </label>
          <label className="field">
            <span>Call returns "flattening" below</span>
            <input type="number" step="0.05" min={0.05} max={1} value={form.flattening_threshold} onChange={set("flattening_threshold")} />
          </label>
        </div>
        <div className="hint">
          For a 0–1 metric like recall, use 0.01 so 0.812 → 0.857 counts as 4.5 points. "Flattening" means the latest version's points per $10K fell below this share of earlier versions' average.
        </div>
        {save.isError && <div className="notice bad" role="alert">{problemText(save.error)}</div>}
        <div className="actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn primary" disabled={!ready || save.isPending}>
            {save.isPending ? "Saving…" : c ? "Save" : "Create capability"}
          </button>
        </div>
      </form>
    </Drawer>
  );
}

// --- outgoing webhooks -----------------------------------------------------------------------

function Webhooks() {
  const { projectId, projects, canWrite, me } = useSession();
  const queryClient = useQueryClient();
  const [adding, setAdding] = useState(false);
  const [secret, setSecret] = useState<{ id: string; value: string } | null>(null);
  const endpoints = useQuery({
    queryKey: ["webhook-endpoints", projectId],
    queryFn: () => listAll<Schemas["WebhookEndpoint"]>("/v1/webhook-endpoints", { project_id: projectId }),
  });
  const refresh = () => {
    void queryClient.invalidateQueries({ queryKey: ["webhook-endpoints"] });
    void queryClient.invalidateQueries({ queryKey: ["webhook-deliveries"] });
  };
  const [form, setForm] = useState({ url: "", description: "", event_types: "*", project: projectId ?? "" });
  const create = useMutation({
    mutationFn: () =>
      api<Schemas["WebhookEndpointCreated"]>("/v1/webhook-endpoints", {
        method: "POST",
        body: {
          project_id: form.project || null,
          url: form.url.trim(),
          description: form.description,
          event_types: form.event_types.split(",").map((t) => t.trim()).filter(Boolean),
        },
      }),
    onSuccess: (ep) => {
      setSecret({ id: ep.id, value: ep.secret });
      setAdding(false);
      setForm((f) => ({ ...f, url: "", description: "" }));
      refresh();
    },
  });
  const toggle = useMutation({
    mutationFn: (ep: Schemas["WebhookEndpoint"]) => api(`/v1/webhook-endpoints/${ep.id}`, { method: "PATCH", body: { enabled: !ep.enabled } }),
    onSuccess: refresh,
  });
  const test = useMutation({
    mutationFn: (id: string) => api(`/v1/webhook-endpoints/${id}/test`, { method: "POST" }),
    onSuccess: () => setTimeout(refresh, 1500),
  });
  const rotate = useMutation({
    mutationFn: (id: string) => api<Schemas["WebhookSecret"]>(`/v1/webhook-endpoints/${id}/rotate-secret`, { method: "POST" }),
    onSuccess: (out, id) => {
      setSecret({ id, value: out.secret });
      refresh();
    },
  });
  const projectName = new Map(projects.map((p) => [p.id, p.name]));

  return (
    <div className="stack">
      <div className="panel" role="region" aria-label="Webhooks">
        <div className="spec-head">
          <div>
            <h2 style={{ marginBottom: 4 }}>Webhooks</h2>
            <div className="sub">DCP posts a signed message to these addresses whenever something changes (a delivery accepted, a request opened…).</div>
          </div>
          {!adding && <WriteButton onClick={() => setAdding(true)}>Add an address</WriteButton>}
        </div>
        {adding && (
          <form
            className="form"
            style={{ marginTop: 12 }}
            onSubmit={(e) => {
              e.preventDefault();
              if (form.url.trim()) create.mutate();
            }}
          >
            <label className="field">
              <span>Address (URL)</span>
              <input type="text" value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} placeholder="https://example.com/dcp-hook" />
            </label>
            <div className="pair">
              <label className="field">
                <span>Events (comma separated; * for all)</span>
                <input type="text" value={form.event_types} onChange={(e) => setForm({ ...form, event_types: e.target.value })} placeholder="batch.*, request.opened" />
              </label>
              <label className="field">
                <span>Description</span>
                <input type="text" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
              </label>
            </div>
            {!projectId && me?.role === "admin" && (
              <label className="field">
                <span>Project</span>
                <select className="input" value={form.project} onChange={(e) => setForm({ ...form, project: e.target.value })}>
                  <option value="">Every project (org-wide)</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </label>
            )}
            {create.isError && <div className="notice bad" role="alert">{problemText(create.error)}</div>}
            <div className="actions">
              <button type="button" className="btn" onClick={() => setAdding(false)}>
                Cancel
              </button>
              <button type="submit" className="btn primary" disabled={!form.url.trim() || create.isPending}>
                Add
              </button>
            </div>
          </form>
        )}
        {secret && (
          <div style={{ marginTop: 12 }}>
            <Secret label="Signing secret: give it to the receiver" value={secret.value} note="Use it to check each message's signature. It's shown in full only now." />
          </div>
        )}
        <div className="stack" style={{ gap: 10, marginTop: 12 }}>
          {endpoints.isPending ? (
            <div className="muted">Loading…</div>
          ) : endpoints.isError ? (
            <div className="notice bad">{problemText(endpoints.error)}</div>
          ) : endpoints.data.length === 0 ? (
            <div className="muted">None yet.</div>
          ) : (
            endpoints.data.map((ep) => (
              <div key={ep.id} className="check">
                <div className="check-head">
                  <code className="mono" style={{ wordBreak: "break-all" }}>{ep.url}</code>
                  <span className={`pill ${!ep.enabled ? "neutral" : ep.last_failure_at && (!ep.last_success_at || ep.last_failure_at > ep.last_success_at) ? "bad" : "good"}`}>
                    {!ep.enabled ? "paused" : ep.last_failure_at && (!ep.last_success_at || ep.last_failure_at > ep.last_success_at) ? "failing" : "on"}
                  </span>
                </div>
                <div className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>
                  {ep.event_types.join(", ")} · {ep.project_id ? projectName.get(ep.project_id) ?? ep.project_id : "every project"}
                  {ep.last_success_at && ` · last delivered ${new Date(ep.last_success_at).toLocaleString()}`}
                  {ep.last_failure_reason && ` · last failure: ${ep.last_failure_reason}`}
                </div>
                {canWrite && (
                  <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
                    <button type="button" className="btn" onClick={() => test.mutate(ep.id)}>Send a test</button>
                    <button type="button" className="btn" onClick={() => toggle.mutate(ep)}>{ep.enabled ? "Pause" : "Turn on"}</button>
                    <button type="button" className="btn" onClick={() => rotate.mutate(ep.id)}>Rotate secret</button>
                  </div>
                )}
                <Deliveries endpointId={ep.id} />
              </div>
            ))
          )}
        </div>
        {[toggle, test, rotate].map((m, i) => m.isError && <div key={i} className="notice bad" role="alert" style={{ marginTop: 8 }}>{problemText(m.error)}</div>)}
      </div>
    </div>
  );
}

function Deliveries({ endpointId }: { endpointId: string }) {
  const { canWrite } = useSession();
  const queryClient = useQueryClient();
  const deliveries = useQuery({
    queryKey: ["webhook-deliveries", endpointId],
    queryFn: () => api<Schemas["Page_WebhookDelivery_"]>("/v1/webhook-deliveries", { query: { endpoint_id: endpointId, limit: 8 } }),
    refetchInterval: (q) => (q.state.data?.data.some((d) => d.status === "pending") ? 2000 : false),
  });
  const redeliver = useMutation({
    mutationFn: (id: string) => api(`/v1/webhook-deliveries/${id}/redeliver`, { method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["webhook-deliveries", endpointId] }),
  });
  const list = deliveries.data?.data ?? [];
  if (list.length === 0) return null;
  return (
    <details style={{ marginTop: 8 }}>
      <summary className="muted" style={{ fontSize: 12.5 }}>Recent deliveries</summary>
      <div className="tablewrap">
        <table>
          <tbody>
            {list.map((d) => {
              const last = d.attempts[d.attempts.length - 1];
              return (
                <tr key={d.id}>
                  <td className="mono">{d.event_type}</td>
                  <td>
                    <span className={`pill ${d.status === "delivered" ? "good" : d.status === "failed" ? "bad" : "accent"}`}>{d.status}</span>
                  </td>
                  <td className="muted">
                    {d.attempt_count} attempt{d.attempt_count === 1 ? "" : "s"}
                    {last && ` · ${last.status_code ?? last.error ?? ""}`}
                  </td>
                  <td className="muted">{new Date(d.created_at).toLocaleString()}</td>
                  <td className="r">
                    {canWrite && d.status === "failed" && (
                      <button type="button" className="btn" onClick={() => redeliver.mutate(d.id)}>Send again</button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </details>
  );
}

// --- projects (admin keys) -------------------------------------------------------------------

function Projects() {
  const { projects } = useSession();
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [renaming, setRenaming] = useState<{ id: string; name: string } | null>(null);
  const refresh = () => queryClient.invalidateQueries({ queryKey: ["projects"] });
  const create = useMutation({
    mutationFn: () => api<Schemas["Project"]>("/v1/projects", { method: "POST", body: { name: name.trim() } }),
    onSuccess: () => {
      setName("");
      void refresh();
    },
  });
  const rename = useMutation({
    mutationFn: (p: { id: string; name: string }) => api(`/v1/projects/${p.id}`, { method: "PATCH", body: { name: p.name.trim() } }),
    onSuccess: () => {
      setRenaming(null);
      void refresh();
    },
  });
  const { canWrite } = useSession();
  return (
    <div className="panel" role="region" aria-label="Projects">
      <h2 style={{ marginBottom: 4 }}>Projects</h2>
      <div className="sub">Each project keeps its own capabilities, specs, sources, requests and data. Project API keys only see their project.</div>
      <div className="tablewrap" style={{ marginTop: 12 }}>
        <table>
          <tbody>
            {projects.map((p) => (
              <tr key={p.id}>
                <td>
                  {renaming?.id === p.id ? (
                    <form
                      style={{ display: "flex", gap: 6 }}
                      onSubmit={(e) => {
                        e.preventDefault();
                        if (renaming.name.trim()) rename.mutate(renaming);
                      }}
                    >
                      <input type="text" aria-label="New name" value={renaming.name} onChange={(e) => setRenaming({ ...renaming, name: e.target.value })} />
                      <button type="submit" className="btn primary">Save</button>
                      <button type="button" className="btn" onClick={() => setRenaming(null)}>Cancel</button>
                    </form>
                  ) : (
                    <span style={{ fontWeight: 500 }}>{p.name}</span>
                  )}
                </td>
                <td className="mono muted">{p.id}</td>
                <td className="muted">Created {day(p.created_at)}</td>
                <td className="r">
                  {canWrite && renaming?.id !== p.id && (
                    <button type="button" className="btn" onClick={() => setRenaming({ id: p.id, name: p.name })}>Rename</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {canWrite && (
        <form
          style={{ display: "flex", gap: 8, marginTop: 12, flexWrap: "wrap" }}
          onSubmit={(e) => {
            e.preventDefault();
            if (name.trim()) create.mutate();
          }}
        >
          <input type="text" aria-label="New project name" value={name} onChange={(e) => setName(e.target.value)} placeholder="New project name" />
          <button type="submit" className="btn primary" disabled={!name.trim() || create.isPending}>Create project</button>
        </form>
      )}
      {[create, rename].map((m, i) => m.isError && <div key={i} className="notice bad" role="alert" style={{ marginTop: 8 }}>{problemText(m.error)}</div>)}
    </div>
  );
}

// --- API keys (admin keys) -------------------------------------------------------------------

function ApiKeys() {
  const { projects, canWrite, me } = useSession();
  const queryClient = useQueryClient();
  const [form, setForm] = useState({ name: "", role: "project", access: "read", project_id: "" });
  const [created, setCreated] = useState<Schemas["ApiKeyCreated"] | null>(null);
  const [confirm, setConfirm] = useState<string | null>(null);
  const keys = useQuery({
    queryKey: ["api-keys"],
    queryFn: () => listAll<Schemas["ApiKey"]>("/v1/api-keys"),
  });
  const refresh = () => queryClient.invalidateQueries({ queryKey: ["api-keys"] });
  const create = useMutation({
    mutationFn: () =>
      api<Schemas["ApiKeyCreated"]>("/v1/api-keys", {
        method: "POST",
        body: { name: form.name.trim(), role: form.role, access: form.access, project_id: form.role === "project" ? form.project_id : null },
      }),
    onSuccess: (key) => {
      setCreated(key);
      setForm((f) => ({ ...f, name: "" }));
      void refresh();
    },
  });
  const revoke = useMutation({
    mutationFn: (id: string) => api<void>(`/v1/api-keys/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      setConfirm(null);
      void refresh();
    },
  });
  const projectName = new Map(projects.map((p) => [p.id, p.name]));
  const ready = form.name.trim() && (form.role === "admin" || form.project_id);

  return (
    <div className="panel" role="region" aria-label="API keys">
      <h2 style={{ marginBottom: 4 }}>API keys</h2>
      <div className="sub">Everyone and everything that uses DCP (this web interface, scripts, CI) signs in with a key. Admin keys see every project; project keys see one.</div>
      {created && (
        <div style={{ marginTop: 12 }}>
          <Secret label={`New key "${created.name}"`} value={created.secret} note="Copy it now: it's shown only once and can't be retrieved later." />
        </div>
      )}
      <div className="tablewrap" style={{ marginTop: 12 }}>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Key starts with</th>
              <th>Can</th>
              <th>Last used</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {(keys.data ?? []).map((k) => (
              <tr key={k.id} style={k.revoked_at ? { opacity: 0.55 } : undefined}>
                <td>
                  {k.name}
                  {k.id === me?.id && <span className="pill accent" style={{ marginLeft: 6 }}>you</span>}
                </td>
                <td className="mono">{k.key_prefix}…</td>
                <td>
                  {k.access === "write" ? "Edit" : "Read"} · {k.role === "admin" ? "all projects (admin)" : projectName.get(k.project_id ?? "") ?? k.project_id}
                </td>
                <td className="muted">{k.revoked_at ? `Revoked ${day(k.revoked_at)}` : k.last_used_at ? day(k.last_used_at) : "Never"}</td>
                <td className="r">
                  {canWrite && !k.revoked_at &&
                    (confirm === k.id ? (
                      <button type="button" className="btn primary danger" onClick={() => revoke.mutate(k.id)}>
                        {k.id === me?.id ? "Yes, revoke (signs you out)" : "Yes, revoke"}
                      </button>
                    ) : (
                      <button type="button" className="btn" onClick={() => setConfirm(k.id)} aria-label={`Revoke ${k.name}`}>
                        Revoke
                      </button>
                    ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {revoke.isError && <div className="notice bad" role="alert" style={{ marginTop: 8 }}>{problemText(revoke.error)}</div>}
      {canWrite && (
        <form
          className="form"
          style={{ marginTop: 16 }}
          onSubmit={(e) => {
            e.preventDefault();
            if (ready) create.mutate();
          }}
        >
          <div className="section-label">New key</div>
          <div className="pair">
            <label className="field">
              <span>Name</span>
              <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="e.g. Dana's dashboard" />
            </label>
            <label className="field">
              <span>Can</span>
              <select className="input" value={form.access} onChange={(e) => setForm({ ...form, access: e.target.value })}>
                <option value="read">Only look (read)</option>
                <option value="write">Look and change (write)</option>
              </select>
            </label>
          </div>
          <div className="pair">
            <label className="field">
              <span>Sees</span>
              <select className="input" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
                <option value="project">One project</option>
                <option value="admin">Everything, incl. keys and projects (admin)</option>
              </select>
            </label>
            {form.role === "project" && (
              <label className="field">
                <span>Project</span>
                <select className="input" value={form.project_id} onChange={(e) => setForm({ ...form, project_id: e.target.value })}>
                  <option value="">Choose…</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </label>
            )}
          </div>
          {create.isError && <div className="notice bad" role="alert">{problemText(create.error)}</div>}
          <div className="actions">
            <button type="submit" className="btn primary" disabled={!ready || create.isPending}>
              Create key
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
