import { expect, test, type Page } from "@playwright/test";

const user = { id: "u1", email: "student@example.com", display_name: "Student", created_at: "2026-01-01T00:00:00Z" };
async function mockApi(page: Page) {
  let authenticated = false; let predictions: any[] = [];
  await page.route("**/api/**", async route => {
    const request = route.request(); const path = new URL(request.url()).pathname;
    const fulfill = (json: unknown, status = 200) => route.fulfill({ status, contentType: "application/json", body: status === 204 ? "" : JSON.stringify(json) });
    if (path === "/api/auth/me") return fulfill(authenticated ? user : { detail: "Authentication required" }, authenticated ? 200 : 401);
    if (path === "/api/auth/register" || path === "/api/auth/login") { authenticated = true; return fulfill(user, path.endsWith("register") ? 201 : 200); }
    if (path === "/api/auth/logout") { authenticated = false; predictions = []; return fulfill({}, 204); }
    if (path === "/api/overview") return fulfill({ total: predictions.length, normal: predictions.length, flagged: 0, model_version: "1.0.0", recent: predictions });
    if (path === "/api/predictions" && request.method() === "POST") { const prediction = { id: "p1", probability: .18, predicted_failure: false, result: "Normal Operation", risk_level: "low", recommendation: "Continue routine monitoring.", model_version: "1.0.0", created_at: new Date().toISOString(), inputs: JSON.parse(request.postData() || "{}") }; predictions = [prediction]; return fulfill(prediction); }
    if (path === "/api/predictions") return fulfill({ items: predictions, total: predictions.length, page: 1, page_size: 20 });
    return fulfill({});
  });
}

test("registration, prediction, history and account switch isolation", async ({ page }) => {
  await mockApi(page); await page.goto("/register");
  await page.getByLabel("Display name").fill("Student"); await page.getByLabel("Email address").fill("student@example.com"); await page.getByLabel("Password").fill("safe-password-123"); await page.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByText("Know where to look next.")).toBeVisible(); await page.getByRole("link", { name: /New Prediction/ }).click(); await page.getByRole("button", { name: "Analyse machine" }).click(); await expect(page.getByText("Normal Operation")).toBeVisible();
  await page.getByRole("link", { name: /Prediction History/ }).click(); await expect(page.getByText("18.0%")).toBeVisible();
  await page.getByRole("button", { name: "Log out" }).click(); await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible(); await page.getByLabel("Email address").fill("other@example.com"); await page.getByLabel("Password").fill("safe-password-456"); await page.getByRole("button", { name: "Sign in" }).click(); await page.getByRole("link", { name: /Prediction History/ }).click(); await expect(page.getByText("No matching predictions.")).toBeVisible();
});

test("mobile navigation remains keyboard and touch accessible", async ({ page }) => {
  await mockApi(page); await page.setViewportSize({ width: 390, height: 844 }); await page.goto("/login"); await page.getByLabel("Email address").fill("student@example.com"); await page.getByLabel("Password").fill("safe-password-123"); await page.getByRole("button", { name: "Sign in" }).click(); await page.getByRole("button", { name: "Toggle navigation" }).click(); await expect(page.getByRole("link", { name: /Batch Analysis/ })).toBeVisible();
});
