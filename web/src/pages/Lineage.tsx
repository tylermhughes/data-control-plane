import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, Navigate, useNavigate, useParams, useSearchParams } from "react-router";

import { api, listAll } from "../api/client";
import type { Schemas } from "../api/client";
import { KIND_COLORS } from "../board";
import { Drawer } from "../components/Drawer";
import { count, day, money, percent } from "../format";
import { useSession } from "../session";
import { problemText } from "./Batch";
import { useCapabilities } from "./Requests";

type Dataset = Schemas["Dataset"];
type DatasetVersion = Schemas["DatasetVersion"];
type EvalResult = Schemas["EvalResult"];
type Batch = Schemas["Batch"];

/** The latest result per metric, from a list of eval results. */
export function latestByMetric(evals: EvalResult[]): Map<string, EvalResult> {
  const out = new Map<string, EvalResult>();
  for (const e of [...evals].sort((a, b) => a.recorded_at.localeCompare(b.recorded_at))) out.set(e.metric, e);
  return out;
}

/** Change from `before` to `after`, positive when it's an improvement. */
export function improvement(before: number, after: number, higherIsBetter: boolean): number {
  return higherIsBetter ? after - before : before - after;
}

export function Lineage() {
  const { projectId, canWrite } = useSession();
  const { datasetId } = useParams();
  const [creating, setCreating] = useState(false);
  const datasets = useQuery({
    queryKey: ["datasets", projectId],
    queryFn: () => listAll<Dataset>("/v1/datasets", { project_id: projectId }),
  });
  if (datasets.isPending) return <div className="panel empty">Loading datasets…</div>;
  if (datasets.isError) return <div className="notice bad">Couldn't load datasets: {problemText(datasets.error)}</div>;
  const list = datasets.data;
  if (!datasetId && list.length > 0) return <Navigate to={`/lineage/${list[0].id}`} replace />;
  const current = list.find((d) => d.id === datasetId);

  return (
    <>
      <div className="view-head">
        <div>
          <h1>Lineage & spend</h1>
          <div className="sub">Trace a dataset version back to the requests and deliveries in it, and forward to the eval it moved.</div>
        </div>
        <button
          type="button"
          className="btn primary"
          disabled={!canWrite}
          title={canWrite ? undefined : "Needs an API key with write access"}
          onClick={() => setCreating(true)}
        >
          New dataset
        </button>
      </div>
      {list.length === 0 ? (
        <div className="panel empty">No datasets yet. A dataset is a named line of training data for one capability.</div>
      ) : (
        <div className="grid-list">
          <nav className="list" aria-label="Datasets">
            {list.map((d) => (
              <Link key={d.id} to={`/lineage/${d.id}`} aria-current={d.id === datasetId ? "page" : undefined}>
                <span className="mono" style={{ color: "var(--fg)" }}>{d.name}</span>
                <span>{d.latest_version ? `${d.latest_version} version${d.latest_version === 1 ? "" : "s"}` : "No versions yet"}</span>
              </Link>
            ))}
          </nav>
          {current ? <DatasetDetail key={current.id} dataset={current} /> : <div className="notice bad">That dataset doesn't exist here.</div>}
        </div>
      )}
      {creating && <NewDataset onClose={() => setCreating(false)} />}
    </>
  );
}

function useLineageData(dataset: Dataset) {
  return useQuery({
    queryKey: ["lineage", dataset.id],
    queryFn: async () => {
      const project = { project_id: dataset.project_id };
      const [versions, evals, batches, requests, sources, specs] = await Promise.all([
        listAll<DatasetVersion>("/v1/dataset-versions", { dataset_id: dataset.id }),
        listAll<EvalResult>("/v1/eval-results", { capability_id: dataset.capability_id }),
        listAll<Batch>("/v1/batches", project),
        listAll<Schemas["Request"]>("/v1/requests", project),
        listAll<Schemas["DataSource"]>("/v1/data-sources", project),
        listAll<Schemas["Spec"]>("/v1/specs", project),
      ]);
      return { versions: versions.sort((a, b) => b.version - a.version), evals, batches, requests, sources, specs };
    },
  });
}

function DatasetDetail({ dataset }: { dataset: Dataset }) {
  const { canWrite } = useSession();
  const [params] = useSearchParams();
  const [adding, setAdding] = useState(false);
  const data = useLineageData(dataset);
  const capabilities = useCapabilities(dataset.project_id);
  const capability = capabilities.data?.find((c) => c.id === dataset.capability_id);

  if (data.isPending) return <div className="panel muted">Loading lineage…</div>;
  if (data.isError) return <div className="notice bad">{problemText(data.error)}</div>;
  const d = data.data;
  const allVersions = new Map(d.versions.map((v) => [v.id, v]));
  const v = d.versions.find((x) => x.version === Number(params.get("v"))) ?? d.versions[0];

  return (
    <div className="stack">
      <div className="panel">
        <div className="spec-head">
          <div>
            <h2 style={{ marginBottom: 4 }}>
              <span className="mono">{dataset.name}</span> {v && <span className="muted">v{v.version}</span>}
            </h2>
            <div className="sub">{capability ? `Trains ${capability.name}` : ""}{dataset.description ? ` · ${dataset.description}` : ""}</div>
          </div>
          {canWrite && (
            <button type="button" className="btn primary" data-tour="new-version" onClick={() => setAdding(true)}>
              New version
            </button>
          )}
        </div>
        {d.versions.length > 0 && (
          <div className="filters" role="group" aria-label="Version" style={{ marginTop: 10 }}>
            {d.versions.map((x) => (
              <Link key={x.id} to={`/lineage/${dataset.id}?v=${x.version}`} className="chip" aria-pressed={x.id === v?.id} style={{ textDecoration: "none", color: "inherit" }}>
                v{x.version}
              </Link>
            ))}
          </div>
        )}
      </div>
      {!v ? (
        <div className="panel empty">No versions yet. Freeze accepted deliveries into version 1.</div>
      ) : (
        <VersionDetail
          version={v}
          baseline={v.baseline_version_id ? allVersions.get(v.baseline_version_id) : undefined}
          capability={capability}
          data={d}
        />
      )}
      {adding && <NewVersion dataset={dataset} latest={d.versions[0]} batches={d.batches} requests={d.requests} sources={d.sources} onClose={() => setAdding(false)} />}
    </div>
  );
}

type LineageData = NonNullable<ReturnType<typeof useLineageData>["data"]>;

function VersionDetail({
  version: v,
  baseline,
  capability,
  data: d,
}: {
  version: DatasetVersion;
  baseline?: DatasetVersion;
  capability?: Schemas["Capability"];
  data: LineageData;
}) {
  const batchById = new Map(d.batches.map((b) => [b.id, b]));
  const sourceById = new Map(d.sources.map((s) => [s.id, s]));
  const requestById = new Map(d.requests.map((r) => [r.id, r]));
  const specName = new Map(d.specs.map((s) => [s.id, s.name]));
  const batches = v.batch_ids.map((id) => batchById.get(id)).filter((b): b is Batch => Boolean(b));
  const baselineIds = new Set(baseline?.batch_ids ?? []);
  const requests = [...new Set(batches.map((b) => b.request_id))].map((id) => requestById.get(id)).filter(Boolean) as Schemas["Request"][];
  const specVersions = new Map<string, string>();
  for (const b of batches) {
    const r = requestById.get(b.request_id);
    const label = r?.spec_version_id === b.spec_version_id && r.spec_id ? `${specName.get(r.spec_id) ?? "Spec"} v${r.spec_version}` : b.spec_version_id;
    specVersions.set(b.spec_version_id, label);
  }
  const delivered = batches.reduce((n, b) => n + b.delivered_count, 0);
  const accepted = batches.reduce((n, b) => n + (b.accepted_count ?? 0), 0);
  const spend = new Map<string, number>();
  for (const b of batches) spend.set(b.currency, (spend.get(b.currency) ?? 0) + Number(b.spend));

  const now = latestByMetric(d.evals.filter((e) => e.dataset_version_id === v.id));
  const before = latestByMetric(d.evals.filter((e) => e.dataset_version_id === baseline?.id));
  const main = capability ? now.get(capability.eval_metric) : [...now.values()][0];
  const mainBefore = main ? before.get(main.metric) : undefined;

  return (
    <>
      <div className="panel" role="region" aria-label="Lineage">
        <h2>Where v{v.version} came from</h2>
        <div className="chain">
          <div className="node wide">
            <div className="kind">Request{requests.length === 1 ? "" : "s"}</div>
            {requests.map((r) => (
              <Link key={r.id} to={`/requests/${r.id}`} className="brow" style={{ padding: "2px 0" }}>
                <span className="name">{r.title}</span>
              </Link>
            ))}
          </div>
          <div className="arrow" aria-hidden="true" />
          <div className="node">
            <div className="kind">Spec</div>
            {[...specVersions].map(([id, label]) => {
              const r = requests.find((x) => x.spec_version_id === id);
              return r?.spec_id ? (
                <Link key={id} to={`/specs/${r.spec_id}?v=${r.spec_version}`} className="name">{label}</Link>
              ) : (
                <div key={id} className="name mono">{label}</div>
              );
            })}
          </div>
          <div className="arrow" aria-hidden="true" />
          <div className="node wide">
            <div className="kind">Deliveries</div>
            {batches.map((b) => {
              const s = sourceById.get(b.data_source_id);
              return (
                <Link key={b.id} to={`/batches/${b.id}`} className="brow">
                  <span className="source" style={{ ["--c" as string]: s ? KIND_COLORS[s.kind] : undefined }}>
                    <span className="sw" />
                    {s?.name ?? "Unknown"}
                  </span>
                  <span className="num muted">{count(b.accepted_count)} kept</span>
                </Link>
              );
            })}
          </div>
          <div className="arrow" aria-hidden="true" />
          <div className="node">
            <div className="kind">QA gate</div>
            <div className="name num">{count(accepted)} of {count(delivered)}</div>
            <div className="detail">{delivered ? `${percent(1 - accepted / delivered, 1)} rejected` : ""}</div>
          </div>
          <div className="arrow" aria-hidden="true" />
          <div className="node">
            <div className="kind">Dataset version</div>
            <div className="name mono">v{v.version}</div>
            <div className="detail">{day(v.created_at)}{baseline ? ` · compared with v${baseline.version}` : " · no baseline"}</div>
          </div>
          <div className="arrow" aria-hidden="true" />
          <div className={`node${main ? " result" : ""}`}>
            <div className="kind">Eval result</div>
            {main ? (
              <>
                <div className="name">{main.metric}</div>
                <div className="detail num">
                  {mainBefore ? `${mainBefore.value} → ` : ""}
                  {main.value}
                </div>
                {main.external_run_url ? (
                  <a className="detail" href={main.external_run_url} target="_blank" rel="noreferrer">{main.run_name || "run"}</a>
                ) : (
                  main.run_name && <div className="detail mono">{main.run_name}</div>
                )}
              </>
            ) : (
              <div className="detail">Not recorded yet</div>
            )}
          </div>
        </div>
        {v.notes && <p className="muted" style={{ margin: "10px 0 0" }}>{v.notes}</p>}
      </div>

      <div className="grid-2">
        <div className="panel" role="region" aria-label="Eval impact">
          <h2>Eval impact {baseline && <span className="muted" style={{ fontWeight: 400 }}>vs v{baseline.version}</span>}</h2>
          {now.size === 0 ? (
            <div className="muted">No eval results for this version yet.</div>
          ) : (
            <div className="tablewrap">
              <table>
                <thead>
                  <tr>
                    <th>Metric</th>
                    <th className="r">Before</th>
                    <th className="r">After</th>
                    <th className="r">Change</th>
                  </tr>
                </thead>
                <tbody>
                  {[...now.values()].map((e) => {
                    const b = before.get(e.metric);
                    const change = b ? improvement(b.value, e.value, e.higher_is_better) : null;
                    return (
                      <tr key={e.metric}>
                        <td>
                          {e.metric}
                          <div className="muted" style={{ fontSize: 12 }}>{e.higher_is_better ? "Higher is better" : "Lower is better"}</div>
                        </td>
                        <td className="r">{b ? b.value : "—"}</td>
                        <td className="r">{e.value}</td>
                        <td className="r">
                          {change === null ? "—" : (
                            <span className={`delta ${change >= 0 ? "up" : "down"}`}>
                              {e.value - b!.value > 0 ? "+" : "−"}
                              {Math.abs(Math.round((e.value - b!.value) * 10000) / 10000)}
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
        <RecordEval version={v} capability={capability} />
      </div>

      <div className="panel" role="region" aria-label="Spend and yield">
        <h2>Spend and yield by delivery</h2>
        <div className="tablewrap">
          <table>
            <thead>
              <tr>
                <th>Delivery</th>
                <th className="r">Delivered</th>
                <th className="r">Accepted</th>
                <th className="r">Rejected</th>
                <th className="r">Spend</th>
                <th className="r">Cost per usable</th>
              </tr>
            </thead>
            <tbody>
              {batches.map((b) => {
                const s = sourceById.get(b.data_source_id);
                const rejected = b.delivered_count ? 1 - (b.accepted_count ?? 0) / b.delivered_count : 0;
                return (
                  <tr key={b.id}>
                    <td>
                      <Link to={`/batches/${b.id}`} className="source" style={{ ["--c" as string]: s ? KIND_COLORS[s.kind] : undefined, textDecoration: "none", color: "inherit" }}>
                        <span className="sw" />
                        {s?.name ?? "Unknown"}
                      </Link>{" "}
                      {baseline && !baselineIds.has(b.id) && <span className="pill accent">new in v{v.version}</span>}
                      <div className="muted" style={{ fontSize: 12 }}>{day(b.received_at)}</div>
                    </td>
                    <td className="r">{count(b.delivered_count)}</td>
                    <td className="r">{count(b.accepted_count)}</td>
                    <td className="r">
                      <span className={`pill ${rejected < 0.05 ? "good" : rejected < 0.1 ? "warn" : "bad"}`}>{percent(rejected, 1)}</span>
                    </td>
                    <td className="r">{money(b.spend, b.currency)}</td>
                    <td className="r"><b>{b.accepted_count ? money(Number(b.spend) / b.accepted_count, b.currency) : "—"}</b></td>
                  </tr>
                );
              })}
              <tr>
                <td><b>Total</b></td>
                <td className="r">{count(delivered)}</td>
                <td className="r">{count(accepted)}</td>
                <td className="r">{delivered ? percent(1 - accepted / delivered, 1) : "—"}</td>
                <td className="r">{[...spend].map(([c, a]) => money(a, c)).join(" + ") || "—"}</td>
                <td className="r">
                  <b>{accepted && spend.size === 1 ? money([...spend.values()][0] / accepted, [...spend.keys()][0]) : "—"}</b>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div className="muted" style={{ fontSize: 12, marginTop: 8 }}>
          Cost per usable counts only items that passed QA, so rework shows up as a higher unit cost.
          {baseline && v.new_vs_baseline.length > 0 && (
            <> Spend behind this version's eval change (new since v{baseline.version}): {v.new_vs_baseline.map((t) => money(t.spend, t.currency)).join(" + ")}.</>
          )}
        </div>
        <Manifest versionId={v.id} />
      </div>
    </>
  );
}

function Manifest({ versionId }: { versionId: string }) {
  const [open, setOpen] = useState(false);
  const manifest = useQuery({
    queryKey: ["manifest", versionId],
    queryFn: () => api<Schemas["Manifest"]>(`/v1/dataset-versions/${versionId}/manifest`),
    enabled: open,
  });
  return (
    <details style={{ marginTop: 12 }} onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)}>
      <summary>Files in this version (what training downloads)</summary>
      {!manifest.data ? (
        <div className="muted" style={{ marginTop: 6 }}>{manifest.isError ? problemText(manifest.error) : "Loading…"}</div>
      ) : (
        <ul className="mono" style={{ fontSize: 12, margin: "8px 0 0", paddingLeft: 18 }}>
          {manifest.data.files.map((f) => (
            <li key={f.batch_id + f.uri} style={{ wordBreak: "break-all" }}>
              {f.uri} <span className="muted">{f.record_count === null ? "" : `(${count(f.record_count)} records)`}</span>
            </li>
          ))}
          {manifest.data.files.length === 0 && <li className="muted">No files: these deliveries were registered without file pointers.</li>}
        </ul>
      )}
    </details>
  );
}

function RecordEval({ version: v, capability }: { version: DatasetVersion; capability?: Schemas["Capability"] }) {
  const { canWrite } = useSession();
  const queryClient = useQueryClient();
  const [form, setForm] = useState({ metric: "", value: "", run_name: "", external_run_url: "" });
  const set = (name: keyof typeof form) => (e: { target: { value: string } }) => setForm((f) => ({ ...f, [name]: e.target.value }));
  const record = useMutation({
    mutationFn: () =>
      api<EvalResult>("/v1/eval-results", {
        method: "POST",
        body: {
          dataset_version_id: v.id,
          metric: form.metric.trim() || undefined,
          value: Number(form.value),
          run_name: form.run_name,
          external_run_url: form.external_run_url.trim() || null,
        },
      }),
    onSuccess: () => {
      setForm({ metric: "", value: "", run_name: "", external_run_url: "" });
      void queryClient.invalidateQueries({ queryKey: ["lineage"] });
      void queryClient.invalidateQueries({ queryKey: ["portfolio"] });
      void queryClient.invalidateQueries({ queryKey: ["diagnosis"] });
    },
  });
  if (!canWrite) return null;
  const ready = form.value.trim() !== "" && Number.isFinite(Number(form.value));
  return (
    <form
      className="panel form"
      role="region"
      aria-label="Record an eval result"
      onSubmit={(e) => {
        e.preventDefault();
        if (ready) record.mutate();
      }}
    >
      <h2 style={{ margin: 0 }}>Record an eval result for v{v.version}</h2>
      <div className="pair">
        <label className="field">
          <span>Metric</span>
          <input type="text" value={form.metric} onChange={set("metric")} placeholder={capability?.eval_metric ?? "the capability's metric"} />
        </label>
        <label className="field">
          <span>Value</span>
          <input type="number" step="any" value={form.value} onChange={set("value")} />
        </label>
      </div>
      <div className="pair">
        <label className="field">
          <span>Run name</span>
          <input type="text" value={form.run_name} onChange={set("run_name")} />
        </label>
        <label className="field">
          <span>Link to the run</span>
          <input type="text" value={form.external_run_url} onChange={set("external_run_url")} placeholder="https://wandb.ai/…" />
        </label>
      </div>
      {record.isError && <div className="notice bad" role="alert">{problemText(record.error)}</div>}
      <div className="actions">
        <button type="submit" className="btn primary" disabled={!ready || record.isPending}>
          {record.isPending ? "Saving…" : "Record result"}
        </button>
      </div>
    </form>
  );
}

function NewVersion({
  dataset,
  latest,
  batches,
  requests,
  sources,
  onClose,
}: {
  dataset: Dataset;
  latest?: DatasetVersion;
  batches: Batch[];
  requests: Schemas["Request"][];
  sources: Schemas["DataSource"][];
  onClose: () => void;
}) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [chosen, setChosen] = useState<Set<string>>(new Set());
  const [notes, setNotes] = useState("");
  const forCapability = new Set(requests.filter((r) => r.capability_id === dataset.capability_id).map((r) => r.id));
  const already = new Set(latest?.batch_ids ?? []);
  const candidates = batches.filter((b) => b.status === "accepted" && forCapability.has(b.request_id) && !already.has(b.id));
  const sourceName = new Map(sources.map((s) => [s.id, s.name]));
  const requestTitle = new Map(requests.map((r) => [r.id, r.title]));
  const create = useMutation({
    mutationFn: () =>
      api<DatasetVersion>(`/v1/datasets/${dataset.id}/versions`, { method: "POST", body: { batch_ids: [...chosen], notes } }),
    onSuccess: (v) => {
      void queryClient.invalidateQueries({ queryKey: ["lineage", dataset.id] });
      void queryClient.invalidateQueries({ queryKey: ["datasets"] });
      onClose();
      navigate(`/lineage/${dataset.id}?v=${v.version}`);
    },
  });
  return (
    <Drawer label="New dataset version" kicker={dataset.name} title={`Freeze v${(latest?.version ?? 0) + 1}`} onClose={onClose}>
      <form
        className="form"
        onSubmit={(e) => {
          e.preventDefault();
          if (chosen.size) create.mutate();
        }}
      >
        <div className="muted">
          {latest
            ? `Starts from v${latest.version}'s ${latest.batch_ids.length} deliveries and adds the ones you pick. v${latest.version} becomes the baseline its eval change is measured against.`
            : "Pick the accepted deliveries that make up version 1."}{" "}
          A version can't change after it's created.
        </div>
        <div className="section-label">Accepted deliveries not in it yet</div>
        {candidates.length === 0 ? (
          <div className="muted">None. Accept more deliveries first.</div>
        ) : (
          <div className="checklist">
            {candidates.map((b) => (
              <label key={b.id}>
                <input
                  type="checkbox"
                  checked={chosen.has(b.id)}
                  onChange={(e) =>
                    setChosen((c) => {
                      const next = new Set(c);
                      if (e.target.checked) next.add(b.id);
                      else next.delete(b.id);
                      return next;
                    })
                  }
                />
                <span>
                  {sourceName.get(b.data_source_id) ?? "Unknown"} · {count(b.accepted_count)} accepted · {money(b.spend, b.currency)}
                  <div className="muted" style={{ fontSize: 12 }}>{requestTitle.get(b.request_id)} · {day(b.received_at)}</div>
                </span>
              </label>
            ))}
          </div>
        )}
        <label className="field">
          <span>Notes</span>
          <input type="text" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="e.g. Adds the cold-chain deliveries" />
        </label>
        {create.isError && <div className="notice bad" role="alert">{problemText(create.error)}</div>}
        <div className="actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn primary" disabled={!chosen.size || create.isPending}>
            {create.isPending ? "Freezing…" : `Freeze with ${chosen.size} new deliver${chosen.size === 1 ? "y" : "ies"}`}
          </button>
        </div>
      </form>
    </Drawer>
  );
}

function NewDataset({ onClose }: { onClose: () => void }) {
  const { projectId } = useSession();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const capabilities = useCapabilities(projectId);
  const [form, setForm] = useState({ capability_id: "", name: "", description: "" });
  const set = (name: keyof typeof form) => (e: { target: { value: string } }) => setForm((f) => ({ ...f, [name]: e.target.value }));
  const create = useMutation({
    mutationFn: () => api<Dataset>("/v1/datasets", { method: "POST", body: { ...form, name: form.name.trim() } }),
    onSuccess: (ds) => {
      void queryClient.invalidateQueries({ queryKey: ["datasets"] });
      onClose();
      navigate(`/lineage/${ds.id}`);
    },
  });
  const ready = form.capability_id && form.name.trim();
  return (
    <Drawer label="New dataset" title="New dataset" onClose={onClose}>
      <form
        className="form"
        onSubmit={(e) => {
          e.preventDefault();
          if (ready) create.mutate();
        }}
      >
        <label className="field">
          <span>Capability it trains</span>
          <select className="input" value={form.capability_id} onChange={set("capability_id")}>
            <option value="">Choose…</option>
            {(capabilities.data ?? []).map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Name</span>
          <input type="text" value={form.name} onChange={set("name")} placeholder="e.g. damage-det" />
        </label>
        <label className="field">
          <span>Description</span>
          <input type="text" value={form.description} onChange={set("description")} />
        </label>
        {create.isError && <div className="notice bad" role="alert">{problemText(create.error)}</div>}
        <div className="actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn primary" disabled={!ready || create.isPending}>
            {create.isPending ? "Creating…" : "Create dataset"}
          </button>
        </div>
      </form>
    </Drawer>
  );
}

