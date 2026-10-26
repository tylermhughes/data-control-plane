import { describe, expect, it } from "vitest";

import type { Schemas } from "./api/client";
import { buildBoard, boardTotals } from "./board";

const req = (id: string, extra: Partial<Schemas["Request"]> = {}) =>
  ({ id, status: "open", spec_version_id: "spv_1", title: id, ...extra }) as Schemas["Request"];
const alloc = (id: string, request_id: string, extra: Partial<Schemas["Allocation"]> = {}) =>
  ({ id, request_id, data_source_id: "src_1", status: "active", quantity: 100, due_date: null, ...extra }) as Schemas["Allocation"];
const batch = (id: string, allocation_id: string, status: string, extra: Partial<Schemas["Batch"]> = {}) =>
  ({ id, allocation_id, status, spend: "100", currency: "USD", accepted_count: null, quality: null, decision_source: null, ...extra }) as Schemas["Batch"];

const stageOf = (cards: ReturnType<typeof buildBoard>, id: string) => cards.find((c) => c.id === id)?.stage;

describe("buildBoard", () => {
  it("puts things in the right column", () => {
    const cards = buildBoard(
      [req("r_new", { spec_version_id: null }), req("r_busy"), req("r_closed", { status: "closed" })],
      [
        alloc("a_planned", "r_busy", { status: "planned" }),
        alloc("a_working", "r_busy"),
        alloc("a_qa", "r_busy"),
        alloc("a_done", "r_busy", { status: "complete" }),
        alloc("a_cancelled", "r_busy", { status: "cancelled" }),
      ],
      [batch("b1", "a_working", "accepted"), batch("b2", "a_qa", "passed")],
      [],
    );
    expect(stageOf(cards, "r_new")).toBe("requests");
    expect(stageOf(cards, "r_busy")).toBeUndefined(); // shown through its allocations
    expect(stageOf(cards, "r_closed")).toBeUndefined();
    expect(stageOf(cards, "a_planned")).toBe("planned");
    expect(stageOf(cards, "a_working")).toBe("production");
    expect(stageOf(cards, "a_qa")).toBe("qa");
    expect(stageOf(cards, "a_done")).toBe("delivered");
    expect(stageOf(cards, "a_cancelled")).toBeUndefined();
    expect(cards.find((c) => c.id === "r_new")?.flags).toEqual([{ tone: "warn", text: "Needs a spec" }]);
  });

  it("flags failed checks, waiting decisions, vendor overrides and overdue work", () => {
    const cards = buildBoard(
      [req("r")],
      [alloc("a", "r", { due_date: "2026-01-01" })],
      [
        batch("b1", "a", "failed"),
        batch("b2", "a", "received"),
        batch("b3", "a", "accepted", { decision_source: "external", quality: { run_id: "q", status: "failed", failed_checks: ["acceptance_rules"], warnings: [], finished_at: null } }),
      ],
      [],
      "2026-10-23",
    );
    expect(cards[0].flags.map((f) => f.text)).toEqual([
      "1 delivery failed checks",
      "1 waiting for a decision",
      "1 accepted by the vendor despite failed checks",
      "Overdue (due 2026-01-01)",
    ]);
  });

  it("totals spend and usable units", () => {
    const totals = boardTotals([
      batch("b1", "a", "accepted", { accepted_count: 90, spend: "150" }),
      batch("b2", "a", "rejected", { accepted_count: 0, spend: "50" }),
    ]);
    expect(totals.spend.get("USD")).toBe(200);
    expect(totals.accepted).toBe(90);
  });
});
