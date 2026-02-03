import { test, expect } from "@playwright/test";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

test("上傳檔案並清理翻譯/校正混合文字", async ({ page }) => {
  const filePath = path.resolve(__dirname, "../../test_files/test.pptx");

  await page.goto("/");

  const fileInput = page.getByTestId("file-input");
  await fileInput.setInputFiles(filePath);

  const extractButton = page.getByTestId("extract-button");
  await extractButton.click();

  const firstSource = page.getByTestId("block-source-text").first();
  await expect(firstSource).toBeVisible();

  const sourceText = (await firstSource.innerText()).trim();
  const firstTarget = page.getByTestId("block-target-text").first();

  await firstTarget.fill(`${sourceText} Proposed Solutions`);

  const cleanedValue = await firstTarget.inputValue();
  expect(cleanedValue).not.toContain(sourceText);
});

test("可切換來源與目標語言", async ({ page }) => {
  await page.goto("/");

  const step2Header = page.getByTestId("step2-header");
  await step2Header.click();

  const sourceLangTrigger = page.getByTestId("source-lang-select-trigger");
  await sourceLangTrigger.click();
  await page.getByTestId("source-lang-select-option-vi").click();

  const targetLangTrigger = page.getByTestId("target-lang-select-trigger");
  await targetLangTrigger.click();
  await page.getByTestId("target-lang-select-option-en").click();

  await expect(sourceLangTrigger).toContainText("Tiếng Việt");
  await expect(targetLangTrigger).toContainText("English");
});
