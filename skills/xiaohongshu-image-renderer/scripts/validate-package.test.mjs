import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import zlib from "node:zlib";

import { renderPackage } from "./render-package.mjs";
import { validatePackage } from "./validate-package.mjs";

const OUTPUT_FILES = ["validation.json", "manifest.json", "final-verification.json"];

function sourceHash(source) {
  return crypto.createHash("sha256")
    .update(`${String(source.title).trim()}\n${String(source.body).replace(/\s+/gu, "").trim()}`)
    .digest("hex");
}

function crc32(bytes) {
  let value = 0xffffffff;
  for (const byte of bytes) {
    value ^= byte;
    for (let bit = 0; bit < 8; bit += 1) value = (value >>> 1) ^ (value & 1 ? 0xedb88320 : 0);
  }
  return (value ^ 0xffffffff) >>> 0;
}

function pngChunk(type, data) {
  const name = Buffer.from(type, "ascii");
  const chunk = Buffer.alloc(12 + data.length);
  chunk.writeUInt32BE(data.length, 0);
  name.copy(chunk, 4);
  data.copy(chunk, 8);
  chunk.writeUInt32BE(crc32(Buffer.concat([name, data])), 8 + data.length);
  return chunk;
}

function validPng(page) {
  const header = Buffer.alloc(13);
  header.writeUInt32BE(1080, 0);
  header.writeUInt32BE(1440, 4);
  header[8] = 8;
  header[9] = 6;
  const pixels = Buffer.alloc((1080 * 4 + 1) * 1440, page);
  for (let row = 0; row < 1440; row += 1) pixels[row * (1080 * 4 + 1)] = 0;
  return Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    pngChunk("IHDR", header),
    pngChunk("IDAT", zlib.deflateSync(pixels)),
    pngChunk("IEND", Buffer.alloc(0)),
  ]);
}

function tableBlock(sourceColumnIndexes, header, rows, tableIndex, tableGroupIndex) {
  return {
    type: "table",
    header,
    alignments: header.map(() => "left"),
    rows,
    sourceColumnIndexes,
    tableIndex,
    tableGroupIndex,
    repeatedKeyColumn: sourceColumnIndexes.length === 2 && sourceColumnIndexes[1] === 4,
  };
}

