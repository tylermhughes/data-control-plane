import { useMutation, useQueries, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router";

import { ApiError, api } from "../api/client";
import type { Schemas } from "../api/client";
import { amounts, count, kindLabel, money, points, ratio, unitCosts } from "../format";
import { useSession } from "../session";
import { useTutorial } from "../tutorial/engine";

type Portfolio = Schemas["Portfolio"];
type CapabilityRow = Schemas["CapabilityRow"];
type Diagnosis = Schemas["Diagnosis"];

const RECOMMENDATION: Record<Diagnosis["recommendation"], { label: string; tone: string }> = {
  keep_going: { label: "Keep going", tone: "good" },
  refine_spec: { label: "Refine the spec", tone: "warn" },
  investigate: { label: "Investigate", tone: "warn" },
  not_enough_data: { label: "Not enough data yet", tone: "neutral" },
};

function totalsByCurrency(rows: { currency: string; amount: string }[][]): { currency: string; amount: string }[] {
  const sums = new Map<string, number>();
  for (const list of rows) for (const a of list) sums.set(a.currency, (sums.get(a.currency) ?? 0) + Number(a.amount));
  return [...sums].map(([currency, amount]) => ({ currency, amount: amount.toFixed(2) }));
}

function usable(rows: { usable_units: { unit: string; count: number }[] }[]): string {
  const sums = new Map<string, number>();
  for (const r of rows) for (const u of r.usable_units) sums.set(u.unit, (sums.get(u.unit) ?? 0) + u.count);
  if (sums.size === 0) return "0";
  return [...sums].map(([unit, n]) => `${count(n)} ${unit}`).join(", ");
}

export function Portfolio() {
  const { projectId } = useSession();
  const tutorial = useTutorial();
  const portfolio = useQuery({
    queryKey: ["portfolio", projectId],
    queryFn: () => api<Portfolio>("/v1/reports/portfolio", { query: { project_id: projectId } }),
  });
  const caps = portfolio.data?.by_capability ?? [];
  const diagnoses = useQueries({
    queries: caps.map((c) => ({
      queryKey: ["diagnosis", c.capability_id],
      queryFn: () => api<Diagnosis>(`/v1/capabilities/${c.capability_id}/diagnosis`),
    })),
  });

  if (portfolio.isPending) return <div className="panel empty">Loading the portfolio…</div>;
  if (portfolio.isError) {
    return <div className="notice bad">Couldn't load the portfolio: {portfolio.error.message}</div>;
  }
  const report = portfolio.data;
  const value = totalsByCurrency(caps.filter((c) => c.value).map((c) => [{ currency: c.currency, amount: c.value! }]));
  const scored = totalsByCurrency(caps.filter((c) => c.value).map((c) => c.spend_on_scored_versions));
  const overallRoi =
    value.length === 1 && scored.length === 1 && Number(scored[0].amount) > 0
      ? Number(value[0].amount) / Number(scored[0].amount)
      : null;

  return (
    <>
      <div className="view-head">
        <div>
          <h1>Portfolio</h1>
          <div className="sub">Which data spend actually improved the models.</div>
        </div>
        <button type="button" className="btn tourbtn" onClick={() => tutorial.start(tutorial.state.done.length ? undefined : "welcome")}>
          Walk me through it
        </button>
      </div>

      <div className="stats" role="group" aria-label="Totals">
        <div className="stat">
          <div className="k">Data spend</div>
          <div className="v">{amounts(totalsByCurrency(caps.map((c) => c.spend)))}</div>
        </div>
        <div className="stat">
          <div className="k">Usable units</div>
          <div className="v">{usable(caps)}</div>
        </div>
        <div className="stat">
          <div className="k">Value of eval gains</div>
          <div className="v">{value.length ? amounts(value) : "—"}</div>
        </div>
        <div className="stat">
          <div className="k">Return on scored spend</div>
          <div className="v">{ratio(overallRoi)}</div>
        </div>
      </div>

      {caps.length === 0 ? (
        <div className="panel empty">
          No capabilities yet. Create one (and run <span className="mono">scripts/demo.py</span> for
          sample data) to see the portfolio.
        </div>
      ) : (
        <div className="stack">
          <CapabilityTable rows={caps} />
          <SourceKindTable report={report} />
          <h2 style={{ margin: "8px 0 0" }}>Diagnosis</h2>
          <div className="grid-2">
            {caps.map((cap, i) => (
              <DiagnosisCard key={cap.capability_id} capability={cap} diagnosis={diagnoses[i]?.data} />
            ))}
          </div>
        </div>
      )}
    </>
  );
}

function CapabilityTable({ rows }: { rows: CapabilityRow[] }) {
  const best = Math.max(0, ...rows.map((r) => r.points_per_10k ?? 0));
  return (
    <div className="panel" data-tour="by-capability">
      <h2>By capability</h2>
      <div className="tablewrap">
        <table>
          <thead>
            <tr>
              <th>Capability</th>
              <th className="r">Spend</th>
              <th className="r">Usable</th>
              <th className="r">Cost / usable</th>
              <th className="r">Eval change</th>
              <th>Points per $10K</th>
              <th className="r">Value</th>
              <th className="r">ROI</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.capability_id}>
                <td>
                  <div style={{ fontWeight: 500 }}>{r.name}</div>
                  <div className="muted" style={{ fontSize: 12 }}>
                    {r.eval_metric} · {money(r.value_per_point, r.currency)} per point
                  </div>
                </td>
                <td className="r">{amounts(r.spend)}</td>
                <td className="r">{usable([r])}</td>
                <td className="r">
                  {unitCosts(r.cost_per_usable_unit)}
                </td>
                <td className="r">{r.eval_change_points === null ? "—" : `${points(r.eval_change_points)} pts`}</td>
                <td>
                  {r.points_per_10k === null ? (
                    <span className="muted">—</span>
                  ) : (
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <div className="bar" style={{ flex: 1 }}>
                        <i style={{ width: `${best ? Math.max(4, (r.points_per_10k / best) * 100) : 0}%` }} />
                      </div>
                      <span className="num">{r.points_per_10k.toFixed(2)}</span>
                    </div>
                  )}
                </td>
                <td className="r">{money(r.value, r.currency)}</td>
                <td className="r">{ratio(r.roi)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.some((r) => r.notes.length) && (
        <ul className="muted" style={{ fontSize: 12.5, margin: "10px 0 0", paddingLeft: 18 }}>
          {rows.flatMap((r) => r.notes.map((n) => <li key={r.capability_id + n}>{r.name}: {n}</li>))}
        </ul>
      )}
    </div>
  );
}

