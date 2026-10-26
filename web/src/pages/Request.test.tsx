import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { Route, Routes } from "react-router";
import { describe, expect, it } from "vitest";

import { RequestPage } from "./Request";
import { Requests } from "./Requests";
import { ADMIN, fakeApi, renderApp } from "../test/render";

const page = (data: unknown[]) => ({ data, next_cursor: null });
const REQUEST = {
  id: "req_1", project_id: "prj_1", capability_id: "cap_1", title: "Next round", requested_by: "Priya Nair", priority: "P1",
  rationale: "Recall is weakest on shrink-wrap.", target_metric: "", quantity: 6000, unit: "images", due_date: "2026-12-15",
  spec_version_id: "spv_1", spec_id: "spc_1", spec_version: 1, status: "open",
  allocated: [{ unit: "images", currency: "USD", quantity: 2000, quoted_cost: "3100.00", delivered_count: 500, accepted_count: 480, spend: "775.00" }],
  opened_at: "2026-10-20T00:00:00Z", closed_at: null, cancelled_at: null, created_at: "2026-10-20T00:00:00Z", updated_at: "",
};
const ALLOCATION = {
  id: "alc_1", request_id: "req_1", data_source_id: "src_surge", quantity: 2000, unit: "images", quoted_unit_rate: "1.55",
  currency: "USD", quoted_cost: "3100.00", accepted_count: 480, progress: 0.24, spend: "775.00", status: "planned", due_date: null,
};
const SUGGESTION = (id: string, name: string) => ({
  data_source_id: id, name, kind: "human_vendor", role: "proven", share: 0.5, expected_usable: 2000, order_quantity: 2100,
  expected_cost: "3255.00", currency: "USD", capacity_by_due_date: null, notes: [], evidence: {},
  allocation: { request_id: "req_1", data_source_id: id, quantity: 2100, quoted_unit_rate: "1.55", currency: "USD" },
});
const PLAN = {
  request_id: "req_1", unit: "images", requested: 6000, already_allocated: 2000, remaining: 4000, due_date: null,
  suggestions: [SUGGESTION("src_mercor", "Mercor"), SUGGESTION("src_returns", "Returns photos")],
  excluded: [{ data_source_id: "src_old", name: "Old archive", reason: "Rights expire before the due date." }],
  shortfall: 0, coverage_gaps: [], method: "Shares in proportion to 1 ÷ cost per usable unit.", generated_at: "",
};

function setup(access = "write") {
  return fakeApi({
    "GET /v1/me": { ...ADMIN, access },
    "GET /v1/projects": page([]),
    "GET /v1/requests": page([REQUEST, { ...REQUEST, id: "req_2", title: "Old ask", status: "closed" }]),
    "GET /v1/requests/req_1": REQUEST,
    "GET /v1/capabilities": page([{ id: "cap_1", project_id: "prj_1", name: "Package damage detection", currency: "USD" }]),
    "GET /v1/allocations": page([ALLOCATION]),
    "GET /v1/data-sources": page([
      { id: "src_surge", name: "Surge", kind: "human_vendor", default_unit: "images" },
      { id: "src_mercor", name: "Mercor", kind: "human_vendor", default_unit: "images" },
    ]),
    "GET /v1/requests/req_1/allocation-plan": PLAN,
    "GET /v1/requests/req_1/coverage": { spec_version_id: "spv_1", tolerance: 0.05, accepted_count: 0, batch_ids: [], counts_from: {}, attributes: [], gaps: [] },
    "GET /v1/events": page([{ id: "evt_1", type: "request.opened", created_at: "2026-10-20T00:00:00Z" }]),
    "POST /v1/allocations": (body: unknown) => ({ status: 201, json: { ...ALLOCATION, ...(body as object) } }),
    "POST /v1/allocations/alc_1/activate": { ...ALLOCATION, status: "active" },
    "POST /v1/requests/req_1/close": { ...REQUEST, status: "closed" },
  });
}

const show = (access?: string) => {
  const calls = setup(access);
  renderApp(<Routes><Route path="/requests/:requestId" element={<RequestPage />} /></Routes>, { path: "/requests/req_1" });
  return calls;
};

describe("Requests list", () => {
  it("shows draft and open requests first, others by filter", async () => {
    setup();
    renderApp(<Requests />);
    expect(await screen.findByRole("link", { name: "Next round" })).toBeTruthy();
    expect(screen.queryByText("Old ask")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Closed" }));
    expect(screen.getByText("Old ask")).toBeTruthy();
    expect(screen.queryByText("Next round")).toBeNull();
  });
});

describe("Request page", () => {
  it("shows totals, allocations, the suggested split and history", async () => {
    show();
    const totals = await screen.findByRole("group", { name: "Request totals" });
    expect(within(totals).getByText("6,000")).toBeTruthy();
    expect(within(totals).getByText("$775")).toBeTruthy();
    const allocations = await screen.findByRole("region", { name: "Allocations" });
    expect(await within(allocations).findByText("Surge")).toBeTruthy();
    const plan = screen.getByRole("region", { name: "Suggested split" });
    expect(await within(plan).findByText(/4,000 images still to plan for/)).toBeTruthy();
    expect(within(plan).getByText(/Old archive left out: Rights expire/)).toBeTruthy();
    expect(await screen.findByText("Request opened")).toBeTruthy();
    expect(screen.getByText("Dec 15, 2026", { exact: false })).toBeTruthy();
  });

  it("adds a suggested allocation, starts one, and closes the request", async () => {
    const calls = show();
    fireEvent.click(await screen.findByRole("button", { name: "Add Mercor" }));
    await waitFor(() => expect(calls.some((c) => c.method === "POST" && c.url.pathname === "/v1/allocations")).toBe(true));
    expect(calls.find((c) => c.method === "POST")?.body).toEqual(PLAN.suggestions[0].allocation);

    fireEvent.click(await screen.findByRole("button", { name: "Start" }));
    await waitFor(() => expect(calls.some((c) => c.url.pathname === "/v1/allocations/alc_1/activate")).toBe(true));

    fireEvent.click(screen.getByRole("button", { name: "Close request" }));
    await waitFor(() => expect(calls.some((c) => c.url.pathname === "/v1/requests/req_1/close")).toBe(true));
  });

  it("adds an allocation by hand", async () => {
    const calls = show();
    const form = await screen.findByRole("region", { name: "Add an allocation" });
    fireEvent.change(within(form).getByLabelText("Source"), { target: { value: "src_mercor" } });
    fireEvent.change(within(form).getByLabelText(/Quantity/), { target: { value: "1000" } });
    fireEvent.change(within(form).getByLabelText(/Quoted price per unit/), { target: { value: "1.65" } });
    expect(within(form).getByText("Quoted cost: $1,650")).toBeTruthy();
    fireEvent.click(within(form).getByRole("button", { name: "Add allocation" }));
    await waitFor(() => expect(calls.some((c) => c.method === "POST")).toBe(true));
    expect(calls.find((c) => c.method === "POST")?.body).toEqual({
      request_id: "req_1", data_source_id: "src_mercor", quantity: 1000, quoted_unit_rate: "1.65", currency: "USD", due_date: null, notes: "",
    });
  });

  it("read-only keys see everything but can't change it", async () => {
    show("read");
    await screen.findByRole("region", { name: "Suggested split" });
    expect(await screen.findByText(/Changing a request needs an API key with write access/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Add Mercor" })).toBeNull();
    expect(screen.queryByRole("region", { name: "Add an allocation" })).toBeNull();
  });
});