function htmlEscape(value) {
  return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

function htmlForBlock(block) {
  if (block.type === "paragraph") return `<p data-render-block="paragraph">${htmlEscape(block.renderedText)}</p>`;
  if (block.type === "heading") return `<h2 data-render-block="heading">${htmlEscape(block.renderedText)}</h2>`;
  if (block.type === "list") return `<ul data-render-block="list">${block.items.map(item => `<li>${htmlEscape(item)}</li>`).join("")}</ul>`;
  return `<div data-render-block="table" data-render-table-index="${block.tableIndex}" data-render-table-group-index="${block.tableGroupIndex}"><table><thead><tr>${block.header.map(cell => `<th>${htmlEscape(cell)}</th>`).join("")}</tr></thead><tbody>${block.rows.map(row => `<tr>${row.map(cell => `<td>${htmlEscape(cell)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}

async function writeFinalHtml(directory, source, pages) {
  const workDirectory = path.join(directory, "_render-work");
  await fs.mkdir(workDirectory, { recursive: true });
  await Promise.all(pages.map((page, index) => fs.writeFile(
    path.join(workDirectory, `page-${String(index + 1).padStart(2, "0")}.html`),
    `<main>${index === 0 ? `<h1 data-render-title>${htmlEscape(source.title)}</h1>` : ""}${page.blocks.map(htmlForBlock).join("")}</main>`,
  )));
}

async function writeJson(directory, filename, value) {
  await fs.writeFile(path.join(directory, filename), `${JSON.stringify(value, null, 2)}\n`);
}

async function readJson(directory, filename) {
  return JSON.parse(await fs.readFile(path.join(directory, filename), "utf8"));
}

async function createValidFixture(t) {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), "xhs-validator-test-"));
  t.after(() => fs.rm(directory, { recursive: true, force: true }));

  const tableHeader = ["岗位", "用户", "场景", "动作", "指标"];
  const tableRows = [
    ["运营 R1", "用户 U1", "场景 S1", "动作 A1", "指标 M1"],
    ["产品 R2", "用户 U2", "场景 S2", "动作 A2", "指标 M2"],
  ];
  const tableMarkdown = [
    `| ${tableHeader.join(" | ")} |`,
    "| --- | --- | --- | --- | --- |",
    ...tableRows.map(row => `| ${row.join(" | ")} |`),
  ].join("\n");
  const source = {
    title: "渠道策略必须保留证据链",
    body: `开场段落必须逐字保留。\n\n${tableMarkdown}`,
    masterRecordId: "rec-master-1",
    masterContentId: "CNT-000001",
    platformRecordId: "rec-xhs-1",
    platformContentId: "XHS-000001",
    jobId: "xhsjob-1",
  };
  source.sourceHash = sourceHash(source);

  const pages = [
    {
      page: 1,
      kind: "cover",
      blocks: [{
        type: "paragraph",
        markdown: "开场段落必须逐字保留。",
        renderedText: "开场段落必须逐字保留。",
      }],
    },
    {
      page: 2,
      kind: "body",
      blocks: [tableBlock([0, 1, 2, 3], tableHeader.slice(0, 4), [tableRows[0].slice(0, 4)], 0, 0)],
    },
    {
      page: 3,
      kind: "body",
      blocks: [
        tableBlock([0, 1, 2, 3], tableHeader.slice(0, 4), [tableRows[1].slice(0, 4)], 0, 0),
        tableBlock([0, 4], [tableHeader[0], tableHeader[4]], tableRows.map(row => [row[0], row[4]]), 0, 1),
      ],
    },
  ];

  const pngs = [validPng(1), validPng(2), validPng(3)];
  const filenames = ["01.png", "02.png", "03.png"];
  const results = filenames.map((filename, index) => {
    const contentTop = index === 0 ? 145 : 143;
    const availableHeight = 1376 - contentTop;
    const contentHeight = Math.round(availableHeight * 0.85);
    return {
      page: index + 1,
      filename,
      width: 1080,
      height: 1440,
      contentTop,
      contentBottom: contentTop + contentHeight,
      contentHeight,
      availableHeight,
      fillRatio: contentHeight / availableHeight,
      contentBottomLimit: 1376,
      overflow: false,
      tableRows: index === 0 ? [] : [{ top: 200, bottom: 300 }],
      sha256: crypto.createHash("sha256").update(pngs[index]).digest("hex"),
    };
  });
  const stats = {
    sourceHash: source.sourceHash,
    width: 1080,
    height: 1440,
    pageCount: 3,
    filenames,
    overflowCount: 0,
    results,
    ok: true,
  };

  await Promise.all([
    writeJson(directory, "source.json", source),
    writeJson(directory, "copy.json", { xiaohongshu_title: "保留原文案" }),
    writeJson(directory, "pages.json", pages),
    writeJson(directory, "render-stats.json", stats),
    writeFinalHtml(directory, source, pages),
    ...filenames.map((filename, index) => fs.writeFile(path.join(directory, filename), pngs[index])),
  ]);
  return { directory, source, pages, stats, tableHeader, tableRows };
}

function hasError(report, code) {
  return report.errors.some(error => error.code === code);
}

async function assertNoFinalArtifacts(directory) {
  const entries = await fs.readdir(directory);
  for (const filename of OUTPUT_FILES) assert.equal(entries.includes(filename), false, filename);
}

test("缺少页面图片时失败并清除旧的通过产物", async t => {
  const fixture = await createValidFixture(t);
  await Promise.all(OUTPUT_FILES.map(filename => writeJson(fixture.directory, filename, { ok: true })));
  await fs.unlink(path.join(fixture.directory, "02.png"));

  const first = await validatePackage(fixture.directory);
  const second = await validatePackage(fixture.directory);

  assert.equal(first.ok, false);
  assert.equal(hasError(first, "MISSING_PAGE_IMAGE"), true);
  assert.deepEqual(second, first);
  await assertNoFinalArtifacts(fixture.directory);
});

test("非连续编号的页面图片失败", async t => {
  const fixture = await createValidFixture(t);
  await fs.rename(path.join(fixture.directory, "02.png"), path.join(fixture.directory, "04.png"));

  const report = await validatePackage(fixture.directory);

  assert.equal(report.ok, false);
  assert.equal(hasError(report, "NON_CONTINUOUS_PAGE_FILENAMES"), true);
});

test("sourceHash 与当前 source.json 内容不一致时失败", async t => {
  const fixture = await createValidFixture(t);
  const changed = { ...fixture.source, sourceHash: "0".repeat(64) };
  await writeJson(fixture.directory, "source.json", changed);

  const report = await validatePackage(fixture.directory);

  assert.equal(report.ok, false);
  assert.equal(hasError(report, "SOURCE_HASH_MISMATCH"), true);
});

test("缺失、空、格式错误或不匹配的 sourceHash 都失败并清除旧产物", async t => {
  for (const declaredHash of [undefined, "", "not-a-sha", "A".repeat(64), "0".repeat(64)]) {
    const fixture = await createValidFixture(t);
    await Promise.all(OUTPUT_FILES.map(filename => writeJson(fixture.directory, filename, { ok: true })));
    const source = { ...fixture.source };
    if (declaredHash === undefined) delete source.sourceHash;
    else source.sourceHash = declaredHash;
    await writeJson(fixture.directory, "source.json", source);

    const report = await validatePackage(fixture.directory);

    assert.equal(report.ok, false, String(declaredHash));
    assert.equal(hasError(report, "INVALID_SOURCE_HASH") || hasError(report, "SOURCE_HASH_MISMATCH"), true);
    await assertNoFinalArtifacts(fixture.directory);
  }
});

test("Markdown 表格被作为普通段落记录时失败", async t => {
  const fixture = await createValidFixture(t);
  const rawTable = fixture.source.body.split("\n\n")[1];
  fixture.pages[0].blocks.push({ type: "paragraph", markdown: rawTable, renderedText: rawTable });
  await writeJson(fixture.directory, "pages.json", fixture.pages);

  const report = await validatePackage(fixture.directory);

  assert.equal(report.ok, false);
  assert.equal(hasError(report, "RAW_MARKDOWN_TABLE_PARAGRAPH"), true);
});

test("按 tableIndex,rowIndex,sourceColumnIndex 检出丢失单元格", async t => {
  const fixture = await createValidFixture(t);
  fixture.pages[2].blocks[1].rows[0].pop();
  await writeJson(fixture.directory, "pages.json", fixture.pages);

  const report = await validatePackage(fixture.directory);

  assert.equal(report.ok, false);
  assert.equal(hasError(report, "LOST_TABLE_CELL"), true);
});

test("非键列单元格重复时失败，而宽表首列的结构性重复通过", async t => {
  const fixture = await createValidFixture(t);
  fixture.pages[2].blocks.push(tableBlock(
    [0, 4],
    [fixture.tableHeader[0], fixture.tableHeader[4]],
    [[fixture.tableRows[0][0], fixture.tableRows[0][4]]],
  ));
  await writeJson(fixture.directory, "pages.json", fixture.pages);

  const report = await validatePackage(fixture.directory);

  assert.equal(report.ok, false);
  assert.equal(hasError(report, "DUPLICATED_TABLE_CELL"), true);
});

test("跨页表格缺少续页表头时失败", async t => {
  const fixture = await createValidFixture(t);
  fixture.pages[2].blocks[0].header = [];
  await writeJson(fixture.directory, "pages.json", fixture.pages);

  const report = await validatePackage(fixture.directory);

  assert.equal(report.ok, false);
  assert.equal(hasError(report, "MISSING_REPEATED_TABLE_HEADER"), true);
});

test("独立依据最终浏览器几何重新计算溢出", async t => {
  const fixture = await createValidFixture(t);
  fixture.stats.results[1].overflow = false;
  fixture.stats.results[1].contentBottom = 1400;
  fixture.stats.overflowCount = 0;
  await writeJson(fixture.directory, "render-stats.json", fixture.stats);

  const report = await validatePackage(fixture.directory);

  assert.equal(report.ok, false);
  assert.equal(report.overflowCount, 1);
  assert.equal(hasError(report, "RENDER_OVERFLOW"), true);
});

test("多页长图的封面、正文和尾页低于密度下限时失败", async t => {
  const fixture = await createValidFixture(t);
  const longOpening = "这是一段用于触发长文密度校验的原文，必须在分页和最终 HTML 中逐字保留。".repeat(40);
  fixture.source.body = fixture.source.body.replace("开场段落必须逐字保留。", longOpening);
  fixture.source.sourceHash = sourceHash(fixture.source);
  fixture.pages[0].blocks[0].markdown = longOpening;
  fixture.pages[0].blocks[0].renderedText = longOpening;
  fixture.stats.sourceHash = fixture.source.sourceHash;
  fixture.stats.results[0].contentBottom = 700;
  fixture.stats.results[1].contentBottom = 800;
  fixture.stats.results[2].contentBottom = 650;
  await Promise.all([
    writeJson(fixture.directory, "source.json", fixture.source),
    writeJson(fixture.directory, "pages.json", fixture.pages),
    writeJson(fixture.directory, "render-stats.json", fixture.stats),
    writeFinalHtml(fixture.directory, fixture.source, fixture.pages),
  ]);

  const report = await validatePackage(fixture.directory);

  assert.equal(report.ok, false);
  assert.equal(hasError(report, "UNDERFILLED_PAGE"), true);
});

test("语义原子约束下的全局最优分页使用可发布密度下限", async t => {
  const fixture = await createValidFixture(t);
  const longOpening = "这是一段用于触发长文密度校验的原文，必须在分页和最终 HTML 中逐字保留。".repeat(40);
  fixture.source.body = fixture.source.body.replace("开场段落必须逐字保留。", longOpening);
  fixture.source.sourceHash = sourceHash(fixture.source);
  fixture.pages[0].blocks[0].markdown = longOpening;
  fixture.pages[0].blocks[0].renderedText = longOpening;
  fixture.stats.sourceHash = fixture.source.sourceHash;
  const acceptedRatios = [0.78, 0.72, 0.67];
  fixture.stats.results.forEach((result, index) => {
    result.contentHeight = Math.round(result.availableHeight * acceptedRatios[index]);
    result.contentBottom = result.contentTop + result.contentHeight;
    result.fillRatio = result.contentHeight / result.availableHeight;
  });
  await Promise.all([
    writeJson(fixture.directory, "source.json", fixture.source),
    writeJson(fixture.directory, "pages.json", fixture.pages),
    writeJson(fixture.directory, "render-stats.json", fixture.stats),
    writeFinalHtml(fixture.directory, fixture.source, fixture.pages),
  ]);

  const report = await validatePackage(fixture.directory);

  assert.equal(hasError(report, "UNDERFILLED_PAGE"), false);
});

test("渲染几何必须完整、有限且使用验证器固定的 1376 底线", async t => {
  const cases = [
    stats => { stats.results[1].contentBottomLimit = 999999; stats.results[1].contentBottom = 5000; },
    stats => { delete stats.results[1].contentTop; },
    stats => { delete stats.results[1].tableRows[0].bottom; },
  ];
  for (const mutate of cases) {
    const fixture = await createValidFixture(t);
    mutate(fixture.stats);
    await writeJson(fixture.directory, "render-stats.json", fixture.stats);
    const report = await validatePackage(fixture.directory);
    assert.equal(report.ok, false);
    assert.equal(hasError(report, "INVALID_RENDER_GEOMETRY"), true);
  }
});

test("多出的未声明编号图片失败", async t => {
  const fixture = await createValidFixture(t);
  await fs.writeFile(path.join(fixture.directory, "04.png"), validPng(4));

  const report = await validatePackage(fixture.directory);

  assert.equal(report.ok, false);
  assert.equal(hasError(report, "EXTRA_UNDECLARED_PAGE_IMAGE"), true);
});

test("PNG 内容被替换后由重新计算的哈希检出", async t => {
  const fixture = await createValidFixture(t);
  const changed = validPng(9);
  await fs.writeFile(path.join(fixture.directory, "02.png"), changed);

  const report = await validatePackage(fixture.directory);

  assert.equal(report.ok, false);
  assert.equal(hasError(report, "PNG_HASH_MISMATCH"), true);
});

test("截断或 CRC 损坏的 PNG 即使声明哈希更新也失败", async t => {
  const fixture = await createValidFixture(t);
  const broken = validPng(9).subarray(0, -8);
  await fs.writeFile(path.join(fixture.directory, "02.png"), broken);
  fixture.stats.results[1].sha256 = crypto.createHash("sha256").update(broken).digest("hex");
  await writeJson(fixture.directory, "render-stats.json", fixture.stats);

  const report = await validatePackage(fixture.directory);

  assert.equal(report.ok, false);
  assert.equal(hasError(report, "INVALID_PNG_STRUCTURE"), true);
});

test("最终 HTML 的标题与表格位置是独立于 pages.json 的语义证据", async t => {
  const fixture = await createValidFixture(t);
  const changedSource = { ...fixture.source, title: "已更新但未重新渲染的标题" };
  changedSource.sourceHash = sourceHash(changedSource);
  fixture.stats.sourceHash = changedSource.sourceHash;
  await writeJson(fixture.directory, "source.json", changedSource);
  await writeJson(fixture.directory, "render-stats.json", fixture.stats);
  const report = await validatePackage(fixture.directory);
  assert.equal(report.ok, false);
  assert.equal(hasError(report, "FINAL_HTML_SEMANTIC_MISMATCH"), true);
});

test("最终图片 HTML 仍暴露 Markdown 加粗标记时失败", async t => {
  const fixture = await createValidFixture(t);
  const pageOnePath = path.join(fixture.directory, "_render-work", "page-01.html");
  const html = await fs.readFile(pageOnePath, "utf8");
  await fs.writeFile(pageOnePath, html.replace(
    "开场段落必须逐字保留。",
    "**开场段落必须逐字保留。**",
  ));

  const report = await validatePackage(fixture.directory);

  assert.equal(report.ok, false);
  assert.equal(hasError(report, "RAW_MARKDOWN_MARKER"), true);
});

test("最终 HTML 的表格与段落或两张表互换顺序时失败", async t => {
  const fixture = await createValidFixture(t);
  const pageTwoPath = path.join(fixture.directory, "_render-work", "page-02.html");
  const original = await fs.readFile(pageTwoPath, "utf8");
  await fs.writeFile(pageTwoPath, original.replace(
    'data-render-table-group-index="0"',
    'data-render-table-group-index="1"',
  ));
  const report = await validatePackage(fixture.directory);
  assert.equal(report.ok, false);
  assert.equal(hasError(report, "FINAL_HTML_SEMANTIC_MISMATCH"), true);
});

test("表格片段不可只有表头或在同页重复", async t => {
  const fixture = await createValidFixture(t);
  fixture.pages[2].blocks.push(tableBlock([0, 4], [fixture.tableHeader[0], fixture.tableHeader[4]], [], 0, 1));
  await writeJson(fixture.directory, "pages.json", fixture.pages);
  const report = await validatePackage(fixture.directory);
  assert.equal(report.ok, false);
  assert.equal(hasError(report, "HEADER_ONLY_TABLE_FRAGMENT"), true);
  assert.equal(hasError(report, "DUPLICATED_TABLE_GROUP_ON_PAGE"), true);
});

test("有效包通过并只在重算完成后写出三个最终产物", async t => {
  const fixture = await createValidFixture(t);
  const originalSource = await fs.readFile(path.join(fixture.directory, "source.json"));
  const originalCopy = await fs.readFile(path.join(fixture.directory, "copy.json"));

  const valid = await validatePackage(fixture.directory);

  assert.equal(valid.ok, true);
  assert.equal(valid.exactText, true);
  assert.equal(valid.tableCount, 1);
  assert.equal(valid.tableRowCount, 2);
  assert.equal(valid.repeatedTableHeaderCount, 1);
  assert.deepEqual(valid.filenames, ["01.png", "02.png", "03.png"]);
  assert.deepEqual(valid.errors, []);
  const validation = await readJson(fixture.directory, "validation.json");
  const manifest = await readJson(fixture.directory, "manifest.json");
  const finalVerification = await readJson(fixture.directory, "final-verification.json");
  assert.equal(validation.exact_text, true);
  assert.equal(manifest.sourceHash, fixture.source.sourceHash);
  assert.equal(manifest.recordId, fixture.source.platformRecordId);
  assert.equal(manifest.contentId, fixture.source.platformContentId);
  assert.deepEqual(manifest.filenames, valid.filenames);
  assert.equal(finalVerification.ok, true);
  assert.equal(finalVerification.localPreview, true);
  assert.equal(finalVerification.publicPublishTriggered, false);
  assert.deepEqual(await fs.readFile(path.join(fixture.directory, "source.json")), originalSource);
  assert.deepEqual(await fs.readFile(path.join(fixture.directory, "copy.json")), originalCopy);
});

test("渲染器完成真实截图后调用独立验证并写出最终产物", async t => {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), "xhs-validator-render-test-"));
  t.after(() => fs.rm(directory, { recursive: true, force: true }));
  const source = {
    title: "渲染完成后必须独立验收",
    body: "这段原文进入真实截图，随后才能生成最终验证产物。",
  };
  source.sourceHash = sourceHash(source);
  await writeJson(directory, "source.json", source);

  await renderPackage(directory);

  const finalVerification = await readJson(directory, "final-verification.json");
  assert.equal(finalVerification.ok, true);
  assert.equal(finalVerification.sourceHash, source.sourceHash);
  for (const filename of OUTPUT_FILES) await fs.access(path.join(directory, filename));
});
