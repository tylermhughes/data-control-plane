import type { Schemas } from "../api/client";
import { percent, words } from "../format";

/** Coverage vs targets: one bar per attribute value (its share) with a tick at the target. */
export function CoverageBars({ coverage, what }: { coverage: Schemas["Coverage"]; what: string }) {
  const attrs = coverage.attributes.filter((a) => a.counted > 0 && a.values.length);
  if (attrs.length === 0) return <div className="muted">No attribute counts were recorded for {what} yet.</div>;
  const from = new Set(Object.values(coverage.counts_from).filter((f) => f !== "none"));
  return (
    <div className="stack" style={{ gap: 14 }}>
      {coverage.gaps.length > 0 && <div className="notice warn">Below target: {coverage.gaps.join("; ")}</div>}
      {attrs.map((a) => (
        <div key={a.attribute}>
          <div className="section-label">{words(a.attribute)}</div>
          {a.values.map((v) => (
            <div key={v.value} className="qrow">
              <span>{words(v.value)}</span>
              <div className="qbar" title={v.target_share === null ? "No target" : `Target ${percent(v.target_share)}`}>
                <i className={v.status === "below" ? "low" : ""} style={{ width: `${(v.actual_share ?? 0) * 100}%` }} />
                {v.target_share !== null && <b style={{ left: `${v.target_share * 100}%` }} />}
              </div>
              <span className="num" style={{ textAlign: "right" }}>
                {percent(v.actual_share)}
                <span className="muted"> / {v.target_share === null ? "—" : percent(v.target_share)}</span>
              </span>
            </div>
          ))}
        </div>
      ))}
      <div className="muted" style={{ fontSize: 12 }}>
        Bar: share of {what}. Tick: the spec's target. Amber: more than {percent(coverage.tolerance)} below target.
        {from.size > 0 &&
          ` Counts from ${[...from].map((f) => (f === "files" ? "DCP's checks on the files" : "the sources' reports")).join(" and ")}.`}
      </div>
    </div>
  );
}
