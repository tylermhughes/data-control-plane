import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link } from "react-router";

import { listAll } from "../api/client";
import type { Schemas } from "../api/client";
import { KIND_COLORS, STAGES, boardTotals, buildBoard } from "../board";
import type { Card } from "../board";
import { count, day, kindLabel, money, percent } from "../format";
import { useSession } from "../session";
import { Drawer } from "../components/Drawer";

function useBoardData(projectId: string | null) {
  const query = { project_id: projectId };
  return useQuery({
    queryKey: ["board", projectId],
    queryFn: async () => {
      const [requests, allocations, batches, sources] = await Promise.all([
        listAll<Schemas["Request"]>("/v1/requests", query),
        listAll<Schemas["Allocation"]>("/v1/allocations", query),
        listAll<Schemas["Batch"]>("/v1/batches", query),
        listAll<Schemas["DataSource"]>("/v1/data-sources", query),
      ]);
      return { requests, allocations, batches, sources };
    },
  });
}

export function Board() {
  const { projectId } = useSession();
  const data = useBoardData(projectId);
  const [kind, setKind] = useState<string>("all");
  const [open, setOpen] = useState<Card | null>(null);

  const cards = useMemo(
    () => (data.data ? buildBoard(data.data.requests, data.data.allocations, data.data.batches, data.data.sources) : []),
    [data.data],
  );
  if (data.isPending) return <div className="panel empty">Loading the board…</div>;
  if (data.isError) return <div className="notice bad">Couldn't load the board: {data.error.message}</div>;

  const kinds = [...new Set(data.data.sources.map((s) => s.kind))].sort();
  const shown = cards.filter((c) => kind === "all" || (c.kind === "allocation" && c.source?.kind === kind));
  const totals = boardTotals(data.data.batches);
  const active = cards.filter((c) => c.kind === "allocation" && (c.stage === "production" || c.stage === "qa")).length;
  const flags = cards.reduce((n, c) => n + c.flags.length, 0);
  const spend = [...totals.spend].map(([currency, amount]) => money(amount, currency)).join(" + ") || money(0);
  const [currency, amount] = [...totals.spend][0] ?? ["USD", 0];

  return (
    <>
      <div className="view-head">
        <div>
          <h1>Program board</h1>
          <div className="sub">Every request and allocation, from every source, from intake to delivery.</div>
        </div>
        <div className="filters" role="group" aria-label="Filter by source type">
          {["all", ...kinds].map((k) => (
            <button
              key={k}
              type="button"
              className="chip"
              aria-pressed={kind === k}
              onClick={() => setKind(k)}
              style={{ ["--c" as string]: KIND_COLORS[k] }}
            >
              {k !== "all" && <span className="sw" style={{ background: KIND_COLORS[k] }} />}
              {k === "all" ? "All sources" : kindLabel(k)}
            </button>
          ))}
        </div>
      </div>

      <div className="stats" role="group" aria-label="Board totals">
        <div className="stat">
          <div className="k">Active allocations</div>
          <div className="v">{active}</div>
        </div>
        <div className="stat">
          <div className="k">Spend</div>
          <div className="v">{spend}</div>
        </div>
        <div className="stat">
          <div className="k">Cost per usable unit</div>
          <div className="v">
            {totals.accepted ? money(amount / totals.accepted, currency) : "—"} <small>blended</small>
          </div>
        </div>
        <div className="stat">
          <div className="k">Open flags</div>
          <div className="v">{flags}</div>
        </div>
      </div>

      {cards.length === 0 ? (
        <div className="panel empty">Nothing on the board yet. Create a request to get started.</div>
      ) : (
        <div className="board">
          {STAGES.map((stage) => {
            const list = shown.filter((c) => c.stage === stage.key);
            return (
              <section key={stage.key} className="col" aria-label={stage.label}>
                <div className="col-head" title={stage.hint}>
                  {stage.label} <span>{list.length}</span>
                </div>
                {list.map((card) => (
                  <BoardCard key={card.id} card={card} onOpen={() => setOpen(card)} />
                ))}
              </section>
            );
          })}
        </div>
      )}
      {open && <CardDrawer card={open} onClose={() => setOpen(null)} />}
    </>
  );
}

function SourceChip({ source }: { source?: Schemas["DataSource"] }) {
  if (!source) return <span className="source muted">Unknown source</span>;
  return (
    <span className="source" style={{ ["--c" as string]: KIND_COLORS[source.kind] }}>
      <span className="sw" />
      {source.name}
    </span>
  );
}

