import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, Navigate, useNavigate, useParams, useSearchParams } from "react-router";

import { api, listAll } from "../api/client";
import type { Schemas } from "../api/client";
import { Drawer } from "../components/Drawer";
import { day, percent, words } from "../format";
import { useSession } from "../session";
import { diffContent, diffLines, ruleText } from "../specDiff";
import type { Version } from "../specDiff";
import { problemText } from "./Batch";

type Spec = Schemas["Spec"];
type SpecVersion = Schemas["SpecVersion"] & Version;

export function Specs() {
  const { projectId, canWrite } = useSession();
  const { specId } = useParams();
  const [creating, setCreating] = useState(false);
  const specs = useQuery({
    queryKey: ["specs", projectId],
    queryFn: () => listAll<Spec>("/v1/specs", { project_id: projectId }),
  });

  if (specs.isPending) return <div className="panel empty">Loading specs…</div>;
  if (specs.isError) return <div className="notice bad">Couldn't load specs: {problemText(specs.error)}</div>;
  const list = specs.data;
  if (!specId && list.length > 0) return <Navigate to={`/specs/${list[0].id}`} replace />;
  const current = list.find((s) => s.id === specId);

  return (
    <>
      <div className="view-head">
        <div>
          <h1>Specs</h1>
          <div className="sub">Versioned guidelines, attributes, coverage targets and acceptance rules. Every request and delivery points to the exact version it used.</div>
        </div>
        <button
          type="button"
          className="btn primary"
          disabled={!canWrite}
          title={canWrite ? undefined : "Needs an API key with write access"}
          onClick={() => setCreating(true)}
        >
          New spec
        </button>
      </div>
      {list.length === 0 ? (
        <div className="panel empty">No specs yet. Create one to describe the data you want.</div>
      ) : (
        <div className="grid-list">
          <nav className="list" aria-label="Specs">
            {list.map((s) => (
              <Link key={s.id} to={`/specs/${s.id}`} aria-current={s.id === specId ? "page" : undefined}>
                {s.name}
                <span>
                  v{s.latest_approved_version ?? "–"} approved
                  {s.draft_version ? ` · v${s.draft_version} draft` : ""}
                </span>
              </Link>
            ))}
          </nav>
          {current ? (
            <SpecDetail key={current.id} spec={current} />
          ) : (
            <div className="notice bad">That spec doesn't exist in this project.</div>
          )}
        </div>
      )}
      {creating && <NewSpec onClose={() => setCreating(false)} />}
    </>
  );
}

