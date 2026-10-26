// Test helpers: render a screen with the real providers and a fake API behind fetch.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router";
import { vi } from "vitest";

import { SessionProvider } from "../session";
import { TutorialProvider } from "../tutorial/engine";
import type { Step } from "../tutorial/engine";
import { STEPS } from "../tutorial/steps";

export type Route = (body: unknown, url: URL) => { status?: number; json?: unknown };

/** Fake the API: keys are "METHOD /path" (path without query string). */
export function fakeApi(routes: Record<string, Route | unknown>) {
  const calls: { method: string; url: URL; body: unknown; headers: Record<string, string> }[] = [];
  const fetchMock = vi.fn(async (input: URL | string, init: RequestInit = {}) => {
    const url = new URL(String(input));
    const method = init.method ?? "GET";
    const body = init.body ? JSON.parse(String(init.body)) : undefined;
    calls.push({ method, url, body, headers: (init.headers ?? {}) as Record<string, string> });
    const route = routes[`${method} ${url.pathname}`];
    if (route === undefined) {
      return new Response(JSON.stringify({ title: "Not found", status: 404, detail: `No fake for ${method} ${url.pathname}` }), { status: 404 });
    }
    const result = typeof route === "function" ? (route as Route)(body, url) : { json: route };
    const status = result.status ?? 200;
    return new Response(status === 204 ? null : JSON.stringify(result.json ?? {}), { status });
  });
  vi.stubGlobal("fetch", fetchMock);
  return calls;
}

export const ADMIN = {
  id: "key_1", name: "admin", key_prefix: "dcp_abcdefgh", role: "admin", access: "write",
  project_id: null, created_at: "2026-10-23T00:00:00Z", updated_at: "2026-10-23T00:00:00Z",
  last_used_at: null, revoked_at: null,
};

export function renderApp(ui: ReactElement, { signedIn = true, path = "/", steps = STEPS }: { signedIn?: boolean; path?: string; steps?: Step[] } = {}) {
  sessionStorage.clear();
  localStorage.clear();
  if (signedIn) sessionStorage.setItem("dcp.apiKey", "dcp_test");
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <SessionProvider>
          <TutorialProvider steps={steps}>{ui}</TutorialProvider>
        </SessionProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}