function BoardCard({ card, onOpen }: { card: Card; onOpen: () => void }) {
  if (card.kind === "request") {
    const r = card.request;
    return (
      <button type="button" className="card" onClick={onOpen} data-testid="card">
        <div className="card-top">
          <span className="mono muted">{r.id.slice(0, 12)}…</span>
          <span className={`pill ${r.priority === "P0" || r.priority === "P1" ? "bad" : "neutral"}`}>{r.priority}</span>
        </div>
        <div className="card-title">{r.title}</div>
        <div className="card-meta">
          {count(r.quantity)} {r.unit}
          {r.requested_by ? ` · ${r.requested_by}` : ""}
        </div>
        {card.flags.map((f) => (
          <div key={f.text} className={`flag ${f.tone}`}>{f.text}</div>
        ))}
        <div className="card-foot">
          <span>{r.status}</span>
          <span>{r.due_date ? `Due ${day(r.due_date)}` : ""}</span>
        </div>
      </button>
    );
  }
  const a = card.allocation;
  const progress = Math.min(1, a.progress);
  return (
    <button
      type="button"
      className="card"
      onClick={onOpen}
      data-testid="card"
      style={{ ["--c" as string]: card.source ? KIND_COLORS[card.source.kind] : undefined }}
    >
      <div className="card-top">
        <SourceChip source={card.source} />
        <span className="pill neutral">{a.status}</span>
      </div>
      <div className="card-title">{card.request?.title ?? a.request_id}</div>
      <div className="card-meta">
        {count(a.quantity)} {a.unit} at {money(a.quoted_unit_rate, a.currency)}
      </div>
      {a.batch_count > 0 && (
        <>
          <div className="bar" title={`${percent(a.progress)} of ordered units accepted`}>
            <i style={{ width: `${progress * 100}%` }} />
          </div>
          <div className="card-meta num">
            {count(a.accepted_count)} of {count(a.quantity)} accepted · {a.batch_count} deliver{a.batch_count === 1 ? "y" : "ies"}
          </div>
        </>
      )}
      {card.flags.map((f) => (
        <div key={f.text} className={`flag ${f.tone}`}>{f.text}</div>
      ))}
      <div className="card-foot">
        <span>{a.due_date ? `Due ${day(a.due_date)}` : "No due date"}</span>
        <span>{Number(a.spend) > 0 ? money(a.spend, a.currency) : "No spend yet"}</span>
      </div>
    </button>
  );
}

function CardDrawer({ card, onClose }: { card: Card; onClose: () => void }) {
  const title = card.kind === "request" ? card.request.title : card.request?.title ?? card.allocation.request_id;
  return (
    <Drawer label="Details" kicker={card.id} title={title} onClose={onClose}>
      {card.kind === "request" ? <RequestDetail request={card.request} /> : <AllocationDetail card={card} />}
    </Drawer>
  );
}

function RequestDetail({ request: r }: { request: Schemas["Request"] }) {
  return (
    <>
      <dl className="kv">
        <dt>Status</dt><dd>{r.status}</dd>
        <dt>Priority</dt><dd>{r.priority}</dd>
        <dt>Requested by</dt><dd>{r.requested_by || "—"}</dd>
        <dt>Quantity</dt><dd>{count(r.quantity)} {r.unit}</dd>
        <dt>Due</dt><dd>{day(r.due_date)}</dd>
        <dt>Spec</dt><dd>{r.spec_version ? `v${r.spec_version}` : "Not chosen yet"}</dd>
      </dl>
      {r.rationale && <p style={{ margin: 0 }}>{r.rationale}</p>}
      <Link to={`/requests/${r.id}`} className="btn primary" style={{ alignSelf: "flex-start" }}>
        Open the request to split it across sources
      </Link>
    </>
  );
}

function AllocationDetail({ card }: { card: Extract<Card, { kind: "allocation" }> }) {
  const a = card.allocation;
  return (
    <>
      <div>
        <SourceChip source={card.source} />
        {card.source && <span className="muted"> · {kindLabel(card.source.kind)}</span>}
      </div>
      <dl className="kv">
        <dt>Status</dt><dd>{a.status}</dd>
        <dt>Ordered</dt><dd>{count(a.quantity)} {a.unit}</dd>
        <dt>Quoted</dt><dd>{money(a.quoted_unit_rate, a.currency)} each · {money(a.quoted_cost, a.currency)}</dd>
        <dt>Delivered</dt><dd>{count(a.delivered_count)}</dd>
        <dt>Accepted</dt><dd>{count(a.accepted_count)} ({percent(a.progress)})</dd>
        <dt>Spend so far</dt><dd>{money(a.spend, a.currency)}</dd>
        <dt>Due</dt><dd>{day(a.due_date)}</dd>
      </dl>
      {card.flags.map((f) => (
        <div key={f.text} className={`flag ${f.tone}`}>{f.text}</div>
      ))}
      <Link to={`/requests/${a.request_id}`} className="btn" style={{ alignSelf: "flex-start" }}>
        Open the request
      </Link>
      <div>
        <div className="section-label">Deliveries</div>
        {card.batches.length === 0 ? (
          <div className="muted">Nothing delivered yet.</div>
        ) : (
          <div className="stack" style={{ gap: 6 }}>
            {card.batches.map((b) => (
              <Link key={b.id} to={`/batches/${b.id}`} className="rowlink">
                <span>
                  <span className="mono">{b.id.slice(0, 14)}…</span>
                  <span className="muted"> · {count(b.delivered_count)} delivered</span>
                </span>
                <StatusPill status={b.status} />
              </Link>
            ))}
          </div>
        )}
      </div>
    </>
  );
}

export function StatusPill({ status }: { status: string }) {
  const tone =
    { accepted: "good", passed: "good", rejected: "bad", failed: "bad", checking: "accent", received: "neutral" }[status] ??
    "neutral";
  return <span className={`pill ${tone}`}>{status}</span>;
}
