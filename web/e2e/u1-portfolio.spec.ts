import { expect, test } from "@playwright/test";

import { signIn } from "./helpers";

test("a bad key is refused with the API's reason", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("API key").fill("dcp_not-a-real-key");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("alert")).toHaveText("Invalid or revoked API key.");
});

test("sign in, see the portfolio and the diagnosis, sign out", async ({ page }) => {
  await signIn(page);
  await expect(page).toHaveURL(/\/portfolio$/);
  const totals = page.getByRole("group", { name: "Totals" });
  await expect(totals).toContainText("$18,825"); // the demo's spend with step 7, plus the waiting delivery
  await expect(page.getByRole("cell", { name: /Package damage detection/ })).toBeVisible();
  await expect(page.getByText("Eval change is an estimate")).toBeVisible();
  const diagnosis = page.getByTestId("diagnosis");
  await expect(diagnosis).toContainText("Refine the spec");
  await expect(diagnosis).toContainText("shrink_wrapped");

  await page.reload(); // the key is kept for this tab
  await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible();
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page.getByLabel("API key")).toBeVisible();
});

test("deep links work", async ({ page }) => {
  await signIn(page);
  await page.goto("/settings");
  await expect(page.getByRole("heading", { name: "Settings" })).toBeVisible();
});
