import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { Route, Routes } from "react-router";
import { describe, expect, it } from "vitest";

import { Settings } from "./Settings";
import { ADMIN, fakeApi, renderApp } from "../test/render";

const page = (data: unknown[]) => ({ data, next_cursor: null });
const PROJECT = { id: "prj_1", name: "Fulfillment vision", description: "", created_at: "2026-10-01T00:00:00Z", updated_at: "" };

function setup(me: object = ADMIN) {
  return fakeApi({
    "GET /v1/me": me,
    "GET /v1/projects": page([PROJECT]),
    "GET /v1/capabilities": page([]),
    "GET /v1/api-keys": page([ADMIN]),
    "GET /v1/webhook-endpoints": page([]),
    "POST /v1/capabilities": (body: unknown) => ({ status: 201, json: { id: "cap_1", ...(body as object) } }),
    "POST /v1/api-keys": (body: unknown) => ({ status: 201, json: { ...ADMIN, id: "key_2", ...(body as object), secret: "dcp_new_secret_once" } }),
  });
}

const show = (tab: string, me?: object) => {
  const calls = setup(me);
  renderApp(
    <Routes>
      <Route path="/settings" element={<Settings />} />
      <Route path="/settings/:tab" element={<Settings />} />
    </Routes>,
    { path: `/settings/${tab}` },
  );
  return calls;
};

describe("Settings", () => {
  it("creates a capability", async () => {
    const calls = show("capabilities");
    const open = (await screen.findByRole("button", { name: "New capability" })) as HTMLButtonElement;
    await waitFor(() => expect(open.disabled).toBe(false));
    fireEvent.click(open);
    const form = screen.getByRole("dialog", { name: "New capability" });
    await within(form).findByRole("option", { name: "Fulfillment vision" });
    fireEvent.change(within(form).getByLabelText("Project"), { target: { value: "prj_1" } });
    fireEvent.change(within(form).getByLabelText("Name"), { target: { value: "Label legibility" } });
    fireEvent.change(within(form).getByLabelText("Eval metric"), { target: { value: "read error rate" } });
    fireEvent.change(within(form).getByLabelText("Better is"), { target: { value: "false" } });
    fireEvent.change(within(form).getByLabelText("Value of one point"), { target: { value: "41000" } });
    fireEvent.click(within(form).getByRole("button", { name: "Create capability" }));
    await waitFor(() => expect(calls.some((c) => c.method === "POST")).toBe(true));
    expect(calls.find((c) => c.method === "POST")?.body).toEqual({
      project_id: "prj_1", name: "Label legibility", description: "", eval_metric: "read error rate", higher_is_better: false,
      value_per_point: "41000", currency: "USD", point_size: 1, flattening_threshold: 0.5,
    });
  });

  it("creates an API key and shows its secret once", async () => {
    show("keys");
    const panel = await screen.findByRole("region", { name: "API keys" });
    await within(panel).findByRole("option", { name: "Fulfillment vision" }); // projects load after the key
    fireEvent.change(within(panel).getByLabelText("Name"), { target: { value: "Dana's dashboard" } });
    fireEvent.change(within(panel).getByLabelText("Project"), { target: { value: "prj_1" } });
    fireEvent.click(within(panel).getByRole("button", { name: "Create key" }));
    expect(await screen.findByText("dcp_new_secret_once")).toBeTruthy();
  });

  it("project keys don't see projects or API keys", async () => {
    show("keys", { ...ADMIN, role: "project", project_id: "prj_1" });
    expect(await screen.findByRole("region", { name: "Capabilities" })).toBeTruthy();
    expect(screen.queryByRole("link", { name: "API keys" })).toBeNull();
    expect(screen.queryByRole("link", { name: "Projects" })).toBeNull();
  });
});
