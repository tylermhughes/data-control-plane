import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ADMIN, fakeApi, renderApp } from "../test/render";
import { useTutorial } from "./engine";
import type { Step } from "./engine";
import { sha256, signWebhook } from "./simulate";
import { STEPS, newestDemo } from "./steps";
import { event } from "./steps";

function StartButton() {
  const tutorial = useTutorial();
  return (
    <button type="button" onClick={() => tutorial.start()}>
      Start
    </button>
  );
}

const TEST_STEPS: Step[] = [
  { id: "hello", chapter: "One", title: "Hello there", body: <p>First step.</p> },
  {
    id: "make",
    chapter: "One",
    title: "Make a capability",
    body: "Do it.",
    task: "create a capability",
    done: event("capability.created", { save: (e) => ({ capabilityId: e.subject_id }) }),
  },
  {
    id: "sim",
    chapter: "Two",
    title: "Simulate",
    body: (v) => `Made ${v.capabilityId}`,
    action: { label: "Simulate it", run: async () => ({ simulated: "yes" }) },
  },
  { id: "end", chapter: "Two", title: "The end", body: "Bye." },
];

function setup(events: unknown[] = []) {
  return fakeApi({
    "GET /v1/me": ADMIN,
    "GET /v1/projects": { data: [], next_cursor: null },
    "GET /v1/events": { data: events, next_cursor: null },
  });
}

const card = () => screen.getByRole("dialog", { name: "Tutorial" });

describe("tutorial", () => {
  it("walks forward and back, and ticks off a step when its event appears", async () => {
    setup([{ id: "evt_1", type: "capability.created", subject_id: "cap_9", created_at: new Date().toISOString(), data: {} }]);
    renderApp(<StartButton />, { steps: TEST_STEPS });
    fireEvent.click(screen.getByRole("button", { name: "Start" }));
    expect(within(card()).getByText("Hello there")).toBeTruthy();
    expect(within(card()).getByText(/step 1 of 4/)).toBeTruthy();

    fireEvent.click(within(card()).getByRole("button", { name: "Next" }));
    expect(within(card()).getByText("Make a capability")).toBeTruthy();
    expect(await within(card()).findByText("✓ Done")).toBeTruthy();

    fireEvent.click(within(card()).getByRole("button", { name: "Next" }));
    expect(within(card()).getByText("Made cap_9")).toBeTruthy(); // vars saved from the event
    fireEvent.click(within(card()).getByRole("button", { name: "Simulate it" }));
    await waitFor(() => expect(within(card()).getByRole("button", { name: "Next" })).toBeTruthy());

    fireEvent.click(within(card()).getByRole("button", { name: "Back" }));
    expect(within(card()).getByText("Make a capability")).toBeTruthy();
    const saved = JSON.parse(localStorage.getItem("dcp.tutorial") ?? "{}");
    expect(saved.done).toEqual(["make", "sim"]);
    expect(saved.vars).toEqual({ capabilityId: "cap_9", simulated: "yes" });
  });

  it("lets you skip a step you haven't done, jump by chapter, minimize and close", async () => {
    setup();
    renderApp(<StartButton />, { steps: TEST_STEPS });
    fireEvent.click(screen.getByRole("button", { name: "Start" }));
    fireEvent.click(within(card()).getByRole("button", { name: "Next" }));
    expect(within(card()).getByText(/Your turn: create a capability/)).toBeTruthy();
    fireEvent.click(within(card()).getByRole("button", { name: "Skip" }));
    expect(within(card()).getByText("Simulate")).toBeTruthy();

    fireEvent.click(within(card()).getByRole("button", { name: "Chapters" }));
    fireEvent.click(within(card()).getByRole("button", { name: /0\. One/ }));
    expect(within(card()).getByText("Hello there")).toBeTruthy();

    fireEvent.click(within(card()).getByRole("button", { name: "Chapters" }));
    fireEvent.click(within(card()).getByRole("button", { name: /Start over/ }));
    expect(within(card()).getByText("Hello there")).toBeTruthy();
    expect(JSON.parse(localStorage.getItem("dcp.tutorial") ?? "{}").done).toEqual([]);

    fireEvent.click(within(card()).getByRole("button", { name: "Minimize the tutorial" }));
    fireEvent.click(screen.getByRole("button", { name: "Show the tutorial" }));
    fireEvent.click(within(card()).getByRole("button", { name: "Close the tutorial" }));
    expect(screen.queryByRole("dialog", { name: "Tutorial" })).toBeNull();
  });
});

describe("the journey", () => {
  it("has unique steps, and every step you must do says what to do", () => {
    expect(new Set(STEPS.map((s) => s.id)).size).toBe(STEPS.length);
    for (const s of STEPS) if (s.done) expect(s.task, s.id).toBeTruthy();
    expect(new Set(STEPS.map((s) => s.chapter)).size).toBeGreaterThanOrEqual(12);
  });

  it("picks the newest demo project", () => {
    const projects = [
      { id: "a", name: "North-star demo 09:00:00", created_at: "2026-10-23T09:00:00Z" },
      { id: "b", name: "North-star demo 10:00:00", created_at: "2026-10-24T10:00:00Z" },
      { id: "c", name: "Fulfillment Vision", created_at: "2026-10-25T00:00:00Z" },
    ] as Parameters<typeof newestDemo>[0];
    expect(newestDemo(projects)?.id).toBe("b");
  });
});

describe("signWebhook", () => {
  it("signs like the Standard Webhooks spec (and DCP's own verifier)", async () => {
    const signature = await signWebhook("whsec_c2VjcmV0LWtleS1mb3ItdGVzdHM=", "msg_1", 1700000000, '{"a":1}');
    expect(signature).toBe("v1,gXywnxeEf2YHZtqre4tCNcV/1MVD1ukMOxG1B0520es=");
  });

  it("gives the same signature without the browser's crypto (pages on plain http)", async () => {
    const signature = await signWebhook("whsec_c2VjcmV0LWtleS1mb3ItdGVzdHM=", "msg_1", 1700000000, '{"a":1}', null);
    expect(signature).toBe("v1,gXywnxeEf2YHZtqre4tCNcV/1MVD1ukMOxG1B0520es=");
  });

  it("hashes like SHA-256, across block boundaries", () => {
    const hex = (bytes: Uint8Array) => [...bytes].map((b) => b.toString(16).padStart(2, "0")).join("");
    expect(hex(sha256(new TextEncoder().encode("abc")))).toBe("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
    expect(hex(sha256(new TextEncoder().encode("a".repeat(1000))))).toBe("41edece42d63e8d9bf515a9ba6932e1c20cbc9f5a5d134645adb5db1b9737ea3");
  });
});
