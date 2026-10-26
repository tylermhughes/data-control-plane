import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router";

import { api, listAll } from "../api/client";
import type { Schemas } from "../api/client";
import { KIND_COLORS } from "../board";
import { CoverageBars } from "../components/Coverage";
import { count, day, kindLabel, money, percent } from "../format";
import { useSession } from "../session";
import { HistoryPanel, problemText } from "./Batch";
import { RequestForm, STATUS_TONE, useCapabilities } from "./Requests";

type Request = Schemas["Request"];
type Allocation = Schemas["Allocation"];
type Source = Schemas["DataSource"];

/** Everything that changes when allocations change. */
function useRefresh(requestId: string) {
  const queryClient = useQueryClient();
  return () => {
    for (const key of [["request", requestId], ["allocations", requestId], ["plan", requestId], ["requests"], ["board"], ["events", requestId]]) {
      void queryClient.invalidateQueries({ queryKey: key });
    }
  };
}

export function RequestPage() {
  const { requestId = "" } = useParams();
  const request = useQuery({
    queryKey: ["request", requestId],
    queryFn: () => api<Request>(`/v1/requests/${requestId}`),
  });
  if (request.isPending) return <div className="panel empty">Loading the request…</div>;
  if (request.isError) {
    return (
      <>
        <Link to="/requests" className="back">← Requests</Link>
        <div className="notice bad">Couldn't load this request: {problemText(request.error)}</div>
      </>
    );
  }
  return <RequestView request={request.data} />;
}

function RequestView({ request: r }: { request: Request }) {
  const { canWrite } = useSession();
  const [editing, setEditing] = useState(false);
  const capabilities = useCapabilities(r.project_id);
  const allocations = useQuery({
    queryKey: ["allocations", r.id],
    queryFn: () => listAll<Allocation>("/v1/allocations", { request_id: r.id }),
  });
  const sources = useQuery({
    queryKey: ["data-sources", r.project_id],
    queryFn: () => listAll<Source>("/v1/data-sources", { project_id: r.project_id }),
  });
  const sourceById = new Map((sources.data ?? []).map((s) => [s.id, s]));
  const capability = capabilities.data?.find((c) => c.id === r.capability_id);
  const totals = r.allocated.find((a) => a.unit === r.unit);
  const live = r.status === "draft" || r.status === "open";

  return (
    <>
      <Link to="/requests" className="back">← Requests</Link>
      <div className="view-head">
        <div>
          <div className="mono muted">{r.id}</div>
          <h1 style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
            {r.title} <span className={`pill ${STATUS_TONE[r.status]}`}>{r.status}</span>
            <span className={`pill ${r.priority <= "P1" ? "bad" : "neutral"}`}>{r.priority}</span>
          </h1>
          <div className="sub">
            {capability ? `${capability.name} · ` : ""}
            {r.requested_by ? `asked by ${r.requested_by} · ` : ""}
            {r.due_date ? `due ${day(r.due_date)}` : "no due date"}
          </div>
        </div>
        {live && canWrite && (
          <button type="button" className="btn" onClick={() => setEditing(true)}>
            Edit
          </button>
        )}
      </div>

      <div className="stats" role="group" aria-label="Request totals">
        <div className="stat">
          <div className="k">Wanted</div>
          <div className="v">{count(r.quantity)} <small>{r.unit}</small></div>
        </div>
        <div className="stat">
          <div className="k">Allocated</div>
          <div className="v">
            {count(totals?.quantity ?? 0)} <small>{totals ? money(totals.quoted_cost, totals.currency) + " quoted" : ""}</small>
          </div>
        </div>
        <div className="stat">
          <div className="k">Accepted</div>
          <div className="v">
            {count(totals?.accepted_count ?? 0)} <small>{percent((totals?.accepted_count ?? 0) / r.quantity)} of wanted</small>
          </div>
        </div>
        <div className="stat">
          <div className="k">Spend</div>
          <div className="v">{r.allocated.length ? r.allocated.map((a) => money(a.spend, a.currency)).join(" + ") : money(0)}</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="stack">
          <AllocationsPanel request={r} allocations={allocations} sourceById={sourceById} />
          {live && r.spec_version_id && <PlanPanel request={r} />}
          {live && canWrite && r.spec_version_id && sources.data && (
            <AddAllocation request={r} sources={sources.data} currency={capability?.currency ?? "USD"} />
          )}
        </div>
        <div className="stack">
          <StatusPanel request={r} />
          <div className="panel">
            <h2>Details</h2>
            <dl className="kv">
              <dt>Spec</dt>
              <dd>
                {r.spec_id ? <Link to={`/specs/${r.spec_id}?v=${r.spec_version}`}>v{r.spec_version}</Link> : <span className="pill warn">Needs a spec</span>}
              </dd>
              <dt>Target eval or slice</dt><dd>{r.target_metric || "—"}</dd>
              <dt>Created</dt><dd>{day(r.created_at)}</dd>
              {r.opened_at && <><dt>Opened</dt><dd>{day(r.opened_at)}</dd></>}
              {r.closed_at && <><dt>Closed</dt><dd>{day(r.closed_at)}</dd></>}
              {r.cancelled_at && <><dt>Cancelled</dt><dd>{day(r.cancelled_at)}</dd></>}
            </dl>
            {r.rationale && <p style={{ margin: "12px 0 0" }}>{r.rationale}</p>}
          </div>
          {r.spec_version_id && <RequestCoverage requestId={r.id} />}
          <HistoryPanel subjectId={r.id} />
        </div>
      </div>
      {editing && <RequestForm request={r} onClose={() => setEditing(false)} />}
    </>
  );
}

