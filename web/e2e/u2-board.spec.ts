import { expect, test } from "@playwright/test";

import { signIn } from "./helpers";

test("the board shows every source's work; accept a waiting delivery", async ({ page }) => {
  await signIn(page);
  await page.getByRole("link", { name: "Program board" }).click();
  await expect(page.getByRole("heading", { name: "Program board" })).toBeVisible();

  // The seeded delivery from Surge is waiting for a decision.
  const qa = page.getByRole("region", { name: "In QA" });
  const card = qa.getByTestId("card").filter({ hasText: "Next round" });
  await expect(card).toContainText("Surge");
  await expect(card).toContainText("1 waiting for a decision");

  // Filter by source type: only the internal returns photos stay.
  await page.getByRole("button", { name: "Enterprise workflows" }).click();
  await expect(qa.getByTestId("card")).toHaveCount(0);
  await expect(page.getByTestId("card").first()).toContainText("Returns photos");
  await page.getByRole("button", { name: "All sources" }).click();

  // Open the card, then the delivery.
  await card.click();
  const drawer = page.getByRole("dialog", { name: "Details" });
  await drawer.getByRole("link", { name: /bat_/ }).click();
  await expect(page).toHaveURL(/\/batches\/bat_/);
  await expect(page.getByRole("heading", { name: /Next round/ })).toBeVisible();
  await expect(page.getByRole("region", { name: "Quality checks" })).toContainText("No files were attached");

  // Accept 480 of the 500 images.
  const decision = page.getByRole("region", { name: "Decision" });
  await decision.getByLabel(/Images to keep/).fill("480");
  await decision.getByLabel("Decided by").fill("Dana Okafor");
  await decision.getByRole("button", { name: "Accept delivery" }).click();
  await expect(decision).toContainText("480 of 500 images");
  await expect(decision).toContainText("Dana Okafor");
  await expect(page.getByRole("region", { name: "History" })).toContainText("Accepted");

  // Back on the board, the allocation has moved out of QA.
  await page.getByRole("link", { name: "← Program board" }).click();
  await expect(page.getByRole("region", { name: "In production" }).getByTestId("card").filter({ hasText: "Next round" })).toBeVisible();
  await expect(qa.getByTestId("card").filter({ hasText: "Next round" })).toHaveCount(0);
});

test("a batch that doesn't exist says so", async ({ page }) => {
  await signIn(page);
  await page.goto("/batches/bat_does_not_exist");
  await expect(page.getByText(/Couldn't load this delivery/)).toBeVisible();
});
