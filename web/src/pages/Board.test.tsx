import { fireEvent, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Board } from "./Board";
import { ADMIN, fakeApi, renderApp } from "../test/render";

const page = (data: unknown[]) => ({ data, next_cursor: null });
const REQUESTS = [
  { id: "req_new", title: "Night-shift dock photos", status: "open", priority: "P1", quantity: 2000, unit: "images", requested_by: "Priya", due_date: null, spec_version_id: null, spec_version: null, rationale: "" },
  { id: "req_dmg", title: "Damaged package photos", status: "open", priority: "P0", quantity: 12000, unit: "images", requested_by: "", due_date: null, spec_version_id: "spv_1", spec_version: 1, rationale: "" },
];
const ALLOCATIONS = [
  { id: "alc_vendor", request_id: "req_dmg", data_source_id: "src_v", status: "active", quantity: 8000, unit: "images", quoted_unit_rate: "1.50", quoted_cost: "12000.00", currency: "USD", due_date: null, delivered_count: 4000, accepted_count: 3600, progress: 0.45, spend: "6000.00", batch_count: 1 },
  { id: "alc_ent", request_id: "req_dmg", data_source_id: "src_e", status: "active", quantity: 4000, unit: "images", quoted_unit_rate: "0.40", quoted_cost: "1600.00", currency: "USD", due_date: null, delivered_count: 0, accepted_count: 0, progress: 0, spend: "0", batch_count: 0 },
];
const SOURCES = [
  { id: "src_v", name: "Surge AI", kind: "human_vendor" },
  { id: "src_e", name: "Warehouse flags", kind: "enterprise_workflow" },
];
const BATCHES = [
  { id: "bat_waiting_000001", allocation_id: "alc_vendor", status: "failed", spend: "6000.00", currency: "USD", delivered_count: 4000, accepted_count: null, quality: null, decision_source: null },
];

function setup() {
  return fakeApi({
    "GET /v1/me": ADMIN,
    "GET /v1/projects": page([]),
    "GET /v1/requests": page(REQUESTS),
    "GET /v1/allocations": page(ALLOCATIONS),
    "GET /v1/batches": page(BATCHES),
    "GET /v1/data-sources": page(SOURCES),
  });
}

describe("Program board", () => {
  it("groups work by stage, with flags and totals", async () => {
    setup();
    renderApp(<Board />);
    const requests = await screen.findByRole("region", { name: "Requests" });
    expect(within(requests).getByText("Night-shift dock photos")).toBeTruthy();
    expect(within(requests).getByText("Needs a spec")).toBeTruthy();
    const qa = screen.getByRole("region", { name: "In QA" });
    expect(within(qa).getByText("Surge AI")).toBeTruthy();
    expect(within(qa).getByText("1 delivery failed checks")).toBeTruthy();
    expect(within(screen.getByRole("region", { name: "In production" })).getByText("Warehouse flags")).toBeTruthy();
    const totals = screen.getByRole("group", { name: "Board totals" });
    expect(within(totals).getByText("$6,000")).toBeTruthy();
    expect(within(totals).getByText("Open flags").nextElementSibling?.textContent).toBe("2");
    expect(within(totals).getByText("Active allocations").nextElementSibling?.textContent).toBe("2");
  });

  it("filters by source type and opens a card's details", async () => {
    setup();
    renderApp(<Board />);
    await screen.findByRole("region", { name: "In QA" });
    fireEvent.click(screen.getByRole("button", { name: "Enterprise workflows" }));
    expect(screen.queryByText("Surge AI")).toBeNull();
    expect(screen.getByText("Warehouse flags")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "All sources" }));
    fireEvent.click(within(screen.getByRole("region", { name: "In QA" })).getByTestId("card"));
    const drawer = screen.getByRole("dialog", { name: "Details" });
    const link = within(drawer).getByRole("link", { name: /bat_waiting/ });
    expect(link.getAttribute("href")).toBe("/batches/bat_waiting_000001");
    fireEvent.click(within(drawer).getByRole("button", { name: "Close" }));
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});
