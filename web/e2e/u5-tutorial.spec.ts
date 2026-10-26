import { expect, test } from "@playwright/test";
import type { Locator, Page } from "@playwright/test";

import { signIn } from "./helpers";

// Goes through the whole tutorial, doing every "your turn" step for real, to prove each one
// is detected. Runs after the other browser tests, on the same seeded demo data.

test.setTimeout(180_000);

function tutorial(page: Page) {
  const card = page.getByRole("dialog", { name: "Tutorial" });
  return {
    card,
    async at(title: string) {
      await expect(card.getByRole("heading", { name: title })).toBeVisible();
    },
    async next() {
      await card.getByRole("button", { name: /^(Next|Finish)$/ }).click();
    },
    async done() {
      await expect(card.getByRole("status")).toHaveText("✓ Done", { timeout: 15_000 });
    },
    async press(name: string | RegExp) {
      await card.getByRole("button", { name }).click();
    },
  };
}

/** The tutorial card sits over the bottom of the page; minimize it while working underneath. */
async function underCard(page: Page, work: () => Promise<void>) {
  await page.getByRole("button", { name: "Minimize the tutorial" }).click();
  await work();
  await page.getByRole("button", { name: "Show the tutorial" }).click();
}

async function click(locator: Locator) {
  await locator.scrollIntoViewIfNeeded();
  await locator.click();
}

