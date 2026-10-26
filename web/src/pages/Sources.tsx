import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate } from "react-router";

import { api, listAll } from "../api/client";
import type { Schemas } from "../api/client";
import { KIND_COLORS } from "../board";
import { Drawer } from "../components/Drawer";
import { ProjectField } from "../components/ProjectField";
import { count, day, kindLabel, money, percent, today } from "../format";
import { useSession } from "../session";
import { LICENSE_LABELS, rightsStatus, sourceStats } from "../sources";
import { problemText } from "./Batch";

type Source = Schemas["DataSource"];

export const KINDS = Object.keys(KIND_COLORS);

export function useSourcesData(projectId: string | null) {
  const query = { project_id: projectId };
  return useQuery({
    queryKey: ["sources-data", projectId],
    queryFn: async () => {
      const [sources, allocations, batches] = await Promise.all([
        listAll<Source>("/v1/data-sources", query),
        listAll<Schemas["Allocation"]>("/v1/allocations", query),
        listAll<Schemas["Batch"]>("/v1/batches", query),
      ]);
      return { sources, allocations, batches };
    },
  });
}

export function RightsPill({ expires }: { expires: string | null }) {
  const status = rightsStatus(expires, today());
  if (status === "expired") return <span className="pill bad">Rights expired {day(expires)}</span>;
  if (status === "soon") return <span className="pill warn">Rights end {day(expires)}</span>;
  return null;
}

export function Sources() {
  const { projectId, canWrite } = useSession();
  const data = useSourcesData(projectId);
  const [kind, setKind] = useState("all");
  const [creating, setCreating] = useState(false);

  return (
    <>
      <div className="view-head">
        <div>
          <h1>Sources & vendors</h1>
          <div className="sub">Every way you get training data, in one registry: vendors, experts, synthetic, environments, internal workflows, beta users and licensed sets. Each is held to the same quality, rights and cost checks.</div>
        </div>
        <button
          type="button"
          className="btn primary"
          data-tour="new-source"
          disabled={!canWrite}
          title={canWrite ? undefined : "Needs an API key with write access"}
          onClick={() => setCreating(true)}
        >
          New source
        </button>
      </div>
      {data.isPending ? (
        <div className="panel empty">Loading sources…</div>
      ) : data.isError ? (
        <div className="notice bad">Couldn't load sources: {problemText(data.error)}</div>
      ) : data.data.sources.length === 0 ? (
        <div className="panel empty">No sources yet. Add the vendors, teams and datasets you get data from.</div>
      ) : (
        <>
          <div className="filters" role="group" aria-label="Filter by source type" style={{ marginBottom: 12 }}>
            {["all", ...new Set(data.data.sources.map((s) => s.kind))].map((k) => (
              <button key={k} type="button" className="chip" aria-pressed={kind === k} onClick={() => setKind(k)}>
                {k !== "all" && <span className="sw" style={{ background: KIND_COLORS[k] }} />}
                {k === "all" ? "All sources" : kindLabel(k)}
              </button>
            ))}
          </div>
          <div className="cards">
            {data.data.sources
              .filter((s) => kind === "all" || s.kind === kind)
              .map((s) => {
                const st = sourceStats(s.id, data.data.allocations, data.data.batches);
                return (
                  <Link
                    key={s.id}
                    to={`/sources/${s.id}`}
                    className="panel srccard"
                    style={{ ["--c" as string]: KIND_COLORS[s.kind] }}
                    data-testid="source-card"
                  >
                    <span className="sname">
                      {s.name}
                      <span className="pill neutral">{kindLabel(s.kind)}</span>
                    </span>
                    <dl className="kv">
                      <dt>Active allocations</dt><dd>{st.activeAllocations}</dd>
                      <dt>Spend</dt><dd>{st.spend.size ? [...st.spend].map(([c, a]) => money(a, c)).join(" + ") : "$0"}</dd>
                      <dt>Usable {s.default_unit}</dt><dd>{st.accepted ? count(st.accepted) : "—"}</dd>
                      <dt>Accept rate</dt><dd>{percent(st.acceptRate, 1)}</dd>
                      <dt>Cost per usable</dt><dd>{st.costPerUsable ? money(st.costPerUsable.amount, st.costPerUsable.currency) : "—"}</dd>
                    </dl>
                    <span className="muted" style={{ fontSize: 12.5 }}>
                      {LICENSE_LABELS[s.license_type]}
                      {st.waiting ? ` · ${st.waiting} waiting for a decision` : ""}
                    </span>
                    <RightsPill expires={s.rights_expires_at} />
                  </Link>
                );
              })}
          </div>
        </>
      )}
      {creating && <SourceForm onClose={() => setCreating(false)} />}
    </>
  );
}

