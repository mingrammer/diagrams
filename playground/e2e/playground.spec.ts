import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  // wait for Pyodide init + the default example to finish rendering
  await expect(page.getByTestId("preview").locator("svg")).toBeVisible({ timeout: 150_000 });
});

test("renders the default example with icons", async ({ page }) => {
  const preview = page.getByTestId("preview");
  await expect(preview.locator("svg image").first()).toHaveAttribute("xlink:href", /icons\/aws\//);
});

test("autocompletes EC2 from the aws compute module", async ({ page }) => {
  const editor = page.getByTestId("editor").locator(".cm-content");
  await editor.click();
  await page.keyboard.press("ControlOrMeta+a");
  await page.keyboard.type("from diagrams.aws.compute import EC2A");
  await expect(page.locator(".cm-tooltip-autocomplete")).toContainText("EC2AutoScaling", { timeout: 10_000 });
});

test("share link roundtrips code", async ({ page, context }) => {
  const editor = page.getByTestId("editor").locator(".cm-content");
  await editor.click();
  await page.keyboard.press("ControlOrMeta+a");
  await page.keyboard.type('from diagrams import Diagram\nwith Diagram("Shared", show=False):\n    pass');
  await page.getByTestId("share-button").click();
  await expect(page.getByTestId("share-button")).toContainText("Link copied!");
  const url = page.url();
  expect(url).toContain("#code=");
  const second = await context.newPage();
  await second.goto(url);
  await expect(second.getByTestId("editor")).toContainText("Shared", { timeout: 150_000 });
});

test("python errors keep the previous preview", async ({ page }) => {
  const editor = page.getByTestId("editor").locator(".cm-content");
  await editor.click();
  await page.keyboard.press("ControlOrMeta+a");
  await page.keyboard.type("1/0");
  await expect(page.getByTestId("error-panel")).toContainText("ZeroDivisionError", { timeout: 30_000 });
  await expect(page.getByTestId("preview").locator("svg")).toBeVisible();
});

test("exports PNG", async ({ page }) => {
  const downloadPromise = page.waitForEvent("download");
  // Background White is the ExportBar's default; WIDTH/HEIGHT left as
  // "auto" fall back to the default-2x output size.
  await page.getByRole("button", { name: "PNG" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(/\.png$/);
});

test("copies image to clipboard", async ({ page }) => {
  await page.getByRole("button", { name: "Copy Image" }).click();
  await expect(page.getByText("Copied!")).toBeVisible();
});
