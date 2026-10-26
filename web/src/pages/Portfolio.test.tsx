import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Portfolio } from "./Portfolio";
import { ADMIN, fakeApi, renderApp } from "../test/render";

const CAP = {
  capability_id: "cap_1", name: "Package damage detection", eval_metric: "recall@0.5", point_size: 0.01,
  value_per_point: "25000.00", currency: "USD", value: "112500.00", roi: 15.62,
  spend: [{ currency: "USD", amount: "13400.00" }], usable_units: [{ unit: "images", count: 10100 }],
  cost_per_usable_unit: [{ unit: "images", currency: "USD", amount: "1.3267" }], eval_change_points: 4.5,
  scored_versions: 1, spend_on_scored_versions: [{ currency: "USD", amount: "7200.00" }], points_per_10k: 6.25,
  sources: { dataset_version_ids: ["dsv_2"], eval_result_ids: ["evr_1", "evr_2"], batch_count: 3 }, notes: [],
};
const KIND = { ...CAP, kind: "enterprise_workflow", is_estimate: true, attribution_method: "accepted_units_share", eval_change_points: 1.8571, points_per_10k: 30.95 };
const DIAGNOSIS = {
  capability_id: "cap_1", eval_metric: "recall@0.5", flattening_threshold: 0.5, trend: "flattening", latest_vs_earlier: 0.14,
  versions: [{ dataset_version_id: "dsv_3", dataset_id: "dst_1", version: 3, created_at: "", eval_value: 0.861, baseline_eval_value: 0.857, points: 0.4, spend: [], points_per_10k: 0.86 }],
  checks: [], recommendation: "refine_spec", summary: "Returns are flattening. The data mix is off: package_type=shrink_wrapped: 27% vs 35% target.",
  coverage: null, generated_at: "",
  suggested_spec_change: { spec_id: "spc_1", from_spec_version: 1, change_note: "", coverage_targets: { package_type: { box: 0.28, mailer: 0.32, shrink_wrapped: 0.4 } } },
};

function setup(access = "write") {
  return fakeApi({
    "GET /v1/me": { ...ADMIN, access },
    "GET /v1/projects": { data: [], next_cursor: null },
    "GET /v1/reports/portfolio": { project_id: null, since: null, until: null, generated_at: "", by_capability: [CAP], by_source_kind: [KIND] },
    "GET /v1/capabilities/cap_1/diagnosis": DIAGNOSIS,
    "POST /v1/capabilities/cap_1/diagnosis/draft-spec": () => ({ status: 201, json: { version: 2 } }),
  });
}

describe("Portfolio", () => {
  it("shows the north-star numbers", async () => {
    setup();
    renderApp(<Portfolio />);
    const totals = await screen.findByRole("group", { name: "Totals" });
    expect(within(totals).getByText("$13,400")).toBeTruthy();
    expect(within(totals).getByText("10,100 images")).toBeTruthy();
    expect(within(totals).getByText("$112,500")).toBeTruthy();
    expect(within(totals).getByText("15.6×")).toBeTruthy();
    expect(screen.getByText("+4.50 pts")).toBeTruthy();
    expect(screen.getByText("6.25")).toBeTruthy();
    expect(screen.getByText("Enterprise workflows")).toBeTruthy();
    expect(screen.getByText("Eval change is an estimate")).toBeTruthy();
  });

  it("shows the diagnosis and drafts the refined spec", async () => {
    const calls = setup();
    renderApp(<Portfolio />);
    const card = await screen.findByTestId("diagnosis");
    expect(within(card).getByText("Refine the spec")).toBeTruthy();
    expect(within(card).getByText(/shrink_wrapped 40%/)).toBeTruthy();
    fireEvent.click(within(card).getByRole("button", { name: "Draft the refined spec" }));
    expect(await within(card).findByText(/Drafted spec version 2/)).toBeTruthy();
    expect(calls.some((c) => c.method === "POST" && c.url.pathname.endsWith("/draft-spec"))).toBe(true);
  });

  it("read-only keys can't draft", async () => {
    setup("read");
    renderApp(<Portfolio />);
    const card = await screen.findByTestId("diagnosis");
    const button = await within(card).findByRole("button", { name: "Draft the refined spec" });
    await waitFor(() => expect(button.hasAttribute("disabled")).toBe(true));
  });
});
