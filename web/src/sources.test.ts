import { describe, expect, it } from "vitest";

import type { Schemas } from "./api/client";
import { rightsStatus, sourceStats } from "./sources";

const batch = (status: string, delivered: number, accepted: number | null, spend: string, source = "src_1") =>
  ({ data_source_id: source, status, delivered_count: delivered, accepted_count: accepted, spend, currency: "USD" }) as Schemas["Batch"];

describe("sourceStats", () => {
  it("adds up spend, yield and cost per usable unit from decided deliveries", () => {
    const stats = sourceStats(
      "src_1",
      [{ data_source_id: "src_1", status: "active" }, { data_source_id: "src_1", status: "complete" }] as Schemas["Allocation"][],
      [batch("accepted", 4000, 3800, "6200"), batch("rejected", 1000, 0, "1550"), batch("received", 500, null, "775"), batch("accepted", 10, 10, "9", "src_2")],
    );
    expect(stats.activeAllocations).toBe(1);
    expect(stats.deliveries).toBe(3);
    expect(stats.spend.get("USD")).toBe(8525);
    expect(stats.acceptRate).toBe(0.76);
    expect(stats.costPerUsable?.amount).toBeCloseTo(8525 / 3800);
    expect(stats.waiting).toBe(1);
  });
});

describe("rightsStatus", () => {
  it("warns before usage rights run out", () => {
    expect(rightsStatus(null, "2026-10-24")).toBe("none");
    expect(rightsStatus("2026-10-01", "2026-10-24")).toBe("expired");
    expect(rightsStatus("2026-12-31", "2026-10-24")).toBe("soon");
    expect(rightsStatus("2028-12-31", "2026-10-24")).toBe("ok");
  });
});