test("the tutorial walks through every use case", async ({ page }) => {
  await signIn(page);
  await page.getByRole("button", { name: "Tutorial" }).click();
  const t = tutorial(page);

  await t.at("Welcome to Data Control Plane");
  await t.next();
  await t.at("Use the demo project");
  await t.done(); // signIn already chose the seeded demo project
  await t.next();

  for (const title of [
    "The portfolio: what the data spend bought",
    "Per capability: cost, eval change, points per $10K",
    "Per source type, honestly labelled",
    "The diagnosis: is the spend still paying off?",
  ]) {
    await t.at(title);
    await expect(page.locator(".tour-on")).toBeVisible();
    await t.next();
  }

  // Board
  await t.at("The Program board");
  await page.getByRole("link", { name: "Program board" }).click();
  await t.done();
  await t.next();
  await t.at("From request to delivered");
  await t.next();
  await t.at("Filter by source type");
  await page.getByRole("button", { name: "Human vendors" }).click();
  await t.done();
  await t.next();
  await t.at("Open a card");
  await underCard(page, async () => {
    await page.getByRole("button", { name: "All sources" }).click();
    await click(page.getByRole("region", { name: "In production" }).getByTestId("card").first());
  });
  await t.done();
  await t.next();
  await t.at("Open a delivery");
  await page.getByRole("dialog", { name: "Details" }).locator("a.rowlink").first().click();
  await t.done();
  await t.next();
  for (const title of ["Automated quality checks", "Coverage against the spec's targets", "The decision, and who made it", "Every change is recorded"]) {
    await t.at(title);
    await t.next();
  }

  // Specs
  await t.at("Specs are versioned");
  await page.getByRole("link", { name: "Specs" }).click();
  await t.done();
  await t.next();
  await t.at("See what changed between versions");
  await t.next();
  await t.at("Review and approve a version");
  await underCard(page, async () => {
    const start = page.getByRole("button", { name: /^Start v\d+$/ });
    if (await start.isVisible()) await start.click();
    const draft = page.getByRole("region", { name: "Draft" });
    await draft.getByLabel("Approved by").fill("Priya Nair");
    await draft.getByRole("button", { name: /^Approve v\d+$/ }).click();
  });
  await t.done();
  await t.next();

  // Request
  await t.at("Create a data request");
  await underCard(page, async () => {
    await page.getByRole("button", { name: "New request" }).click();
    const form = page.getByRole("dialog", { name: "New request" });
    await form.getByLabel("Capability it should improve").selectOption({ label: "Package damage detection" });
    await form.getByLabel("What data do you need?").fill("Cold-chain packages with condensation");
    await form.getByLabel("How many").fill("2000");
    await form.getByRole("combobox", { name: /^Spec/ }).selectOption({ index: 1 });
    await form.getByRole("button", { name: "Create request" }).click();
  });
  await t.done();
  await t.next();
  await t.at("Open the request");
  await underCard(page, () => page.getByRole("button", { name: "Open request" }).click());
  await t.done();
  await t.next();

  // Split
  await t.at("DCP suggests a split");
  await underCard(page, () => click(page.getByRole("button", { name: "Add all as planned allocations" })));
  await t.done();
  await t.next();
  await t.at("Or allocate by hand");
  await t.next();
  await t.at("Start the work");
  await underCard(page, () =>
    click(page.getByRole("region", { name: "Allocations" }).getByRole("row").filter({ hasText: "Surge" }).getByRole("button", { name: "Start" })),
  );
  await t.done();
  await t.next();

  // Intake
  await t.at("The source's page");
  await t.press("Take me there");
  await t.done();
  await t.next();
  await t.at("Give the source a webhook address");
  await underCard(page, () => click(page.getByRole("button", { name: "Add a webhook URL" })));
  await t.done();
  await t.next();
  await t.at("The source delivers");
  await t.press(/Simulate: the vendor's system sends a delivery/);
  await expect(t.card.getByRole("button", { name: "Next" })).toBeVisible();
  await t.next();
  await t.at("Or watch a storage bucket");
  await t.next();
  await t.at("Or through the API");
  await t.press(/Simulate: register a delivery through the API/);
  await expect(t.card.getByRole("button", { name: "Next" })).toBeVisible();
  await t.next();

  // Decide
  await t.at("Accept the good delivery");
  await expect(page.getByRole("heading", { name: /Cold-chain packages/ })).toBeVisible();
  await underCard(page, async () => {
    const decision = page.getByRole("region", { name: "Decision" });
    await decision.getByLabel(/to keep/).fill("1150");
    await decision.getByLabel("Decided by").fill("Dana Okafor");
    await decision.getByRole("button", { name: "Accept delivery" }).click();
  });
  await t.done();
  await t.next();
  await t.at("Reject the weak one");
  await expect(page.getByRole("group", { name: "Delivery totals" })).toContainText("600 images");
  await underCard(page, async () => {
    const decision = page.getByRole("region", { name: "Decision" });
    await decision.getByRole("button", { name: "Reject", exact: true }).click();
    await decision.getByLabel("Why reject it?").fill("Rater agreement 0.74, below the 0.85 target.");
    await decision.getByRole("button", { name: "Reject delivery" }).click();
  });
  await t.done();
  await t.next();
  await t.at("The source's track record updates");
  await t.next();

  // Dataset and eval
  await t.at("Lineage: from request to eval");
  await t.next();
  await t.at("Freeze the next version");
  await underCard(page, async () => {
    await page.getByRole("button", { name: "New version" }).click();
    const drawer = page.getByRole("dialog", { name: "New dataset version" });
    await drawer.getByRole("checkbox").first().check();
    await drawer.getByRole("button", { name: /^Freeze with/ }).click();
  });
  await t.done();
  await t.next();
  await t.at("Record the eval result");
  await underCard(page, async () => {
    const form = page.getByRole("region", { name: "Record an eval result" });
    await form.getByLabel("Value").fill("0.872");
    await form.getByRole("button", { name: "Record result" }).click();
  });
  await t.done();
  await t.next();
  await t.at("The eval moved");
  await t.next();

  // Close the loop
  await t.at("Back to the results");
  await t.next();
  await t.at("Complete the work");
  await underCard(page, () => click(page.getByRole("region", { name: "Allocations" }).getByRole("button", { name: "Complete" })));
  await t.done();
  await t.next();
  await t.at("Close the request");
  await underCard(page, () => page.getByRole("button", { name: "Close request" }).click());
  await t.done();
  await t.next();

  // Admin
  await t.at("Add a capability");
  await underCard(page, async () => {
    await page.getByRole("button", { name: "New capability" }).click();
    const form = page.getByRole("dialog", { name: "New capability" });
    await form.getByLabel("Name").fill("Shipping label legibility");
    await form.getByLabel("Eval metric").fill("read error rate");
    await form.getByLabel(/^Better is/).selectOption("false");
    await form.getByLabel(/^Value of one point/).fill("41000");
    await form.getByRole("button", { name: "Create capability" }).click();
  });
  await t.done();
  await t.next();
  await t.at("Register a new source");
  await underCard(page, async () => {
    await page.getByRole("button", { name: "New source" }).click();
    const form = page.getByRole("dialog", { name: "New source" });
    await form.getByLabel("Name").fill("Tutorial SimLab");
    await form.getByLabel(/^Type/).selectOption({ label: "Synthetic data" });
    await form.getByRole("button", { name: "Create source" }).click();
  });
  await t.done();
  await t.next();
  await t.at("Give a teammate access");
  await underCard(page, async () => {
    const keys = page.getByRole("region", { name: "API keys" });
    await keys.getByLabel(/^Name/).fill("Teammate (read-only)");
    await keys.getByRole("combobox", { name: /^Project/ }).selectOption({ index: 1 });
    await click(keys.getByRole("button", { name: "Create key" }));
  });
  await t.done();
  await t.next();
  await t.at("Take access away");
  await underCard(page, async () => {
    const keys = page.getByRole("region", { name: "API keys" });
    await click(keys.getByRole("button", { name: "Revoke Teammate (read-only)" }));
    await click(keys.getByRole("button", { name: "Yes, revoke" }));
  });
  await t.done();
  await t.next();
  await t.at("Send updates to your other tools");
  await underCard(page, async () => {
    const hooks = page.getByRole("region", { name: "Webhooks" });
    await hooks.getByRole("button", { name: "Add an address" }).click();
    await hooks.getByLabel("Address (URL)").fill("https://example.com/tutorial-hook");
    await hooks.getByRole("button", { name: "Add", exact: true }).click();
  });
  await t.done();
  await t.next();

  await t.at("Everything you did is in the API");
  await t.next();
  await t.at("That's the whole loop");
  await t.next();
  await expect(t.card).toBeHidden();
});
