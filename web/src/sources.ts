// A source's track record, worked out from its allocations and deliveries.
import type { Schemas } from "./api/client";

export type SourceStats = {
  activeAllocations: number;
  deliveries: number;
  spend: Map<string, number>; // per currency
  delivered: number; // in decided deliveries
  accepted: number;
  acceptRate: number | null; // accepted ÷ delivered, decided deliveries only
  costPerUsable: { amount: number; currency: string } | null; // single currency only
  waiting: number; // deliveries still to decide
};

export function sourceStats(
  sourceId: string,
  allocations: Schemas["Allocation"][],
  batches: Schemas["Batch"][],
): SourceStats {
  const mine = batches.filter((b) => b.data_source_id === sourceId);
  const spend = new Map<string, number>();
  let delivered = 0;
  let accepted = 0;
  let waiting = 0;
  for (const b of mine) {
    spend.set(b.currency, (spend.get(b.currency) ?? 0) + Number(b.spend));
    if (b.status === "accepted" || b.status === "rejected") {
      delivered += b.delivered_count;
      accepted += b.accepted_count ?? 0;
    } else {
      waiting += 1;
    }
  }
  const currencies = [...spend.keys()];
  return {
    activeAllocations: allocations.filter((a) => a.data_source_id === sourceId && a.status === "active").length,
    deliveries: mine.length,
    spend,
    delivered,
    accepted,
    acceptRate: delivered ? accepted / delivered : null,
    costPerUsable: accepted && currencies.length === 1 ? { amount: spend.get(currencies[0])! / accepted, currency: currencies[0] } : null,
    waiting,
  };
}

/** "expired", "soon" (within 90 days), "ok", or "none" (no end date). */
export function rightsStatus(expires: string | null, today: string): "expired" | "soon" | "ok" | "none" {
  if (!expires) return "none";
  if (expires < today) return "expired";
  const soon = new Date(today);
  soon.setDate(soon.getDate() + 90);
  return expires <= soon.toISOString().slice(0, 10) ? "soon" : "ok";
}

export const LICENSE_LABELS: Record<string, string> = {
  owned: "Owned by us",
  vendor_agreement: "Vendor agreement",
  licensed: "Licensed",
  customer_terms: "Customer terms",
  employee_notice: "Employee notice",
  open_license: "Open license",
  other: "Other",
};