function SpecDetail({ spec }: { spec: Spec }) {
  const [params, setParams] = useSearchParams();
  const [showChanges, setShowChanges] = useState(true);
  const versions = useQuery({
    queryKey: ["spec-versions", spec.id],
    queryFn: () => listAll<SpecVersion>(`/v1/specs/${spec.id}/versions`),
  });
  const usedBy = useQuery({
    queryKey: ["requests", spec.project_id],
    queryFn: () => listAll<Schemas["Request"]>("/v1/requests", { project_id: spec.project_id }),
  });

  if (versions.isPending) return <div className="panel muted">Loading versions…</div>;
  if (versions.isError) return <div className="notice bad">{problemText(versions.error)}</div>;
  const all = [...versions.data].sort((a, b) => b.version - a.version);
  const wanted = Number(params.get("v") ?? spec.latest_version);
  const v = all.find((x) => x.version === wanted) ?? all[0];
  const previous = all.find((x) => x.version < v.version);
  const requests = (usedBy.data ?? []).filter((r) => r.spec_id === spec.id);

  return (
    <div className="grid-2">
      <div className="stack">
        <div className="panel">
          <div className="spec-head">
            <div>
              <h2 style={{ marginBottom: 4 }}>
                {spec.name} <span className="mono muted">v{v.version}</span>
              </h2>
              <div className="sub">
                {v.status === "approved" ? (
                  <>
                    <span className="pill good">Approved</span> by {v.approved_by}, {day(v.approved_at)}
                  </>
                ) : (
                  <>
                    <span className="pill accent">Draft</span> updated {day(v.updated_at)}
                  </>
                )}
              </div>
              {spec.description && <p style={{ margin: "8px 0 0" }}>{spec.description}</p>}
            </div>
            {previous && (
              <label className="toggle">
                <input type="checkbox" checked={showChanges} onChange={(e) => setShowChanges(e.target.checked)} />
                Show changes since v{previous.version}
              </label>
            )}
          </div>
          <SpecContent version={v} previous={showChanges ? previous : undefined} />
        </div>
      </div>
      <div className="stack">
        {v.status === "draft" ? (
          <DraftActions spec={spec} version={v} />
        ) : (
          v.version === spec.latest_version && <NewVersion spec={spec} onCreated={(n) => setParams({ v: String(n) })} />
        )}
        <div className="panel" role="region" aria-label="Version history">
          <h2>Version history</h2>
          <ul className="timeline">
            {all.map((x) => (
              <li key={x.id} aria-current={x.version === v.version}>
                <Link to={`/specs/${spec.id}?v=${x.version}`}>
                  <b>v{x.version}</b>{" "}
                  <span className={`pill ${x.status === "approved" ? "good" : "accent"}`}>{x.status}</span>
                  <div>{x.change_note || <span className="muted">No change note.</span>}</div>
                  <div className="muted" style={{ fontSize: 12 }}>
                    {x.status === "approved" ? `${x.approved_by}, ${day(x.approved_at)}` : `Created ${day(x.created_at)}`}
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </div>
        <div className="panel" role="region" aria-label="Used by">
          <h2>Used by</h2>
          {requests.length === 0 ? (
            <div className="muted">No requests use this spec yet.</div>
          ) : (
            <div className="stack" style={{ gap: 6 }}>
              {requests.map((r) => (
                <Link key={r.id} to={`/requests/${r.id}`} className="rowlink">
                  <span>{r.title}</span>
                  <span className="muted">v{r.spec_version} · {r.status}</span>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SpecContent({ version: v, previous }: { version: SpecVersion; previous?: SpecVersion }) {
  const lines = diffLines(previous?.guidelines ?? v.guidelines, v.guidelines);
  const changes = previous ? diffContent(previous, v) : [];
  const guidelinesChanged = previous !== undefined && previous.guidelines !== v.guidelines;
  return (
    <>
      {previous && (
        <div className="rule-section" role="region" aria-label="Changes">
          <h3>Changes since v{previous.version}</h3>
          {changes.length === 0 && !guidelinesChanged ? (
            <div className="muted">No changes yet.</div>
          ) : (
            <>
              <div className="legend" style={{ marginBottom: 8 }}>
                <span><span className="ins">Added or new</span></span>
                <span><span className="del">Removed or old</span></span>
              </div>
              <ul className="rules">
                {guidelinesChanged && <li>Guidelines changed (highlighted below).</li>}
                {changes.map((c) => (
                  <li key={c.kind + c.text}>
                    {c.kind === "changed" ? (
                      <>
                        <span className="del">{c.old}</span> <span className="ins"><span className="tag">Changed</span>{c.text}</span>
                      </>
                    ) : (
                      <span className={c.kind === "added" ? "ins" : "del"}>
                        <span className="tag">{c.kind === "added" ? "Added" : "Removed"}</span>
                        {c.text}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
      <div className="rule-section">
        <h3>Guidelines</h3>
        {v.guidelines || previous?.guidelines ? (
          <div className="guidelines">
            {lines.map((l, i) => (
              <div key={i}>
                {l.kind === "same" ? l.text : <span className={l.kind === "added" ? "ins" : "del"}>{l.text || " "}</span>}
              </div>
            ))}
          </div>
        ) : (
          <div className="muted">No guidelines written yet.</div>
        )}
      </div>
      <div className="rule-section">
        <h3>Attributes and coverage targets</h3>
        {v.attributes.length === 0 ? (
          <div className="muted">No attributes. Add some to track the data mix.</div>
        ) : (
          <div className="tablewrap">
            <table>
              <thead>
                <tr>
                  <th>Attribute</th>
                  <th>Value</th>
                  <th className="r">Target share</th>
                </tr>
              </thead>
              <tbody>
                {v.attributes.flatMap((a) =>
                  a.values.map((value, i) => {
                    const share = v.coverage_targets[a.name]?.[value];
                    return (
                      <tr key={a.name + value}>
                        <td className="muted">{i === 0 ? words(a.name) : ""}</td>
                        <td>{words(value)}</td>
                        <td className="r">{share === undefined ? "—" : percent(share, share * 100 % 1 ? 1 : 0)}</td>
                      </tr>
                    );
                  }),
                )}
              </tbody>
            </table>
          </div>
        )}
        <div className="muted" style={{ fontSize: 12, marginTop: 6 }}>
          A value is flagged when it's more than {percent(v.coverage_tolerance)} below its target.
        </div>
      </div>
      <div className="rule-section">
        <h3>Acceptance rules</h3>
        {v.acceptance_rules.length === 0 ? (
          <div className="muted">No acceptance rules.</div>
        ) : (
          <ul className="rules">
            {v.acceptance_rules.map((r) => (
              <li key={ruleText(r)}>
                <span className="mono">{ruleText(r)}</span>
                {r.description && <span className="muted"> · {r.description}</span>}
              </li>
            ))}
          </ul>
        )}
      </div>
      {v.record_schema && (
        <div className="rule-section">
          <details>
            <summary>Record format (JSON Schema)</summary>
            <pre className="code">{JSON.stringify(v.record_schema, null, 2)}</pre>
          </details>
        </div>
      )}
    </>
  );
}

function useSpecRefresh(spec: Spec) {
  const queryClient = useQueryClient();
  return () => {
    void queryClient.invalidateQueries({ queryKey: ["specs"] });
    void queryClient.invalidateQueries({ queryKey: ["spec-versions", spec.id] });
  };
}

function NewVersion({ spec, onCreated }: { spec: Spec; onCreated: (version: number) => void }) {
  const { canWrite } = useSession();
  const refresh = useSpecRefresh(spec);
  const create = useMutation({
    mutationFn: () => api<SpecVersion>(`/v1/specs/${spec.id}/versions`, { method: "POST", body: {} }),
    onSuccess: (v) => {
      refresh();
      onCreated(v.version);
    },
  });
  return (
    <div className="panel" role="region" aria-label="Change this spec">
      <h2>Change this spec</h2>
      <p className="muted" style={{ marginTop: 0 }}>
        Approved versions never change. Start a draft of v{spec.latest_version + 1} (a copy of this one), edit it, then approve it.
      </p>
      {create.isError && <div className="notice bad" role="alert">{problemText(create.error)}</div>}
      <button
        type="button"
        className="btn primary"
        disabled={!canWrite || create.isPending}
        title={canWrite ? undefined : "Needs an API key with write access"}
        onClick={() => create.mutate()}
      >
        Start v{spec.latest_version + 1}
      </button>
    </div>
  );
}

function DraftActions({ spec, version: v }: { spec: Spec; version: SpecVersion }) {
  const { canWrite } = useSession();
  const navigate = useNavigate();
  const refresh = useSpecRefresh(spec);
  const [editing, setEditing] = useState(false);
  const [approver, setApprover] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const approve = useMutation({
    mutationFn: () =>
      api<SpecVersion>(`/v1/specs/${spec.id}/versions/${v.version}/approve`, {
        method: "POST",
        body: { approved_by: approver.trim() },
      }),
    onSuccess: refresh,
  });
  const remove = useMutation({
    mutationFn: () => api<void>(`/v1/specs/${spec.id}/versions/${v.version}`, { method: "DELETE" }),
    onSuccess: () => {
      refresh();
      navigate(`/specs/${spec.id}`);
    },
  });

  if (!canWrite) {
    return (
      <div className="panel" role="region" aria-label="Draft">
        <h2>Draft</h2>
        <div className="notice info">This version is a draft. Editing and approving need an API key with write access.</div>
      </div>
    );
  }
  return (
    <div className="panel decide" role="region" aria-label="Draft">
      <h2 style={{ margin: 0 }}>Review this draft</h2>
      <div className="muted">Requests can only use approved versions. Once approved, a version can never change.</div>
      <button type="button" className="btn" onClick={() => setEditing(true)} style={{ alignSelf: "flex-start" }}>
        Edit draft
      </button>
      <form
        className="decide"
        onSubmit={(e) => {
          e.preventDefault();
          if (approver.trim()) approve.mutate();
        }}
      >
        <label className="field">
          <span>Approved by</span>
          <input type="text" value={approver} onChange={(e) => setApprover(e.target.value)} placeholder="Your name" />
        </label>
        {approve.isError && <div className="notice bad" role="alert">{problemText(approve.error)}</div>}
        <div className="row">
          <button type="submit" className="btn primary" disabled={!approver.trim() || approve.isPending}>
            {approve.isPending ? "Approving…" : `Approve v${v.version}`}
          </button>
          {v.version > 1 &&
            (confirmDelete ? (
              <button type="button" className="btn primary danger" onClick={() => remove.mutate()} disabled={remove.isPending}>
                Yes, delete v{v.version}
              </button>
            ) : (
              <button type="button" className="btn" onClick={() => setConfirmDelete(true)}>
                Delete draft
              </button>
            ))}
        </div>
        {remove.isError && <div className="notice bad" role="alert">{problemText(remove.error)}</div>}
      </form>
      {editing && <DraftEditor spec={spec} version={v} onClose={() => setEditing(false)} onSaved={refresh} />}
    </div>
  );
}

// --- editing ---------------------------------------------------------------------------------

type RuleRow = { metric: string; operator: string; threshold: string; rest: Partial<Schemas["AcceptanceRule"]> };

/** "package_type: box, mailer" lines <-> attributes. */
export function attributesToText(attributes: Schemas["Attribute"][]): string {
  return attributes.map((a) => `${a.name}: ${a.values.join(", ")}`).join("\n");
}

export function textToAttributes(text: string, old: Schemas["Attribute"][] = []): Schemas["Attribute"][] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [name, ...rest] = line.split(":");
      const values = rest.join(":").split(",").map((v) => v.trim()).filter(Boolean);
      const description = old.find((a) => a.name === name.trim())?.description ?? "";
      return { name: name.trim(), values, description };
    });
}

function DraftEditor({
  spec,
  version: v,
  onClose,
  onSaved,
}: {
  spec: Spec;
  version: SpecVersion;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [guidelines, setGuidelines] = useState(v.guidelines);
  const [attrText, setAttrText] = useState(attributesToText(v.attributes));
  const [targets, setTargets] = useState<Record<string, Record<string, string>>>(() =>
    Object.fromEntries(
      Object.entries(v.coverage_targets).map(([a, values]) => [
        a,
        Object.fromEntries(Object.entries(values).map(([value, share]) => [value, String(Math.round(share * 1000) / 10)])),
      ]),
    ),
  );
  const [tolerance, setTolerance] = useState(String(Math.round(v.coverage_tolerance * 1000) / 10));
  const [rules, setRules] = useState<RuleRow[]>(
    v.acceptance_rules.map(({ metric, operator, threshold, ...rest }) => ({ metric, operator, threshold: String(threshold), rest })),
  );
  const [note, setNote] = useState(v.change_note);
  const attributes = textToAttributes(attrText, v.attributes);

  const save = useMutation({
    mutationFn: () => {
      const coverage_targets: Record<string, Record<string, number>> = {};
      for (const a of attributes) {
        for (const value of a.values) {
          const raw = targets[a.name]?.[value]?.trim();
          if (raw) (coverage_targets[a.name] ??= {})[value] = Math.round(Number(raw) * 10) / 1000;
        }
      }
      return api<SpecVersion>(`/v1/specs/${spec.id}/versions/${v.version}`, {
        method: "PATCH",
        body: {
          guidelines,
          attributes,
          coverage_targets,
          coverage_tolerance: Math.round(Number(tolerance) * 10) / 1000,
          acceptance_rules: rules
            .filter((r) => r.metric.trim())
            .map((r) => ({ ...r.rest, metric: r.metric.trim(), operator: r.operator, threshold: Number(r.threshold) })),
          change_note: note,
        },
      });
    },
    onSuccess: () => {
      onSaved();
      onClose();
    },
  });
  const setTarget = (attr: string, value: string, share: string) =>
    setTargets((t) => ({ ...t, [attr]: { ...t[attr], [value]: share } }));
  const setRule = (i: number, change: Partial<RuleRow>) => setRules((rs) => rs.map((r, j) => (j === i ? { ...r, ...change } : r)));

  return (
    <Drawer label="Edit draft" kicker={`${spec.name}`} title={`Edit draft v${v.version}`} onClose={onClose}>
      <form
        className="form"
        onSubmit={(e) => {
          e.preventDefault();
          save.mutate();
        }}
      >
        <label className="field">
          <span>What changed in this version?</span>
          <input type="text" value={note} onChange={(e) => setNote(e.target.value)} />
        </label>
        <label className="field">
          <span>Guidelines</span>
          <textarea rows={8} value={guidelines} onChange={(e) => setGuidelines(e.target.value)} />
        </label>
        <label className="field">
          <span>Attributes, one per line: name: value, value, …</span>
          <textarea rows={3} value={attrText} onChange={(e) => setAttrText(e.target.value)} className="mono" />
        </label>
        {attributes.some((a) => a.values.length) && (
          <div>
            <div className="section-label">Coverage targets (% of items)</div>
            {attributes.map((a) => {
              const total = a.values.reduce((sum, value) => sum + (Number(targets[a.name]?.[value]) || 0), 0);
              return (
                <div key={a.name} style={{ marginBottom: 10 }}>
                  <div className="muted" style={{ fontSize: 12.5, marginBottom: 4 }}>
                    {words(a.name)} <span className={total > 100.0001 ? "pill bad" : "pill neutral"}>total {Math.round(total * 10) / 10}%</span>
                  </div>
                  <div className="pair">
                    {a.values.map((value) => (
                      <label key={value} className="field">
                        <span>{words(value)}</span>
                        <input
                          type="number"
                          min={0}
                          max={100}
                          step={0.1}
                          value={targets[a.name]?.[value] ?? ""}
                          onChange={(e) => setTarget(a.name, value, e.target.value)}
                        />
                      </label>
                    ))}
                  </div>
                </div>
              );
            })}
            <label className="field" style={{ maxWidth: 220 }}>
              <span>Flag values more than this many points below target</span>
              <input type="number" min={0} max={100} step={0.1} value={tolerance} onChange={(e) => setTolerance(e.target.value)} />
            </label>
          </div>
        )}
        <div>
          <div className="section-label">Acceptance rules</div>
          <div className="stack" style={{ gap: 6 }}>
            {rules.map((r, i) => (
              <div key={i} className="ruleRow">
                <input type="text" aria-label="Metric" value={r.metric} onChange={(e) => setRule(i, { metric: e.target.value })} placeholder="metric, e.g. agreement" />
                <select className="input" aria-label="Operator" value={r.operator} onChange={(e) => setRule(i, { operator: e.target.value })}>
                  {[">=", ">", "<=", "<", "=="].map((op) => (
                    <option key={op}>{op}</option>
                  ))}
                </select>
                <input type="number" step="any" aria-label="Threshold" value={r.threshold} onChange={(e) => setRule(i, { threshold: e.target.value })} />
                <button type="button" className="x" aria-label="Remove rule" onClick={() => setRules((rs) => rs.filter((_, j) => j !== i))}>
                  ×
                </button>
              </div>
            ))}
          </div>
          <button
            type="button"
            className="btn"
            style={{ marginTop: 6 }}
            onClick={() => setRules((rs) => [...rs, { metric: "", operator: ">=", threshold: "0", rest: {} }])}
          >
            Add a rule
          </button>
          <div className="hint" style={{ marginTop: 4 }}>
            Metrics come from DCP's checks (duplicate_rate, schema_valid_rate, …) or the source's report (e.g. agreement).
          </div>
        </div>
        {save.isError && <div className="notice bad" role="alert">{problemText(save.error)}</div>}
        <div className="actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn primary" disabled={save.isPending}>
            {save.isPending ? "Saving…" : "Save draft"}
          </button>
        </div>
      </form>
    </Drawer>
  );
}

function NewSpec({ onClose }: { onClose: () => void }) {
  const { projectId, projects } = useSession();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [project, setProject] = useState(projectId ?? "");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [guidelines, setGuidelines] = useState("");
  const [attrText, setAttrText] = useState("");
  const create = useMutation({
    mutationFn: () =>
      api<Spec>("/v1/specs", {
        method: "POST",
        body: {
          project_id: project || undefined,
          name: name.trim(),
          description,
          first_version: { guidelines, attributes: textToAttributes(attrText), change_note: "First version." },
        },
      }),
    onSuccess: (spec) => {
      void queryClient.invalidateQueries({ queryKey: ["specs"] });
      onClose();
      navigate(`/specs/${spec.id}`);
    },
  });
  return (
    <Drawer label="New spec" title="New spec" onClose={onClose}>
      <form
        className="form"
        onSubmit={(e) => {
          e.preventDefault();
          if (name.trim()) create.mutate();
        }}
      >
        {!projectId && (
          <label className="field">
            <span>Project</span>
            <select className="input" value={project} onChange={(e) => setProject(e.target.value)}>
              <option value="">Choose a project…</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </label>
        )}
        <label className="field">
          <span>Name</span>
          <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Package damage" />
        </label>
        <label className="field">
          <span>Description</span>
          <input type="text" value={description} onChange={(e) => setDescription(e.target.value)} />
        </label>
        <label className="field">
          <span>Guidelines</span>
          <textarea rows={6} value={guidelines} onChange={(e) => setGuidelines(e.target.value)} placeholder="How to collect or label each item." />
        </label>
        <label className="field">
          <span>Attributes, one per line: name: value, value, …</span>
          <textarea rows={3} className="mono" value={attrText} onChange={(e) => setAttrText(e.target.value)} placeholder="package_type: box, mailer, shrink_wrapped" />
        </label>
        <div className="hint">Version 1 starts as a draft. Set coverage targets and acceptance rules by editing it, then approve it.</div>
        {create.isError && <div className="notice bad" role="alert">{problemText(create.error)}</div>}
        <div className="actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn primary" disabled={!name.trim() || (!projectId && !project) || create.isPending}>
            {create.isPending ? "Creating…" : "Create spec"}
          </button>
        </div>
      </form>
    </Drawer>
  );
}
