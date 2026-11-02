import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const skillPath = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "SKILL.md");

test("锁定模板直接使用现有视觉合同，设计变更才调用设计技能", async () => {
  const skill = await fs.readFile(skillPath, "utf8");
  const visualContract = "Read [visual-contract.md](references/visual-contract.md) completely before any image work.";

  assert.ok(skill.includes(visualContract), "必须先读取完整视觉合同");
  assert.match(skill, /ui-ux-pro-max only when the user has authorized a\s+template design change/);
  assert.match(skill, /new general design-system search\s+is not a prerequisite/);
  assert.match(skill, /never alter, summarize, reorder, or omit source copy/);
});
