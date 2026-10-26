import { expect } from "@playwright/test";
import type { Page } from "@playwright/test";

declare const process: { env: Record<string, string | undefined> };

export const API_KEY = process.env.DCP_API_KEY ?? "";
export const PROJECT_ID = process.env.DCP_PROJECT_ID ?? "";

/** Sign in with the seeded admin key and pick the seeded project. */
export async function signIn(page: Page): Promise<void> {
  await page.goto("/");
  await page.getByLabel("API key").fill(API_KEY);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible();
  if (PROJECT_ID) await page.getByLabel("Project").selectOption(PROJECT_ID);
}