/** New source (no `source`) or edit one. Kind and project can't change after creation. */
export function SourceForm({ source, onClose }: { source?: Source; onClose: () => void }) {
  const { projectId } = useSession();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [project, setProject] = useState(projectId ?? "");
  const [form, setForm] = useState({
    name: source?.name ?? "",
    kind: source?.kind ?? "human_vendor",
    default_unit: source?.default_unit ?? "images",
    license_type: source?.license_type ?? "vendor_agreement",
    consent_scope: source?.consent_scope ?? "",
    rights_expires_at: source?.rights_expires_at ?? "",
    pii_handling: source?.pii_handling ?? "",
    notes: source?.notes ?? "",
  });
  const set = (name: keyof typeof form) => (e: { target: { value: string } }) => setForm((f) => ({ ...f, [name]: e.target.value }));
  const save = useMutation({
    mutationFn: () => {
      const { kind, ...rest } = form;
      const body = { ...rest, name: form.name.trim(), default_unit: form.default_unit.trim(), rights_expires_at: form.rights_expires_at || null };
      return source
        ? api<Source>(`/v1/data-sources/${source.id}`, { method: "PATCH", body })
        : api<Source>("/v1/data-sources", { method: "POST", body: { ...body, kind, project_id: project || undefined } });
    },
    onSuccess: (saved) => {
      void queryClient.invalidateQueries({ queryKey: ["sources-data"] });
      void queryClient.invalidateQueries({ queryKey: ["data-sources"] });
      queryClient.setQueryData(["data-source", saved.id], saved);
      onClose();
      if (!source) navigate(`/sources/${saved.id}`);
    },
  });
  const ready = form.name.trim() && form.default_unit.trim() && (source || projectId || project);

  return (
    <Drawer label={source ? "Edit source" : "New source"} title={source ? `Edit ${source.name}` : "New source"} onClose={onClose}>
      <form
        className="form"
        onSubmit={(e) => {
          e.preventDefault();
          if (ready) save.mutate();
        }}
      >
        {!source && <ProjectField value={project} onChange={setProject} />}
        <label className="field">
          <span>Name</span>
          <input type="text" value={form.name} onChange={set("name")} placeholder="e.g. Surge" />
        </label>
        <div className="pair">
          <label className="field">
            <span>Type</span>
            <select className="input" value={form.kind} onChange={set("kind")} disabled={Boolean(source)}>
              {KINDS.map((k) => (
                <option key={k} value={k}>{kindLabel(k)}</option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Unit of data</span>
            <input type="text" value={form.default_unit} onChange={set("default_unit")} placeholder="images, tasks, reviews…" />
          </label>
        </div>
        <div className="pair">
          <label className="field">
            <span>Rights basis</span>
            <select className="input" value={form.license_type} onChange={set("license_type")}>
              {Object.entries(LICENSE_LABELS).map(([k, label]) => (
                <option key={k} value={k}>{label}</option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Rights end on</span>
            <input type="date" value={form.rights_expires_at} onChange={set("rights_expires_at")} />
          </label>
        </div>
        <label className="field">
          <span>What contributors agreed to</span>
          <textarea rows={2} value={form.consent_scope} onChange={set("consent_scope")} />
        </label>
        <label className="field">
          <span>Personal data handling</span>
          <textarea rows={2} value={form.pii_handling} onChange={set("pii_handling")} placeholder="e.g. faces blurred before delivery" />
        </label>
        <label className="field">
          <span>Notes</span>
          <textarea rows={2} value={form.notes} onChange={set("notes")} placeholder="Contract, contacts, quote numbers…" />
        </label>
        {save.isError && <div className="notice bad" role="alert">{problemText(save.error)}</div>}
        <div className="actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn primary" disabled={!ready || save.isPending}>
            {save.isPending ? "Saving…" : source ? "Save" : "Create source"}
          </button>
        </div>
      </form>
    </Drawer>
  );
}
