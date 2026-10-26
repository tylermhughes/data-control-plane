import { fireEvent, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "../App";
import { ADMIN, fakeApi, renderApp } from "../test/render";

describe("sign in", () => {
  it("signs in with a valid key and keeps it for this tab only", async () => {
    const calls = fakeApi({
      "GET /v1/me": ADMIN,
      "GET /v1/projects": { data: [], next_cursor: null },
      "GET /v1/reports/portfolio": { project_id: null, since: null, until: null, generated_at: "", by_capability: [], by_source_kind: [] },
    });
    renderApp(<App />, { signedIn: false });
    fireEvent.change(screen.getByLabelText("API key"), { target: { value: " dcp_secret " } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByRole("heading", { name: "Portfolio" })).toBeTruthy();
    expect(sessionStorage.getItem("dcp.apiKey")).toBe("dcp_secret");
    expect(calls[0].headers.Authorization).toBe("Bearer dcp_secret");
  });

  it("shows the API's reason for a bad key", async () => {
    fakeApi({ "GET /v1/me": () => ({ status: 401, json: { title: "Unauthorized", status: 401, detail: "Invalid or revoked API key." } }) });
    renderApp(<App />, { signedIn: false });
    fireEvent.change(screen.getByLabelText("API key"), { target: { value: "dcp_nope" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByRole("alert")).toHaveProperty("textContent", "Invalid or revoked API key.");
    await waitFor(() => expect(sessionStorage.getItem("dcp.apiKey")).toBeNull());
  });
});
