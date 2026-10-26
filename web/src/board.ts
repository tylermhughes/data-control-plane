// The Program board's rules: which column each request or allocation goes in, and its flags.
import type { Schemas } from "./api/client";
import { today as todayLocal } from "./format";

export type Stage = "requests" | "planned" | "production" | "qa" | "delivered";

export const STAGES: { key: Stage; label: string; hint: string }[] = [
  { key: "requests", label: "Requests", hint: "No work allocated yet" },
  { key: "planned", label: "Planned", hint: "Agreed, not started" },
  { key: "production", label: "In production", hint: "Work under way" },
  { key: "qa", label: "In QA", hint: "Deliveries to check or decide" },
  { key: "delivered", label: "Delivered", hint: "Completed" },
];

export const UNDECIDED = new Set(["received", "checking", "passed", "failed"]);

export type Flag = { tone: "bad" | "warn"; text: string };

export type Card =
  | { kind: "request"; id: string; stage: Stage; request: Schemas["Request"]; flags: Flag[] }
  | {
      kind: "allocation";
      id: string;
      stage: Stage;
      allocation: Schemas["Allocation"];
      request?: Schemas["Request"];
      source?: Schemas["DataSource"];
      batches: Schemas["Batch"][];
      flags: Flag[];
    };

export function allocationFlags(
  allocation: Schemas["Allocation"],
  batches: Schemas["Batch"][],
  today: string,
): Flag[] {
  const flags: Flag[] = [];
  const failed = batches.filter((b) => b.status === "failed").length;
  if (failed) flags.push({ tone: "bad", text: `${failed} ${failed === 1 ? "delivery" : "deliveries"} failed checks` });
  const waiting = batches.filter((b) => b.status === "received" || b.status === "passed").length;
  if (waiting) flags.push({ tone: "warn", text: `${waiting} waiting for a decision` });
  const flagged = batches.filter(
    (b) => b.status === "accepted" && b.decision_source === "external" && b.quality?.failed_checks.length,
  ).length;
  if (flagged) flags.push({ tone: "warn", text: `${flagged} accepted by the vendor despite failed checks` });
  if (allocation.due_date && allocation.due_date < today && allocation.status !== "complete") {
    flags.push({ tone: "bad", text: `Overdue (due ${allocation.due_date})` });
  }
  return flags;
}

export function buildBoard(
  requests: Schemas["Request"][],
  allocations: Schemas["Allocation"][],
  batches: Schemas["Batch"][],
  sources: Schemas["DataSource"][],
  today = todayLocal(),
): Card[] {
  const requestById = new Map(requests.map((r) => [r.id, r]));
  const sourceById = new Map(sources.map((s) => [s.id, s]));
  const batchesByAllocation = new Map<string, Schemas["Batch"][]>();
  for (const b of batches) {
    batchesByAllocation.set(b.allocation_id, [...(batchesByAllocation.get(b.allocation_id) ?? []), b]);
  }
  const live = allocations.filter((a) => a.status !== "cancelled");
  const allocated = new Set(live.map((a) => a.request_id));

  const cards: Card[] = [];
  for (const r of requests) {
    if ((r.status === "draft" || r.status === "open") && !allocated.has(r.id)) {
      const flags: Flag[] = [];
      if (!r.spec_version_id) flags.push({ tone: "warn", text: "Needs a spec" });
      cards.push({ kind: "request", id: r.id, stage: "requests", request: r, flags });
    }
  }
  for (const a of live) {
    const own = batchesByAllocation.get(a.id) ?? [];
    let stage: Stage = "production";
    if (a.status === "planned") stage = "planned";
    else if (a.status === "complete") stage = "delivered";
    else if (own.some((b) => UNDECIDED.has(b.status))) stage = "qa";
    cards.push({
      kind: "allocation",
      id: a.id,
      stage,
      allocation: a,
      request: requestById.get(a.request_id),
      source: sourceById.get(a.data_source_id),
      batches: own,
      flags: allocationFlags(a, own, today),
    });
  }
  return cards;
}

/** Spend and usable units across batches, per currency (for the stats strip). */
export function boardTotals(batches: Schemas["Batch"][]) {
  const spend = new Map<string, number>();
  let accepted = 0;
  for (const b of batches) {
    spend.set(b.currency, (spend.get(b.currency) ?? 0) + Number(b.spend));
    if (b.status === "accepted") accepted += b.accepted_count ?? 0;
  }
  return { spend, accepted };
}

export const KIND_COLORS: Record<string, string> = {
  human_vendor: "var(--s-human)",
  expert_network: "var(--s-expert)",
  synthetic: "var(--s-syn)",
  rl_environment: "var(--s-env)",
  enterprise_workflow: "var(--s-ent)",
  beta_users: "var(--s-beta)",
  licensed_dataset: "var(--s-lic)",
};
