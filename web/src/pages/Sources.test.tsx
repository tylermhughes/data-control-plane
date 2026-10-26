import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { Route, Routes } from "react-router";
import { describe, expect, it } from "vitest";

import { SourcePage } from "./Source";
import { Sources } from "./Sources";
import { ADMIN, fakeApi, renderApp } from "../test/render";

const page = (data: unknown[]) => ({ data, next_cursor: null });
const SURGE = {
  id: "src_surge", project_id: "prj_1", name: "Surge", description: "", kind: "human_vendor", default_unit: "images",
  license_type: "vendor_agreement", consent_scope: "Contributor consent on file.", rights_expires_at: "2026-01-01",
  pii_handling: "", notes: "", created_at: "2026-10-01T00:00:00Z", updated_at: "",
};
const RETURNS = { ...SURGE, id: "src_returns", name: "Returns photos", kind: "enterprise_workflow", license_type: "customer_terms", rights_expires_at: null };
const BATCHES = [
  { id: "bat_1", data_source_id: "src_surge", status: "accepted", delivered_count: 4000, accepted_count: 3800, spend: "6200", currency: "USD", received_at: "2026-10-20T00:00:00Z" },
];

function setup(access = "write") {
  return fakeApi({
    "GET /v1/me": { ...ADMIN, access },
    "GET /v1/projects": page([{ id: "prj_1", name: "Fulfillment vision" }]),
    "GET /v1/data-sources": page([SURGE, RETURNS]),
    "GET /v1/data-sources/src_surge": SURGE,
    "GET /v1/allocations": page([{ id: "alc_1", request_id: "req_1", data_source_id: "src_surge", status: "active", quantity: 4000, accepted_count: 3800, unit: "images" }]),
    "GET /v1/batches": page(BATCHES),
    "GET /v1/requests": page([{ id: "req_1", title: "Shrink-wrapped packaging" }]),
    "GET /v1/inbound-webhooks": page([]),
    "GET /v1/connectors": page([]),
    "POST /v1/data-sources": (body: unknown) => ({ status: 201, json: { ...SURGE, id: "src_new", ...(body as object) } }),
    "POST /v1/inbound-webhooks": () => ({
      status: 201,
      json: { id: "ihk_1", data_source_id: "src_surge", url_path: "/v1/inbound/ihk_1", enabled: true, last_received_at: null, secret: "whsec_shown_once" },
    }),
  });
}

describe("Sources", () => {
  it("shows each source's track record and rights warnings", async () => {
    setup();
    renderApp(<Sources />);
    const cards = await screen.findAllByTestId("source-card");
    const surge = cards.find((c) => c.textContent?.includes("Surge"))!;
    expect(within(surge).getByText("$6,200")).toBeTruthy();
    expect(within(surge).getByText("95.0%")).toBeTruthy();
    expect(within(surge).getByText("$1.63")).toBeTruthy();
    expect(within(surge).getByText(/Rights expired/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Enterprise workflows" }));
    expect(screen.getAllByTestId("source-card")).toHaveLength(1);
  });

  it("creates a source", async () => {
    const calls = setup();
    renderApp(<Sources />);
    const open = (await screen.findByRole("button", { name: "New source" })) as HTMLButtonElement;
    await waitFor(() => expect(open.disabled).toBe(false));
    fireEvent.click(open);
    const form = screen.getByRole("dialog", { name: "New source" });
    await within(form).findByRole("option", { name: "Fulfillment vision" });
    fireEvent.change(within(form).getByLabelText("Project"), { target: { value: "prj_1" } });
    fireEvent.change(within(form).getByLabelText("Name"), { target: { value: "Northgate SimLab" } });
    fireEvent.change(within(form).getByLabelText("Type"), { target: { value: "synthetic" } });
    fireEvent.click(within(form).getByRole("button", { name: "Create source" }));
    await waitFor(() => expect(calls.some((c) => c.method === "POST")).toBe(true));
    expect(calls.find((c) => c.method === "POST")?.body).toMatchObject({ project_id: "prj_1", name: "Northgate SimLab", kind: "synthetic", default_unit: "images" });
  });
});

describe("Source page", () => {
  it("shows the work and sets up a delivery webhook, showing its secret once", async () => {
    setup();
    renderApp(<Routes><Route path="/sources/:sourceId" element={<SourcePage />} /></Routes>, { path: "/sources/src_surge" });
    expect(await screen.findByText("Shrink-wrapped packaging")).toBeTruthy();
    expect(screen.getByText("Contributor consent on file.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Add a webhook URL" }));
    expect(await screen.findByText("whsec_shown_once")).toBeTruthy();
  });

  it("read-only keys can't set up intake", async () => {
    setup("read");
    renderApp(<Routes><Route path="/sources/:sourceId" element={<SourcePage />} /></Routes>, { path: "/sources/src_surge" });
    await screen.findByText("Shrink-wrapped packaging");
    expect(screen.queryByRole("button", { name: "Add a webhook URL" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Watch a bucket" })).toBeNull();
  });
});
