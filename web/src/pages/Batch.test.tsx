import { fireEvent, screen, within } from "@testing-library/react";
import { Route, Routes } from "react-router";
import { describe, expect, it } from "vitest";

import { BatchPage } from "./Batch";
import { ADMIN, fakeApi, renderApp } from "../test/render";

const BATCH = {
  id: "bat_1", request_id: "req_1", allocation_id: "alc_1", data_source_id: "src_1", status: "failed",
  received_at: "2026-10-20T10:00:00Z", delivered_count: 4000, accepted_count: null, spend: "6000.00", currency: "USD",
  spend_is_estimate: false, artifacts: [{ uri: "s3://intake/b1.jsonl", format: "jsonl", record_count: 4000 }],
  quality: { run_id: "qrn_1", status: "failed", failed_checks: ["acceptance_rules"], warnings: [], finished_at: "" },
  override_reason: null, decision_source: null, decided_by: null, decided_at: null, rejection_reason: null, external_url: null,
};
const RUN = {
  id: "qrn_1", status: "failed", checks: [
    { name: "format", outcome: "passed", summary: "All 4,000 records parse.", details: {} },
    { name: "acceptance_rules", outcome: "failed", summary: "duplicate_rate 3.1% is above 2%.", details: {} },
  ],
};
const COVERAGE = {
  spec_version_id: "spv_1", tolerance: 0.05, accepted_count: 0, batch_ids: ["bat_1"], counts_from: { bat_1: "files" },
  gaps: ["package_type=shrink_wrapped: 20% vs 35% target"],
  attributes: [{ attribute: "package_type", counted: 4000, counted_share_of_accepted: null, values: [
    { value: "shrink_wrapped", count: 800, actual_share: 0.2, target_share: 0.35, gap: -0.15, status: "below" },
  ] }],
};

function setup(access = "write") {
  return fakeApi({
    "GET /v1/me": { ...ADMIN, access },
    "GET /v1/projects": { data: [], next_cursor: null },
    "GET /v1/batches/bat_1": BATCH,
    "GET /v1/allocations/alc_1": { id: "alc_1", unit: "images" },
    "GET /v1/data-sources/src_1": { id: "src_1", name: "Surge AI", kind: "human_vendor" },
    "GET /v1/requests/req_1": { id: "req_1", title: "Damaged package photos" },
    "GET /v1/quality-runs/qrn_1": RUN,
    "GET /v1/batches/bat_1/coverage": COVERAGE,
    "GET /v1/events": { data: [{ id: "evt_1", type: "batch.received", created_at: "2026-10-20T10:00:00Z" }], next_cursor: null },
    "POST /v1/batches/bat_1/accept": (body: unknown) => ({ json: { ...BATCH, status: "accepted", accepted_count: (body as { accepted_count: number }).accepted_count, override_reason: "Approved by Dana", decided_by: "Dana", decided_at: "2026-10-21T00:00:00Z" } }),
  });
}

const show = (access?: string) => {
  const calls = setup(access);
  renderApp(<Routes><Route path="/batches/:batchId" element={<BatchPage />} /></Routes>, { path: "/batches/bat_1" });
  return calls;
};

describe("Batch page", () => {
  it("shows checks, coverage and history", async () => {
    show();
    expect(await screen.findByText("Damaged package photos")).toBeTruthy();
    const checks = await screen.findByRole("region", { name: "Quality checks" });
    expect(await within(checks).findByText("duplicate_rate 3.1% is above 2%.")).toBeTruthy();
    const coverage = screen.getByRole("region", { name: "Coverage" });
    expect(await within(coverage).findByText(/shrink_wrapped: 20% vs 35% target/)).toBeTruthy();
    expect(await screen.findByText("Delivery registered")).toBeTruthy();
  });

  it("needs a reason to accept a failed delivery", async () => {
    const calls = show();
    const submit = (await screen.findByRole("button", { name: "Accept delivery" })) as HTMLButtonElement;
    const form = screen.getByRole("region", { name: "Decision" });
    fireEvent.change(within(form).getByLabelText(/Images to keep/), { target: { value: "3800" } });
    expect(submit.disabled).toBe(true);
    fireEvent.change(within(form).getByLabelText("Why accept it anyway?"), { target: { value: "Approved by Dana" } });
    fireEvent.change(within(form).getByLabelText("Decided by"), { target: { value: "Dana" } });
    fireEvent.click(submit);
    expect(await screen.findByText(/Accepted despite failed checks: Approved by Dana/)).toBeTruthy();
    const post = calls.find((c) => c.method === "POST");
    expect(post?.body).toEqual({ accepted_count: 3800, decided_by: "Dana", override_reason: "Approved by Dana" });
  });

  it("read-only keys can't decide", async () => {
    show("read");
    expect(await screen.findByText(/needs an API key with write access/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Accept delivery" })).toBeNull();
  });
});
