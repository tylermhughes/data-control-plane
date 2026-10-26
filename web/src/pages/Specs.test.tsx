import { fireEvent, screen, within } from "@testing-library/react";
import { Route, Routes } from "react-router";
import { describe, expect, it } from "vitest";

import { Specs, textToAttributes } from "./Specs";
import { ADMIN, fakeApi, renderApp } from "../test/render";

const SPEC = { id: "spc_1", project_id: "prj_1", name: "Package damage", description: "", latest_version: 2, latest_approved_version: 1, draft_version: 2 };
const V1 = {
  id: "spv_1", spec_id: "spc_1", version: 1, status: "approved", approved_by: "Priya Nair", approved_at: "2026-10-01T00:00:00Z",
  created_at: "2026-10-01T00:00:00Z", updated_at: "2026-10-01T00:00:00Z", change_note: "First version.",
  guidelines: "Box every damaged area.\nOne box per area.",
  attributes: [{ name: "package_type", values: ["box", "mailer", "shrink_wrapped"], description: "" }],
  coverage_targets: { package_type: { box: 0.3, mailer: 0.35, shrink_wrapped: 0.35 } },
  coverage_tolerance: 0.05, acceptance_rules: [{ metric: "agreement", operator: ">=", threshold: 0.85 }], record_schema: null,
};
const V2 = { ...V1, id: "spv_2", version: 2, status: "draft", approved_by: null, approved_at: null, change_note: "More shrink-wrap.",
  coverage_targets: { package_type: { box: 0.28, mailer: 0.32, shrink_wrapped: 0.4 } } };

function setup(access = "write") {
  return fakeApi({
    "GET /v1/me": { ...ADMIN, access },
    "GET /v1/projects": { data: [], next_cursor: null },
    "GET /v1/specs": { data: [SPEC], next_cursor: null },
    "GET /v1/specs/spc_1/versions": { data: [V1, V2], next_cursor: null },
    "GET /v1/requests": { data: [{ id: "req_1", title: "Shrink-wrapped packaging", spec_id: "spc_1", spec_version: 1, status: "open" }], next_cursor: null },
    "POST /v1/specs/spc_1/versions/2/approve": (body: unknown) => ({ json: { ...V2, status: "approved", ...(body as object) } }),
    "PATCH /v1/specs/spc_1/versions/2": (body: unknown) => ({ json: { ...V2, ...(body as object) } }),
  });
}

const show = (access?: string) => {
  const calls = setup(access);
  renderApp(<Routes><Route path="/specs/:specId" element={<Specs />} /></Routes>, { path: "/specs/spc_1" });
  return calls;
};

describe("Specs", () => {
  it("shows the latest version with its changes since the one before", async () => {
    show();
    const changes = await screen.findByRole("region", { name: "Changes" });
    expect(within(changes).getByText("Target package_type=shrink_wrapped: 40%")).toBeTruthy();
    expect(within(changes).getByText("Target package_type=shrink_wrapped: 35%")).toBeTruthy();
    expect(screen.getByText("Box every damaged area.")).toBeTruthy();
    expect(within(screen.getByRole("region", { name: "Used by" })).getByText("Shrink-wrapped packaging")).toBeTruthy();
    fireEvent.click(screen.getByLabelText(/Show changes since v1/));
    expect(screen.queryByRole("region", { name: "Changes" })).toBeNull();
  });

  it("approves a draft with the approver's name", async () => {
    const calls = show();
    const approve = (await screen.findByRole("button", { name: "Approve v2" })) as HTMLButtonElement;
    expect(approve.disabled).toBe(true);
    fireEvent.change(screen.getByLabelText("Approved by"), { target: { value: "Priya Nair" } });
    fireEvent.click(approve);
    await screen.findByText("Approve v2"); // still there until the list refreshes
    expect(calls.find((c) => c.method === "POST")?.body).toEqual({ approved_by: "Priya Nair" });
  });

  it("edits a draft's coverage targets", async () => {
    const calls = show();
    fireEvent.click(await screen.findByRole("button", { name: "Edit draft" }));
    const editor = screen.getByRole("dialog", { name: "Edit draft" });
    fireEvent.change(within(editor).getByLabelText("shrink wrapped"), { target: { value: "45" } });
    fireEvent.change(within(editor).getByLabelText("box"), { target: { value: "23" } });
    fireEvent.click(within(editor).getByRole("button", { name: "Save draft" }));
    await screen.findByRole("button", { name: "Edit draft" });
    const patch = calls.find((c) => c.method === "PATCH")?.body as { coverage_targets: unknown; acceptance_rules: unknown };
    expect(patch.coverage_targets).toEqual({ package_type: { box: 0.23, mailer: 0.32, shrink_wrapped: 0.45 } });
    expect(patch.acceptance_rules).toEqual([{ metric: "agreement", operator: ">=", threshold: 0.85 }]);
  });

  it("read-only keys can't change specs", async () => {
    show("read");
    expect(await screen.findByText(/Editing and approving need an API key with write access/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Edit draft" })).toBeNull();
  });
});

describe("textToAttributes", () => {
  it("reads one attribute per line", () => {
    expect(textToAttributes("package_type: box, mailer\n\nzone: induct")).toEqual([
      { name: "package_type", values: ["box", "mailer"], description: "" },
      { name: "zone", values: ["induct"], description: "" },
    ]);
  });
});
