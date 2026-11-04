import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";
import * as renderer from "./render-package.mjs";

test("newcomer can select an executable outside a platform default", async t => {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), "xhs-chrome-location-"));
  t.after(() => fs.rm(dir, {recursive:true, force:true}));
  const executable = path.join(dir, "custom-chrome");
  await fs.writeFile(executable, "#!/bin/sh\nexit 0\n", {mode:0o755});
  assert.equal(renderer.resolveChromePath({chromePath:executable}), executable);
  assert.equal(renderer.resolveChromePath({env:{XHS_CHROME_PATH:executable, PATH:""}}), executable);
});

test("missing explicit Chrome is an actionable dependency failure", () => {
  assert.throws(() => renderer.resolveChromePath({chromePath:"/definitely-not-installed/chrome"}), /Chrome.*unavailable/);
});

test("system PATH discovery finds a member's installed Chromium", async t => {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), "xhs-chromium-location-"));
  t.after(() => fs.rm(dir, {recursive:true, force:true}));
  const executable = path.join(dir, "chromium");
  await fs.writeFile(executable, "#!/bin/sh\nexit 0\n", {mode:0o755});
  assert.equal(renderer.resolveChromePath({env:{PATH:dir}, platform:"linux"}), executable);
});

test("production CLI accepts --chrome-path and reports the missing executable", async t => {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), "xhs-portable-cli-"));
  t.after(() => fs.rm(dir, {recursive:true, force:true}));
  await fs.writeFile(path.join(dir,"source.json"), JSON.stringify({title:"演示",body:"这是测试。"}));
  const result = spawnSync(process.execPath,[fileURLToPath(new URL("./render-package.mjs",import.meta.url)),dir,"--chrome-path","/definitely-not-installed/chrome"],{encoding:"utf8"});
  assert.notEqual(result.status,0);
  assert.match(result.stderr,/Chrome.*unavailable/);
  assert.doesNotMatch(result.stderr,/Usage:/);
});

test("failed Chrome selection cannot leave old successful package markers", async t => {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), "xhs-chrome-failure-"));
  t.after(() => fs.rm(dir, {recursive:true, force:true}));
  await fs.writeFile(path.join(dir,"source.json"), JSON.stringify({title:"演示",body:"这是测试。"}));
  for (const name of ["validation.json","manifest.json","final-verification.json"]) await fs.writeFile(path.join(dir,name),"{\"ok\":true}");
  await assert.rejects(renderer.renderPackage(dir,{chromePath:"/definitely-not-installed/chrome"}), /Chrome.*unavailable/);
  for (const name of ["validation.json","manifest.json","final-verification.json"]) await assert.rejects(fs.access(path.join(dir,name)), {code:"ENOENT"});
});
