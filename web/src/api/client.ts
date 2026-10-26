// The one place the UI talks to DCP: the public REST API, with the signed-in API key.
import type { components } from "./schema";

export type Schemas = components["schemas"];
export type Problem = Schemas["Problem"];

export class ApiError extends Error {
  constructor(
    public status: number,
    public problem: Problem,
  ) {
    super(problem.detail);
  }
}

type Query = Record<string, string | number | boolean | null | undefined>;

let apiKey: string | null = null;
let onUnauthorized: () => void = () => {};

export function setApiKey(key: string | null): void {
  apiKey = key;
}

/** Called when the API says the key is missing or revoked (401), e.g. to sign out. */
export function setUnauthorizedHandler(handler: () => void): void {
  onUnauthorized = handler;
}

export async function api<T>(
  path: string,
  options: { method?: string; query?: Query; body?: unknown; key?: string } = {},
): Promise<T> {
  const url = new URL(path, window.location.origin);
  for (const [name, value] of Object.entries(options.query ?? {})) {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(name, String(value));
    }
  }
  const key = options.key ?? apiKey;
  const response = await fetch(url, {
    method: options.method ?? "GET",
    headers: {
      ...(key ? { Authorization: `Bearer ${key}` } : {}),
      ...(options.body !== undefined ? { "Content-Type": "application/json" } : {}),
    },
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });
  if (response.status === 204) return undefined as T;
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401 && !options.key) onUnauthorized();
    throw new ApiError(
      response.status,
      data ?? { type: "about:blank", title: response.statusText, status: response.status, detail: response.statusText },
    );
  }
  return data as T;
}

/** Every page of a list endpoint (follows next_cursor), up to `max` items. */
export async function listAll<T>(path: string, query: Query = {}, max = 1000): Promise<T[]> {
  const items: T[] = [];
  let cursor: string | null | undefined;
  do {
    const page = await api<{ data: T[]; next_cursor: string | null }>(path, {
      query: { ...query, limit: 200, cursor },
    });
    items.push(...page.data);
    cursor = page.next_cursor;
  } while (cursor && items.length < max);
  return items;
}
