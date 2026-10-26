import { expect, test } from "@playwright/test";

import { signIn } from "./helpers";

test("review the drafted spec's changes and approve it", async ({ page }) => {
  await signIn(page);
  await page.getByRole("link", { name: "Specs" }).click();
  await page.getByRole("navigation", { name: "Specs" }).getByRole("link", { name: /Package damage/ }).click();

  // The diagnosis drafted v2 with new coverage targets; the changes are highlighted.
  await expect(page.getByRole("heading", { name: /Package damage v2/ })).toBeVisible();
  const changes = page.getByRole("region", { name: "Changes" });
  await expect(changes).toContainText("Target package_type=shrink_wrapped");

  const draft = page.getByRole("region", { name: "Draft" });
  await draft.getByLabel("Approved by").fill("Priya Nair");
  await draft.getByRole("button", { name: "Approve v2" }).click();
  await expect(page.getByRole("button", { name: "Start v3" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Version history" })).toContainText("Priya Nair");
});

test("create a request, open it, split it across sources and start the work", async ({ page }) => {
  await signIn(page);
  await page.getByRole("link", { name: "Requests" }).click();
  await page.getByRole("button", { name: "New request" }).click();

  const form = page.getByRole("dialog", { name: "New request" });
  await form.getByLabel("Capability it should improve").selectOption({ label: "Package damage detection" });
  await form.getByLabel("What data do you need?").fill("Cold-chain packages with condensation");
  await form.getByLabel("Requested by").fill("Marco Díaz");
  await form.getByLabel("How many").fill("3000");
  await form.getByLabel(/^Spec/).selectOption({ label: "Package damage v1" });
  await form.getByRole("button", { name: "Create request" }).click();

  await expect(page).toHaveURL(/\/requests\/req_/);
  await expect(page.getByRole("heading", { name: /Cold-chain packages/ })).toContainText("draft");
  await page.getByRole("button", { name: "Open request" }).click();
  await expect(page.getByRole("heading", { name: /Cold-chain packages/ })).toContainText("open");

  // DCP suggests a split from each source's track record; add it.
  const plan = page.getByRole("region", { name: "Suggested split" });
  await expect(plan).toContainText("3,000 images still to plan for");
  await plan.getByRole("button", { name: "Add all as planned allocations" }).click();
  await expect(plan).toContainText("Fully allocated");

  const allocations = page.getByRole("region", { name: "Allocations" });
  await expect(allocations.getByRole("row")).not.toHaveCount(1);
  const first = allocations.getByRole("row").nth(1);
  await expect(first).toContainText("planned");
  await first.getByRole("button", { name: "Start" }).click();
  await expect(first).toContainText("active");
  await expect(page.getByRole("region", { name: "History" })).toContainText("Request opened");
});
