import { expect, test } from "@playwright/test";

import { signIn } from "./helpers";

test("sources: track record, a delivery webhook, and a new source", async ({ page }) => {
  await signIn(page);
  await page.getByRole("link", { name: "Sources & vendors" }).click();
  const surge = page.getByTestId("source-card").filter({ hasText: "Surge" });
  await expect(surge).toContainText("Accept rate");
  await surge.click();

  await expect(page.getByRole("heading", { name: /Surge/ })).toBeVisible();
  await expect(page.getByRole("region", { name: "Work" })).toContainText("Shrink-wrapped and glossy packaging");
  await page.getByRole("button", { name: "Add a webhook URL" }).click();
  const secret = page.getByRole("status", { name: /Signing secret/ });
  await expect(secret).toContainText("whsec_");
  await expect(page.getByRole("region", { name: "Inbound webhooks" })).toContainText("/v1/inbound/ihk_");

  await page.getByRole("link", { name: "← Sources & vendors" }).click();
  await page.getByRole("button", { name: "New source" }).click();
  const form = page.getByRole("dialog", { name: "New source" });
  await form.getByLabel("Name").fill("Northgate SimLab");
  await form.getByLabel("Type").selectOption({ label: "Synthetic data" });
  await form.getByRole("button", { name: "Create source" }).click();
  await expect(page.getByRole("heading", { name: /Northgate SimLab/ })).toBeVisible();
});

test("lineage: trace a version, freeze the next one and record its eval", async ({ page }) => {
  await signIn(page);
  await page.getByRole("link", { name: "Lineage & spend" }).click();
  const chain = page.getByRole("region", { name: "Lineage" });
  await expect(chain).toContainText("Where v3 came from");
  await expect(chain).toContainText("0.857 → 0.861");
  await expect(page.getByRole("region", { name: "Spend and yield" })).toContainText("new in v3");

  // The delivery accepted in the board test can go into v4.
  await page.getByRole("button", { name: "New version" }).click();
  const drawer = page.getByRole("dialog", { name: "New dataset version" });
  await drawer.getByRole("checkbox").first().check();
  await drawer.getByRole("button", { name: /Freeze with 1 new delivery/ }).click();
  await expect(chain).toContainText("Where v4 came from");
  await expect(chain).toContainText("Not recorded yet");

  const form = page.getByRole("region", { name: "Record an eval result" });
  await form.getByLabel("Value").fill("0.866");
  await form.getByRole("button", { name: "Record result" }).click();
  await expect(chain).toContainText("0.861 → 0.866");
  await expect(page.getByRole("region", { name: "Eval impact" })).toContainText("+0.005");
});

test("settings: capabilities, a read-only key shown once then revoked, a webhook", async ({ page }) => {
  await signIn(page);
  await page.getByRole("link", { name: "Settings" }).click();
  await expect(page.getByRole("region", { name: "Capabilities" })).toContainText("Package damage detection");

  await page.getByRole("navigation", { name: "Settings" }).getByRole("link", { name: "API keys" }).click();
  const keys = page.getByRole("region", { name: "API keys" });
  await keys.getByLabel("Name").fill("Dashboard (read-only)");
  await keys.getByRole("combobox", { name: /^Project/ }).selectOption({ index: 1 });
  await keys.getByRole("button", { name: "Create key" }).click();
  await expect(keys.getByRole("status")).toContainText("dcp_");
  await keys.getByRole("button", { name: "Revoke Dashboard (read-only)" }).click();
  await keys.getByRole("button", { name: "Yes, revoke" }).click();
  await expect(keys.getByRole("row").filter({ hasText: "Dashboard (read-only)" })).toContainText("Revoked");

  await page.getByRole("navigation", { name: "Settings" }).getByRole("link", { name: "Webhooks" }).click();
  const hooks = page.getByRole("region", { name: "Webhooks" });
  await hooks.getByRole("button", { name: "Add an address" }).click();
  await hooks.getByLabel("Address (URL)").fill("https://example.com/dcp-hook");
  await hooks.getByRole("button", { name: "Add", exact: true }).click();
  await expect(hooks.getByRole("status")).toContainText("whsec_");
  await expect(hooks).toContainText("https://example.com/dcp-hook");
});
