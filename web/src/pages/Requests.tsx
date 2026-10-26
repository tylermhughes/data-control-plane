import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate } from "react-router";

import { api, listAll } from "../api/client";
import type { Schemas } from "../api/client";
import { Drawer } from "../components/Drawer";
import { count, day } from "../format";
import { useSession } from "../session";
import { problemText } from "./Batch";

type Request = Schemas["Request"];

const FILTERS = [
  { key: "active", label: "Draft and open", statuses: ["draft", "open"] },
  { key: "closed", label: "Closed", statuses: ["closed"] },
  { key: "cancelled", label: "Cancelled", statuses: ["cancelled"] },
  { key: "all", label: "All", statuses: ["draft", "open", "closed", "cancelled"] },
];

export const STATUS_TONE: Record<string, string> = {
  draft: "neutral",
  open: "accent",
  closed: "good",
  cancelled: "bad",
  planned: "neutral",
  active: "accent",
  complete: "good",
};

export function useCapabilities(projectId: string | null) {
  return useQuery({
    queryKey: ["capabilities", projectId],
    queryFn: () => listAll<Schemas["Capability"]>("/v1/capabilities", { project_id: projectId }),
  });
}

export function Requests() {
  const { projectId, canWrite } = useSession();
  const [filter, setFilter] = useState("active");
  const [creating, setCreating] = useState(false);
  const requests = useQuery({
    queryKey: ["requests", projectId],
    queryFn: () => listAll<Request>("/v1/requests", { project_id: projectId }),
  });
  const capabilities = useCapabilities(projectId);
  const capName = new Map((capabilities.data ?? []).map((c) => [c.id, c.name]));

  const statuses = FILTERS.find((f) => f.key === filter)!.statuses;
  const shown = (requests.data ?? []).filter((r) => statuses.includes(r.status));

  return (
    <>
      <div className="view-head">
        <div>
          <h1>Requests</h1>
          <div className="sub">What data the team asked for and why, and how each request is split across sources.</div>
        </div>
        <button
          type="button"
          className="btn primary"
          data-tour="new-request"
          disabled={!canWrite}
          title={canWrite ? undefined : "Needs an API key with write access"}
          onClick={() => setCreating(true)}
        >
          New request
        </button>
      </div>
      <div className="filters" role="group" aria-label="Filter by status" style={{ marginBottom: 12 }}>
        {FILTERS.map((f) => (
          <button key={f.key} type="button" className="chip" aria-pressed={filter === f.key} onClick={() => setFilter(f.key)}>
            {f.label}
          </button>
        ))}
      </div>
      {requests.isPending ? (
        <div className="panel empty">Loading requests…</div>
      ) : requests.isError ? (
        <div className="notice bad">Couldn't load requests: {problemText(requests.error)}</div>
      ) : shown.length === 0 ? (
        <div className="panel empty">No requests here yet.</div>
      ) : (
        <div className="panel">
          <div className="tablewrap">
            <table>
              <thead>
                <tr>
                  <th>Request</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Capability</th>
                  <th>Spec</th>
                  <th className="r">Wanted</th>
                  <th className="r">Allocated</th>
                  <th className="r">Accepted</th>
                  <th>Due</th>
                </tr>
              </thead>
              <tbody>
                {shown.map((r) => {
                  const allocated = r.allocated.filter((a) => a.unit === r.unit);
                  return (
                    <tr key={r.id}>
                      <td>
                        <Link to={`/requests/${r.id}`} style={{ fontWeight: 500 }}>{r.title}</Link>
                        <div className="muted" style={{ fontSize: 12 }}>{r.requested_by || "—"}</div>
                      </td>
                      <td><span className={`pill ${r.priority <= "P1" ? "bad" : "neutral"}`}>{r.priority}</span></td>
                      <td><span className={`pill ${STATUS_TONE[r.status]}`}>{r.status}</span></td>
                      <td>{capName.get(r.capability_id) ?? "—"}</td>
                      <td>{r.spec_version ? `v${r.spec_version}` : <span className="pill warn">Needs a spec</span>}</td>
                      <td className="r">{count(r.quantity)} {r.unit}</td>
                      <td className="r">{count(allocated.reduce((n, a) => n + a.quantity, 0))}</td>
                      <td className="r">{count(allocated.reduce((n, a) => n + a.accepted_count, 0))}</td>
                      <td>{day(r.due_date)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
      {creating && <RequestForm onClose={() => setCreating(false)} />}
    </>
  );
}

/** Approved spec versions in a project, newest first, for choosing a request's spec. */
export function useApprovedVersions(projectId: string | undefined) {
  return useQuery({
    queryKey: ["approved-spec-versions", projectId],
    enabled: Boolean(projectId),
    queryFn: async () => {
      const specs = await listAll<Schemas["Spec"]>("/v1/specs", { project_id: projectId });
      const lists = await Promise.all(
        specs
          .filter((s) => s.latest_approved_version)
          .map(async (s) => {
            const versions = await listAll<Schemas["SpecVersion"]>(`/v1/specs/${s.id}/versions`);
            return versions
              .filter((v) => v.status === "approved")
              .sort((a, b) => b.version - a.version)
              .map((v) => ({ id: v.id, label: `${s.name} v${v.version}` }));
          }),
      );
      return lists.flat();
    },
  });
}

/** New request (no `request`) or edit an existing one. */
export function RequestForm({ request, onClose }: { request?: Request; onClose: () => void }) {
  const { projectId } = useSession();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const capabilities = useCapabilities(projectId);
  const [form, setForm] = useState({
    capability_id: request?.capability_id ?? "",
    title: request?.title ?? "",
    requested_by: request?.requested_by ?? "",
    priority: request?.priority ?? "P2",
    target_metric: request?.target_metric ?? "",
    rationale: request?.rationale ?? "",
    quantity: request ? String(request.quantity) : "",
    unit: request?.unit ?? "images",
    due_date: request?.due_date ?? "",
    spec_version_id: request?.spec_version_id ?? "",
  });
  const set = (name: keyof typeof form) => (e: { target: { value: string } }) => setForm((f) => ({ ...f, [name]: e.target.value }));
  const capability = capabilities.data?.find((c) => c.id === form.capability_id);
  const versions = useApprovedVersions(request?.project_id ?? capability?.project_id);

  const save = useMutation({
    mutationFn: () => {
      const body: Record<string, unknown> = {
        title: form.title.trim(),
        requested_by: form.requested_by,
        priority: form.priority,
        target_metric: form.target_metric,
        rationale: form.rationale,
        quantity: Number(form.quantity),
        unit: form.unit.trim(),
        due_date: form.due_date || null,
      };
      if (!request) {
        body.capability_id = form.capability_id;
        if (form.spec_version_id) body.spec_version_id = form.spec_version_id;
        return api<Request>("/v1/requests", { method: "POST", body });
      }
      if (form.spec_version_id && form.spec_version_id !== request.spec_version_id) body.spec_version_id = form.spec_version_id;
      return api<Request>(`/v1/requests/${request.id}`, { method: "PATCH", body });
    },
    onSuccess: (saved) => {
      void queryClient.invalidateQueries({ queryKey: ["requests"] });
      void queryClient.invalidateQueries({ queryKey: ["board"] });
      queryClient.setQueryData(["request", saved.id], saved);
      onClose();
      if (!request) navigate(`/requests/${saved.id}`);
    },
  });
  const quantityOk = Number.isInteger(Number(form.quantity)) && Number(form.quantity) > 0;
  const ready = form.title.trim() && quantityOk && form.unit.trim() && (request || form.capability_id);

  return (
    <Drawer label={request ? "Edit request" : "New request"} title={request ? "Edit request" : "New data request"} onClose={onClose}>
      <form
        className="form"
        onSubmit={(e) => {
          e.preventDefault();
          if (ready) save.mutate();
        }}
      >
        {!request && (
          <label className="field">
            <span>Capability it should improve</span>
            <select className="input" value={form.capability_id} onChange={set("capability_id")}>
              <option value="">Choose…</option>
              {(capabilities.data ?? []).map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
            {capabilities.data?.length === 0 && (
              <span className="hint">
                No capabilities yet. <Link to="/settings/capabilities">Create one in Settings</Link> first.
              </span>
            )}
          </label>
        )}
        <label className="field">
          <span>What data do you need?</span>
          <input type="text" value={form.title} onChange={set("title")} placeholder="e.g. Crushed boxes under low dock lighting" />
        </label>
        <div className="pair">
          <label className="field">
            <span>Requested by</span>
            <input type="text" value={form.requested_by} onChange={set("requested_by")} />
          </label>
          <label className="field">
            <span>Priority</span>
            <select className="input" value={form.priority} onChange={set("priority")}>
              <option value="P0">P0 (urgent)</option>
              <option value="P1">P1 (high)</option>
              <option value="P2">P2 (medium)</option>
              <option value="P3">P3 (low)</option>
            </select>
          </label>
        </div>
        <div className="pair">
          <label className="field">
            <span>How many</span>
            <input type="number" min={1} value={form.quantity} onChange={set("quantity")} />
          </label>
          <label className="field">
            <span>Unit</span>
            <input type="text" value={form.unit} onChange={set("unit")} />
          </label>
        </div>
        <label className="field">
          <span>Due date</span>
          <input type="date" value={form.due_date} onChange={set("due_date")} />
        </label>
        <label className="field">
          <span>Target eval or slice</span>
          <input type="text" value={form.target_metric} onChange={set("target_metric")} placeholder="e.g. recall@0.5, shrink-wrapped slice" />
        </label>
        <label className="field">
          <span>Why now?</span>
          <textarea rows={3} value={form.rationale} onChange={set("rationale")} placeholder="What failure or deadline is driving this?" />
        </label>
        <label className="field">
          <span>Spec (approved versions only; can be added later)</span>
          <select className="input" value={form.spec_version_id} onChange={set("spec_version_id")} disabled={!request && !capability}>
            <option value="">{request?.spec_version_id ? "Keep the current spec" : "No spec yet"}</option>
            {(versions.data ?? []).map((v) => (
              <option key={v.id} value={v.id}>{v.label}</option>
            ))}
          </select>
        </label>
        {save.isError && <div className="notice bad" role="alert">{problemText(save.error)}</div>}
        <div className="actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn primary" disabled={!ready || save.isPending}>
            {save.isPending ? "Saving…" : request ? "Save" : "Create request"}
          </button>
        </div>
      </form>
    </Drawer>
  );
}