function StatusPanel({ request: r }: { request: Request }) {
  const { canWrite } = useSession();
  const refresh = useRefresh(r.id);
  const [confirmCancel, setConfirmCancel] = useState(false);
  const act = useMutation({
    mutationFn: (action: "open" | "close" | "cancel") => api<Request>(`/v1/requests/${r.id}/${action}`, { method: "POST" }),
    onSuccess: () => {
      setConfirmCancel(false);
      refresh();
    },
  });
  if (r.status === "closed" || r.status === "cancelled") return null;
  const explain =
    r.status === "draft"
      ? r.spec_version_id
        ? "Open the request so the work can start."
        : "Choose an approved spec (Edit), then open the request."
      : "Close it when you have what you need, or cancel it if it's no longer wanted.";
  return (
    <div className="panel decide" role="region" aria-label="Status">
      <h2 style={{ margin: 0 }}>Next step</h2>
      <div className="muted">{explain}</div>
      {!canWrite ? (
        <div className="notice info">Changing a request needs an API key with write access.</div>
      ) : (
        <div className="row">
          {r.status === "draft" && (
            <button type="button" className="btn primary" disabled={!r.spec_version_id || act.isPending} onClick={() => act.mutate("open")}>
              Open request
            </button>
          )}
          {r.status === "open" && (
            <button type="button" className="btn primary" disabled={act.isPending} onClick={() => act.mutate("close")}>
              Close request
            </button>
          )}
          {confirmCancel ? (
            <button type="button" className="btn primary danger" disabled={act.isPending} onClick={() => act.mutate("cancel")}>
              Yes, cancel it
            </button>
          ) : (
            <button type="button" className="btn" onClick={() => setConfirmCancel(true)}>
              Cancel request
            </button>
          )}
        </div>
      )}
      {act.isError && <div className="notice bad" role="alert">{problemText(act.error)}</div>}
    </div>
  );
}

function SourceName({ source }: { source?: Source }) {
  if (!source) return <span className="muted">Unknown source</span>;
  return (
    <span className="source" style={{ ["--c" as string]: KIND_COLORS[source.kind] }} title={kindLabel(source.kind)}>
      <span className="sw" />
      {source.name}
    </span>
  );
}