function SourceKindTable({ report }: { report: Portfolio }) {
  if (report.by_source_kind.length === 0) return null;
  return (
    <div className="panel" data-tour="by-source-kind">
      <div style={{ display: "flex", justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}>
        <h2>By source type</h2>
        <span className="pill neutral" title="Each version's eval change is split by each source type's share of the items it added.">
          Eval change is an estimate
        </span>
      </div>
      <div className="tablewrap">
        <table>
          <thead>
            <tr>
              <th>Source type</th>
              <th className="r">Spend</th>
              <th className="r">Usable</th>
              <th className="r">Cost / usable</th>
              <th className="r">Eval change (est.)</th>
              <th className="r">Points per $10K</th>
            </tr>
          </thead>
          <tbody>
            {report.by_source_kind.map((r) => (
              <tr key={r.kind}>
                <td>{kindLabel(r.kind)}</td>
                <td className="r">{amounts(r.spend)}</td>
                <td className="r">{usable([r])}</td>
                <td className="r">
                  {unitCosts(r.cost_per_usable_unit)}
                </td>
                <td className="r">{r.eval_change_points === null ? "—" : `${points(r.eval_change_points)} pts`}</td>
                <td className="r">{r.points_per_10k === null ? "—" : r.points_per_10k.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function DiagnosisCard({ capability, diagnosis }: { capability: CapabilityRow; diagnosis?: Diagnosis }) {
  const { canWrite } = useSession();
  const queryClient = useQueryClient();
  const draft = useMutation({
    mutationFn: () =>
      api<Schemas["SpecVersion"]>(`/v1/capabilities/${capability.capability_id}/diagnosis/draft-spec`, {
        method: "POST",
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["diagnosis", capability.capability_id] }),
  });
  if (!diagnosis) {
    return <div className="panel muted">{capability.name}: loading the diagnosis…</div>;
  }
  const rec = RECOMMENDATION[diagnosis.recommendation];
  const change = diagnosis.suggested_spec_change;
  return (
    <div className={`rec${rec.tone === "warn" ? " warn" : ""}`} data-testid="diagnosis">
      <div style={{ display: "flex", justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}>
        <h3 style={{ margin: 0 }}>{capability.name}</h3>
        <span className={`pill ${rec.tone}`}>{rec.label}</span>
      </div>
      <div>{diagnosis.summary}</div>
      {diagnosis.versions.length > 0 && (
        <div className="muted" style={{ fontSize: 12.5 }}>
          {diagnosis.versions
            .map((v) => `v${v.version}: ${points(v.points)} pts${v.points_per_10k === null ? "" : `, ${v.points_per_10k.toFixed(2)}/10K`}`)
            .join(" · ")}
        </div>
      )}
      {change && (
        <div className="panel" style={{ padding: 12 }}>
          <h3>Suggested coverage targets</h3>
          {Object.entries(change.coverage_targets).map(([attr, values]) => (
            <div key={attr} style={{ fontSize: 13 }}>
              <span className="muted">{attr}: </span>
              {Object.entries(values)
                .map(([v, share]) => `${v} ${(share * 100).toFixed(0)}%`)
                .join(" · ")}
            </div>
          ))}
          {draft.isSuccess ? (
            <div className="notice good" style={{ marginTop: 10 }}>
              Drafted spec version {draft.data.version} for review.{" "}
              <Link to={`/specs/${draft.data.spec_id}?v=${draft.data.version}`}>Review and approve it in Specs</Link>.
            </div>
          ) : (
            <div style={{ marginTop: 10, display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
              <button
                className="btn primary"
                type="button"
                disabled={!canWrite || draft.isPending}
                title={canWrite ? undefined : "Needs an API key with write access"}
                onClick={() => draft.mutate()}
              >
                {draft.isPending ? "Drafting…" : "Draft the refined spec"}
              </button>
              {draft.isError && (
                <span className="notice bad" role="alert">
                  {draft.error instanceof ApiError ? draft.error.problem.detail : draft.error.message}
                </span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
