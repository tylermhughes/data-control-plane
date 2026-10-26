import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router";

import { ApiError, api, listAll } from "../api/client";
import type { Schemas } from "../api/client";
import { count, day, kindLabel, money, percent } from "../format";
import { useSession } from "../session";
import { CoverageBars } from "../components/Coverage";
import { StatusPill } from "./Board";

type Batch = Schemas["Batch"];

const DECIDABLE = new Set(["received", "passed", "failed"]);

const CHECK_LABELS: Record<string, string> = {
  files: "Files can be read",
  format: "Record format",
  schema: "Matches the spec's schema",
  duplicates: "Duplicates",
  stats: "Statistics",
  attribute_counts: "Attribute counts",
  acceptance_rules: "Acceptance rules",
};

const OUTCOME_TONE: Record<string, string> = { passed: "good", warning: "warn", failed: "bad", skipped: "neutral" };

export function problemText(error: Error): string {
  return error instanceof ApiError ? (error.problem.detail ?? error.problem.title ?? error.message) : error.message;
}

export function eventLabel(type: string): string {
  const labels: Record<string, string> = {
    "batch.received": "Delivery registered",
    "batch.reimported": "Delivery re-sent by the source",
    "batch.updated": "Delivery details changed",
    "batch.checked": "Checks finished",
    "batch.accepted": "Accepted",
    "batch.rejected": "Rejected",
  };
  if (labels[type]) return labels[type];
  const [thing, ...what] = type.split(".");
  const text = `${thing} ${what.join(" ")}`.replace(/_/g, " ");
  return text[0].toUpperCase() + text.slice(1); // "request.opened" -> "Request opened"
}

export function BatchPage() {
  const { batchId = "" } = useParams();
  const batch = useQuery({
    queryKey: ["batch", batchId],
    queryFn: () => api<Batch>(`/v1/batches/${batchId}`),
    // Checks run in the background; look again until they finish.
    refetchInterval: (q) => (q.state.data?.status === "checking" ? 2000 : false),
  });

  if (batch.isPending) return <div className="panel empty">Loading the delivery…</div>;
  if (batch.isError) {
    return (
      <>
        <Link to="/board" className="back">← Program board</Link>
        <div className="notice bad">Couldn't load this delivery: {problemText(batch.error)}</div>
      </>
    );
  }
  return <BatchView batch={batch.data} />;
}