function AllocationsPanel({
  request: r,
  allocations,
  sourceById,
}: {
  request: Request;
  allocations: ReturnType<typeof useQuery<Allocation[]>>;
  sourceById: Map<string, Source>;
}) {
  return (
    <div className="panel" role="region" aria-label="Allocations">
      <h2>Allocations</h2>
      {allocations.isPending ? (
        <div className="muted">Loading…</div>
      ) : allocations.isError ? (
        <div className="notice bad">{problemText(allocations.error)}</div>
      ) : allocations.data.length === 0 ? (
        <div className="muted">
          {r.spec_version_id ? "Not split across any sources yet. Use the suggested split below, or add one yourself." : "Choose a spec first: allocations are quoted against an approved spec version."}
        </div>
      ) : (
        <div className="tablewrap">
          <table>
            <thead>
              <tr>
                <th>Source</th>
                <th className="r">Ordered</th>
                <th className="r">Quoted</th>
                <th className="r">Accepted</th>
                <th className="r">Spend</th>
                <th>Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {allocations.data.map((a) => (
                <AllocationRow key={a.id} allocation={a} source={sourceById.get(a.data_source_id)} requestOpen={r.status === "open"} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function AllocationRow({ allocation: a, source, requestOpen }: { allocation: Allocation; source?: Source; requestOpen: boolean }) {
  const { canWrite } = useSession();
  const refresh = useRefresh(a.request_id);
  const [confirmCancel, setConfirmCancel] = useState(false);
  const act = useMutation({
    mutationFn: (action: "activate" | "complete" | "cancel") => api<Allocation>(`/v1/allocations/${a.id}/${action}`, { method: "POST" }),
    onSuccess: refresh,
  });
  return (
    <tr>
      <td>
        <SourceName source={source} />
        {a.due_date && <div className="muted" style={{ fontSize: 12 }}>due {day(a.due_date)}</div>}
        {act.isError && <div className="notice bad" role="alert" style={{ marginTop: 4 }}>{problemText(act.error)}</div>}
      </td>
      <td className="r">{count(a.quantity)} {a.unit}</td>
      <td className="r">
        {money(a.quoted_cost, a.currency)}
        <div className="muted" style={{ fontSize: 12 }}>{money(a.quoted_unit_rate, a.currency)} each</div>
      </td>
      <td className="r">
        {count(a.accepted_count)}
        <div className="muted" style={{ fontSize: 12 }}>{percent(a.progress)}</div>
      </td>
      <td className="r">{money(a.spend, a.currency)}</td>
      <td><span className={`pill ${STATUS_TONE[a.status]}`}>{a.status}</span></td>
      <td className="r">
        {canWrite && (a.status === "planned" || a.status === "active") && (
          <div style={{ display: "flex", gap: 6, justifyContent: "flex-end", flexWrap: "wrap" }}>
            {a.status === "planned" && (
              <button
                type="button"
                className="btn"
                disabled={!requestOpen || act.isPending}
                title={requestOpen ? undefined : "Open the request first"}
                onClick={() => act.mutate("activate")}
              >
                Start
              </button>
            )}
            {a.status === "active" && (
              <button type="button" className="btn" disabled={act.isPending} onClick={() => act.mutate("complete")}>
                Complete
              </button>
            )}
            {confirmCancel ? (
              <button type="button" className="btn primary danger" disabled={act.isPending} onClick={() => act.mutate("cancel")}>
                Yes, cancel
              </button>
            ) : (
              <button type="button" className="btn" onClick={() => setConfirmCancel(true)} aria-label={`Cancel ${source?.name ?? "allocation"}`}>
                Cancel
              </button>
            )}
          </div>
        )}
      </td>
    </tr>
  );
}

function PlanPanel({ request: r }: { request: Request }) {
  const { canWrite } = useSession();
  const refresh = useRefresh(r.id);
  const plan = useQuery({
    queryKey: ["plan", r.id],
    queryFn: () => api<Schemas["AllocationPlan"]>(`/v1/requests/${r.id}/allocation-plan`),
  });
  const add = useMutation({
    mutationFn: async (list: Schemas["Suggestion"][]) => {
      for (const s of list) await api<Allocation>("/v1/allocations", { method: "POST", body: s.allocation });
    },
    onSettled: refresh,
  });

  return (
    <div className="panel" role="region" aria-label="Suggested split">
      <div className="spec-head">
        <h2 style={{ margin: 0 }}>Suggested split</h2>
        <span className="pill neutral" title={plan.data?.method}>Suggestion</span>
      </div>
      {plan.isPending ? (
        <div className="muted">Working it out…</div>
      ) : plan.isError ? (
        <div className="notice bad">{problemText(plan.error)}</div>
      ) : plan.data.remaining <= 0 ? (
        <div className="muted" style={{ marginTop: 8 }}>
          Fully allocated: {count(plan.data.already_allocated)} of {count(plan.data.requested)} {plan.data.unit} are planned or under way.
        </div>
      ) : (
        <>
          <p className="muted" style={{ margin: "8px 0 12px" }}>
            {count(plan.data.remaining)} {plan.data.unit} still to plan for. {plan.data.method}
          </p>
          {plan.data.suggestions.length === 0 ? (
            <div className="muted">No source can take this on.</div>
          ) : (
            <div className="tablewrap">
              <table>
                <thead>
                  <tr>
                    <th>Source</th>
                    <th className="r">Share</th>
                    <th className="r">Order</th>
                    <th className="r">Expected usable</th>
                    <th className="r">Expected cost</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {plan.data.suggestions.map((s) => (
                    <tr key={s.data_source_id}>
                      <td>
                        {s.name} <span className={`pill ${s.role === "proven" ? "good" : "accent"}`}>{s.role}</span>
                        {s.notes.map((n) => (
                          <div key={n} className="muted" style={{ fontSize: 12 }}>{n}</div>
                        ))}
                      </td>
                      <td className="r">{percent(s.share)}</td>
                      <td className="r">{count(s.order_quantity)}</td>
                      <td className="r">{count(s.expected_usable)}</td>
                      <td className="r">{s.expected_cost ? money(s.expected_cost, s.currency ?? "USD") : "—"}</td>
                      <td className="r">
                        {canWrite && (
                          <button type="button" className="btn" disabled={add.isPending} onClick={() => add.mutate([s])} aria-label={`Add ${s.name}`}>
                            Add
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {plan.data.shortfall > 0 && (
            <div className="notice warn" style={{ marginTop: 10 }}>
              About {count(plan.data.shortfall)} {plan.data.unit} can't be delivered by the due date by any source.
            </div>
          )}
          {plan.data.excluded.length > 0 && (
            <ul className="muted" style={{ fontSize: 12.5, margin: "10px 0 0", paddingLeft: 18 }}>
              {plan.data.excluded.map((x) => (
                <li key={x.data_source_id}>{x.name} left out: {x.reason}</li>
              ))}
            </ul>
          )}
          {add.isError && <div className="notice bad" role="alert" style={{ marginTop: 10 }}>{problemText(add.error)}</div>}
          {canWrite && plan.data.suggestions.length > 1 && (
            <button
              type="button"
              className="btn primary"
              style={{ marginTop: 12 }}
              disabled={add.isPending}
              onClick={() => add.mutate(plan.data.suggestions)}
            >
              {add.isPending ? "Adding…" : "Add all as planned allocations"}
            </button>
          )}
          <div className="muted" style={{ fontSize: 12, marginTop: 8 }}>
            Added allocations start as planned. Nothing is sent to a source until you start it.
          </div>
        </>
      )}
    </div>
  );
}

function AddAllocation({ request: r, sources, currency }: { request: Request; sources: Source[]; currency: string }) {
  const refresh = useRefresh(r.id);
  const [form, setForm] = useState({ data_source_id: "", quantity: "", quoted_unit_rate: "", currency, due_date: "", notes: "" });
  const set = (name: keyof typeof form) => (e: { target: { value: string } }) => setForm((f) => ({ ...f, [name]: e.target.value }));
  const create = useMutation({
    mutationFn: () =>
      api<Allocation>("/v1/allocations", {
        method: "POST",
        body: {
          request_id: r.id,
          data_source_id: form.data_source_id,
          quantity: Number(form.quantity),
          quoted_unit_rate: form.quoted_unit_rate.trim(),
          currency: form.currency.trim().toUpperCase(),
          due_date: form.due_date || null,
          notes: form.notes,
        },
      }),
    onSuccess: () => {
      setForm((f) => ({ ...f, data_source_id: "", quantity: "", quoted_unit_rate: "", notes: "" }));
      refresh();
    },
  });
  const quantity = Number(form.quantity);
  const rate = Number(form.quoted_unit_rate);
  const ready = form.data_source_id && Number.isInteger(quantity) && quantity > 0 && form.quoted_unit_rate.trim() !== "" && rate >= 0;
  const source = sources.find((s) => s.id === form.data_source_id);

  return (
    <form
      className="panel form"
      role="region"
      aria-label="Add an allocation"
      onSubmit={(e) => {
        e.preventDefault();
        if (ready) create.mutate();
      }}
    >
      <h2 style={{ margin: 0 }}>Add an allocation</h2>
      <label className="field">
        <span>Source</span>
        <select className="input" value={form.data_source_id} onChange={set("data_source_id")}>
          <option value="">Choose…</option>
          {sources.map((s) => (
            <option key={s.id} value={s.id}>{s.name} ({kindLabel(s.kind)})</option>
          ))}
        </select>
      </label>
      <div className="pair">
        <label className="field">
          <span>Quantity{source ? ` (${source.default_unit})` : ""}</span>
          <input type="number" min={1} value={form.quantity} onChange={set("quantity")} />
        </label>
        <label className="field">
          <span>Quoted price per unit ({form.currency})</span>
          <input type="text" inputMode="decimal" value={form.quoted_unit_rate} onChange={set("quoted_unit_rate")} placeholder="1.55" />
        </label>
      </div>
      <div className="pair">
        <label className="field">
          <span>Due date</span>
          <input type="date" value={form.due_date} onChange={set("due_date")} />
        </label>
        <label className="field">
          <span>Currency</span>
          <input type="text" value={form.currency} onChange={set("currency")} maxLength={3} />
        </label>
      </div>
      <label className="field">
        <span>Notes</span>
        <input type="text" value={form.notes} onChange={set("notes")} placeholder="e.g. quote number" />
      </label>
      {ready && <div className="muted">Quoted cost: {money(quantity * rate, form.currency.toUpperCase() || "USD")}</div>}
      {create.isError && <div className="notice bad" role="alert">{problemText(create.error)}</div>}
      <div className="actions">
        <button type="submit" className="btn primary" disabled={!ready || create.isPending}>
          {create.isPending ? "Adding…" : "Add allocation"}
        </button>
      </div>
    </form>
  );
}

function RequestCoverage({ requestId }: { requestId: string }) {
  const coverage = useQuery({
    queryKey: ["request-coverage", requestId],
    queryFn: () => api<Schemas["Coverage"]>(`/v1/requests/${requestId}/coverage`),
  });
  return (
    <div className="panel" role="region" aria-label="Coverage">
      <h2>Coverage vs targets</h2>
      {coverage.isPending ? (
        <div className="muted">Loading…</div>
      ) : coverage.isError ? (
        <div className="notice bad">{problemText(coverage.error)}</div>
      ) : (
        <CoverageBars coverage={coverage.data} what="accepted deliveries" />
      )}
    </div>
  );
}
