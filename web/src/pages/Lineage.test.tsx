import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { Route, Routes } from "react-router";
import { describe, expect, it } from "vitest";

import { Lineage, improvement } from "./Lineage";
import { ADMIN, fakeApi, renderApp } from "../test/render";

const page = (data: unknown[]) => ({ data, next_cursor: null });
const batch = (id: string, source: string, accepted: number, spend: string) => ({
  id, request_id: "req_1", data_source_id: source, spec_version_id: "spv_1", status: "accepted", delivered_count: 4000,
  accepted_count: accepted, spend, currency: "USD", received_at: "2026-10-20T00:00:00Z",
});
const V1 = { id: "dsv_1", dataset_id: "dst_1", version: 1, baseline_version_id: null, batch_ids: ["bat_1"], totals: [], new_vs_baseline: [], notes: "", created_at: "2026-10-21T00:00:00Z" };
const V2 = { ...V1, id: "dsv_2", version: 2, baseline_version_id: "dsv_1", batch_ids: ["bat_1", "bat_2"], new_vs_baseline: [{ unit: "images", currency: "USD", batch_count: 1, accepted_count: 3700, spend: "6600.00" }] };
const evr = (id: string, version: string, value: number) => ({ id, dataset_version_id: version, metric: "recall@0.5", value, higher_is_better: true, run_name: "", external_run_url: null, recorded_at: "2026-10-22T00:00:00Z" });

function setup() {
  return fakeApi({
    "GET /v1/me": ADMIN,
    "GET /v1/projects": page([]),
    "GET /v1/datasets": page([{ id: "dst_1", project_id: "prj_1", capability_id: "cap_1", name: "damage-det", description: "", latest_version: 2 }]),
    "GET /v1/dataset-versions": page([V1, V2]),
    "GET /v1/eval-results": page([evr("evr_1", "dsv_1", 0.812), evr("evr_2", "dsv_2", 0.857)]),
    "GET /v1/batches": page([batch("bat_1", "src_surge", 3800, "6200"), batch("bat_2", "src_mercor", 3700, "6600"), batch("bat_3", "src_surge", 2900, "4650")]),
    "GET /v1/requests": page([{ id: "req_1", title: "Shrink-wrapped packaging", capability_id: "cap_1", spec_id: "spc_1", spec_version_id: "spv_1", spec_version: 1 }]),
    "GET /v1/data-sources": page([{ id: "src_surge", name: "Surge", kind: "human_vendor" }, { id: "src_mercor", name: "Mercor", kind: "human_vendor" }]),
    "GET /v1/specs": page([{ id: "spc_1", name: "Package damage" }]),
    "GET /v1/capabilities": page([{ id: "cap_1", name: "Package damage detection", eval_metric: "recall@0.5", currency: "USD" }]),
    "POST /v1/datasets/dst_1/versions": () => ({ status: 201, json: { ...V2, id: "dsv_3", version: 3 } }),
    "POST /v1/eval-results": () => ({ status: 201, json: evr("evr_3", "dsv_2", 0.86) }),
  });
}

const show = () => {
  const calls = setup();
  renderApp(<Routes><Route path="/lineage/:datasetId" element={<Lineage />} /></Routes>, { path: "/lineage/dst_1" });
  return calls;
};

describe("Lineage", () => {
  it("traces the latest version from request to eval", async () => {
    show();
    const chain = await screen.findByRole("region", { name: "Lineage" });
    expect(within(chain).getByText("Shrink-wrapped packaging")).toBeTruthy();
    expect(within(chain).getByText("Package damage v1")).toBeTruthy();
    expect(within(chain).getByText("7,500 of 8,000")).toBeTruthy();
    expect(within(chain).getByText("0.812 → 0.857")).toBeTruthy();
    const impact = screen.getByRole("region", { name: "Eval impact" });
    expect(within(impact).getByText("+0.045")).toBeTruthy();
    const spend = screen.getByRole("region", { name: "Spend and yield" });
    expect(within(spend).getByText("new in v2")).toBeTruthy();
    expect(within(spend).getByText("$12,800")).toBeTruthy();
  });

  it("freezes a new version from accepted deliveries not in it yet", async () => {
    const calls = show();
    fireEvent.click(await screen.findByRole("button", { name: "New version" }));
    const drawer = screen.getByRole("dialog", { name: "New dataset version" });
    fireEvent.click(within(drawer).getByRole("checkbox"));
    fireEvent.click(within(drawer).getByRole("button", { name: "Freeze with 1 new delivery" }));
    await waitFor(() => expect(calls.some((c) => c.method === "POST")).toBe(true));
    expect(calls.find((c) => c.method === "POST")?.body).toEqual({ batch_ids: ["bat_3"], notes: "" });
  });

  it("records an eval result", async () => {
    const calls = show();
    const form = await screen.findByRole("region", { name: "Record an eval result" });
    fireEvent.change(within(form).getByLabelText("Value"), { target: { value: "0.86" } });
    fireEvent.click(within(form).getByRole("button", { name: "Record result" }));
    await waitFor(() => expect(calls.some((c) => c.method === "POST")).toBe(true));
    expect(calls.find((c) => c.method === "POST")?.body).toMatchObject({ dataset_version_id: "dsv_2", value: 0.86 });
  });
});

describe("improvement", () => {
  it("is positive when a lower-is-better metric goes down", () => {
    expect(improvement(4.8, 4.1, false)).toBeCloseTo(0.7);
    expect(improvement(0.812, 0.857, true)).toBeCloseTo(0.045);
  });
});