function BatchView({ batch: b }: { batch: Batch }) {
  const allocation = useQuery({
    queryKey: ["allocation", b.allocation_id],
    queryFn: () => api<Schemas["Allocation"]>(`/v1/allocations/${b.allocation_id}`),
  });
  const source = useQuery({
    queryKey: ["data-source", b.data_source_id],
    queryFn: () => api<Schemas["DataSource"]>(`/v1/data-sources/${b.data_source_id}`),
  });
  const request = useQuery({
    queryKey: ["request", b.request_id],
    queryFn: () => api<Schemas["Request"]>(`/v1/requests/${b.request_id}`),
  });
  const unit = allocation.data?.unit ?? "items";

  return (
    <>
      <Link to="/board" className="back">← Program board</Link>
      <div className="view-head">
        <div>
          <div className="mono muted">{b.id}</div>
          <h1 style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
            {request.data?.title ?? "Delivery"} <StatusPill status={b.status} />
          </h1>
          <div className="sub">
            {source.data ? `${source.data.name} · ${kindLabel(source.data.kind)} · ` : ""}received {day(b.received_at)}
            {b.external_url && (
              <>
                {" · "}
                <a href={b.external_url} target="_blank" rel="noreferrer">open at the source</a>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="stats" role="group" aria-label="Delivery totals">
        <div className="stat">
          <div className="k">Delivered</div>
          <div className="v">{count(b.delivered_count)} <small>{unit}</small></div>
        </div>
        <div className="stat">
          <div className="k">Accepted</div>
          <div className="v">
            {b.accepted_count === null ? "—" : count(b.accepted_count)}
            {b.accepted_count !== null && b.delivered_count > 0 && <small> {percent(b.accepted_count / b.delivered_count)}</small>}
          </div>
        </div>
        <div className="stat">
          <div className="k">Spend</div>
          <div className="v">
            {money(b.spend, b.currency)} {b.spend_is_estimate && <small>estimate</small>}
          </div>
        </div>
        <div className="stat">
          <div className="k">Cost per usable unit</div>
          <div className="v">{b.accepted_count ? money(Number(b.spend) / b.accepted_count, b.currency) : "—"}</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="stack">
          <QualityPanel batch={b} />
          <CoveragePanel batchId={b.id} />
          <FilesPanel batch={b} />
        </div>
        <div className="stack">
          <DecisionPanel batch={b} unit={unit} />
          <HistoryPanel subjectId={b.id} />
        </div>
      </div>
    </>
  );
}

function QualityPanel({ batch: b }: { batch: Batch }) {
  const { canWrite } = useSession();
  const queryClient = useQueryClient();
  const runId = b.quality?.run_id;
  const run = useQuery({
    queryKey: ["quality-run", runId],
    queryFn: () => api<Schemas["QualityRun"]>(`/v1/quality-runs/${runId}`),
    enabled: Boolean(runId),
    refetchInterval: (q) => (q.state.data && ["queued", "running"].includes(q.state.data.status) ? 2000 : false),
  });
  const rerun = useMutation({
    mutationFn: () => api<Schemas["QualityRun"]>(`/v1/batches/${b.id}/checks`, { method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["batch", b.id] }),
  });

  return (
    <div className="panel" aria-label="Quality checks" role="region">
      <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <h2 style={{ margin: 0 }}>Quality checks</h2>
        {b.artifacts.length > 0 && (
          <button
            type="button"
            className="btn"
            disabled={!canWrite || rerun.isPending || b.status === "checking"}
            title={canWrite ? undefined : "Needs an API key with write access"}
            onClick={() => rerun.mutate()}
          >
            {rerun.isPending ? "Starting…" : "Run checks again"}
          </button>
        )}
      </div>
      {rerun.isError && <div className="notice bad" role="alert" style={{ marginTop: 10 }}>{problemText(rerun.error)}</div>}
      <div style={{ marginTop: 12 }}>
        {!runId ? (
          <div className="muted">
            {b.artifacts.length ? "Checks haven't run yet." : "No files were attached, so there's nothing for DCP to check."}
          </div>
        ) : !run.data ? (
          <div className="muted">Loading the checks…</div>
        ) : run.data.status === "queued" || run.data.status === "running" ? (
          <div className="notice info">Checks are running…</div>
        ) : run.data.status === "error" ? (
          <div className="notice bad">The checks couldn't run: {run.data.error}</div>
        ) : (
          run.data.checks.map((c) => (
            <div key={c.name} className="check">
              <div className="check-head">
                <strong style={{ fontWeight: 500 }}>{CHECK_LABELS[c.name] ?? c.name}</strong>
                <span className={`pill ${OUTCOME_TONE[c.outcome]}`}>{c.outcome}</span>
              </div>
              <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>{c.summary}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function CoveragePanel({ batchId }: { batchId: string }) {
  const coverage = useQuery({
    queryKey: ["coverage", batchId],
    queryFn: () => api<Schemas["Coverage"]>(`/v1/batches/${batchId}/coverage`),
  });
  return (
    <div className="panel" role="region" aria-label="Coverage">
      <h2>Coverage vs targets</h2>
      {coverage.isPending ? (
        <div className="muted">Loading…</div>
      ) : coverage.isError ? (
        <div className="notice bad">{problemText(coverage.error)}</div>
      ) : (
        <CoverageBars coverage={coverage.data} what="this delivery" />
      )}
    </div>
  );
}

function FilesPanel({ batch: b }: { batch: Batch }) {
  if (b.artifacts.length === 0) return null;
  return (
    <div className="panel">
      <h2>Files</h2>
      <div className="tablewrap">
        <table>
          <thead>
            <tr>
              <th>Location</th>
              <th>Format</th>
              <th className="r">Records</th>
            </tr>
          </thead>
          <tbody>
            {b.artifacts.map((f) => (
              <tr key={f.uri}>
                <td className="mono" style={{ wordBreak: "break-all" }}>{f.uri}</td>
                <td>{f.format}</td>
                <td className="r">{f.record_count === null || f.record_count === undefined ? "—" : count(f.record_count)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function DecisionPanel({ batch: b, unit }: { batch: Batch; unit: string }) {
  if (!DECIDABLE.has(b.status) && b.status !== "checking") {
    return (
      <div className="panel" role="region" aria-label="Decision">
        <h2>Decision</h2>
        <dl className="kv">
          <dt>Decision</dt><dd><StatusPill status={b.status} /></dd>
          <dt>By</dt><dd>{b.decided_by || "—"}{b.decision_source === "external" ? " (at the source)" : ""}</dd>
          <dt>When</dt><dd>{day(b.decided_at)}</dd>
          {b.accepted_count !== null && (
            <>
              <dt>Kept</dt><dd>{count(b.accepted_count)} of {count(b.delivered_count)} {unit}</dd>
            </>
          )}
        </dl>
        {b.override_reason && <div className="notice warn" style={{ marginTop: 10 }}>Accepted despite failed checks: {b.override_reason}</div>}
        {b.rejection_reason && <div className="notice bad" style={{ marginTop: 10 }}>Reason: {b.rejection_reason}</div>}
      </div>
    );
  }
  return <DecideForm batch={b} unit={unit} />;
}

function DecideForm({ batch: b, unit }: { batch: Batch; unit: string }) {
  const { canWrite } = useSession();
  const queryClient = useQueryClient();
  const [mode, setMode] = useState<"accept" | "reject">("accept");
  const [kept, setKept] = useState(String(b.delivered_count));
  const [decidedBy, setDecidedBy] = useState("");
  const [reason, setReason] = useState("");
  const failed = b.status === "failed";

  const decide = useMutation({
    mutationFn: () =>
      mode === "accept"
        ? api<Batch>(`/v1/batches/${b.id}/accept`, {
            method: "POST",
            body: {
              accepted_count: Number(kept),
              decided_by: decidedBy,
              ...(failed ? { override_reason: reason } : {}),
            },
          })
        : api<Batch>(`/v1/batches/${b.id}/reject`, { method: "POST", body: { reason, decided_by: decidedBy } }),
    onSuccess: (updated) => {
      queryClient.setQueryData(["batch", b.id], updated);
      void queryClient.invalidateQueries({ queryKey: ["board"] });
      void queryClient.invalidateQueries({ queryKey: ["events", b.id] });
      void queryClient.invalidateQueries({ queryKey: ["portfolio"] });
    },
  });

  if (!canWrite) {
    return (
      <div className="panel" role="region" aria-label="Decision">
        <h2>Decision</h2>
        <div className="notice info">Waiting for a decision. Accepting or rejecting needs an API key with write access.</div>
      </div>
    );
  }
  if (b.status === "checking") {
    return (
      <div className="panel" role="region" aria-label="Decision">
        <h2>Decision</h2>
        <div className="notice info">Checks are running. You can decide once they finish.</div>
      </div>
    );
  }
  const needsReason = mode === "reject" || failed;
  const keptNumber = Number(kept);
  const keptValid = kept.trim() !== "" && Number.isInteger(keptNumber) && keptNumber >= 0;
  const ready = (mode === "reject" || keptValid) && (!needsReason || reason.trim() !== "");

  return (
    <form
      className="panel decide"
      role="region"
      aria-label="Decision"
      onSubmit={(e) => {
        e.preventDefault();
        if (ready) decide.mutate();
      }}
    >
      <h2 style={{ margin: 0 }}>Decide</h2>
      {failed && (
        <div className="notice bad">
          This delivery failed its checks. You can still accept it, but you'll need to say why.
        </div>
      )}
      <div className="filters" role="group" aria-label="Accept or reject">
        <button type="button" className="chip" aria-pressed={mode === "accept"} onClick={() => setMode("accept")}>
          Accept
        </button>
        <button type="button" className="chip" aria-pressed={mode === "reject"} onClick={() => setMode("reject")}>
          Reject
        </button>
      </div>
      {mode === "accept" && (
        <label className="field">
          <span>{unit[0].toUpperCase() + unit.slice(1)} to keep (of {count(b.delivered_count)} delivered)</span>
          <input type="text" inputMode="numeric" value={kept} onChange={(e) => setKept(e.target.value)} />
        </label>
      )}
      {needsReason && (
        <label className="field">
          <span>{mode === "reject" ? "Why reject it?" : "Why accept it anyway?"}</span>
          <textarea rows={3} value={reason} onChange={(e) => setReason(e.target.value)} />
        </label>
      )}
      <label className="field">
        <span>Decided by</span>
        <input type="text" value={decidedBy} onChange={(e) => setDecidedBy(e.target.value)} />
      </label>
      {decide.isError && <div className="notice bad" role="alert">{problemText(decide.error)}</div>}
      <div className="row">
        <button type="submit" className={`btn primary${mode === "reject" ? " danger" : ""}`} disabled={!ready || decide.isPending}>
          {decide.isPending ? "Saving…" : mode === "accept" ? "Accept delivery" : "Reject delivery"}
        </button>
      </div>
    </form>
  );
}

export function HistoryPanel({ subjectId }: { subjectId: string }) {
  const events = useQuery({
    queryKey: ["events", subjectId],
    queryFn: () => listAll<Schemas["Event"]>("/v1/events", { subject_id: subjectId }),
  });
  return (
    <div className="panel" role="region" aria-label="History">
      <h2>History</h2>
      {events.isPending ? (
        <div className="muted">Loading…</div>
      ) : events.isError ? (
        <div className="notice bad">{problemText(events.error)}</div>
      ) : events.data.length === 0 ? (
        <div className="muted">Nothing recorded yet.</div>
      ) : (
        <ol className="timeline">
          {events.data.map((e) => (
            <li key={e.id}>
              <div>
                <div>{eventLabel(e.type)}</div>
                <div className="muted" style={{ fontSize: 12 }}>
                  {new Date(e.created_at).toLocaleString()} · <span className="mono">{e.type}</span>
                </div>
              </div>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
