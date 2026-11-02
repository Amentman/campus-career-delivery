import crypto from "node:crypto";
import { spawn } from "node:child_process";
import fs from "node:fs";
import fsp from "node:fs/promises";
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

import {
  paginateMeasuredBlocks,
  parseMarkdownBlocks,
  splitParagraphsIntoSentences,
  splitWideTables,
} from "./layout.mjs";
import { clearValidationArtifacts, validatePackage } from "./validate-package.mjs";

const PAGE_WIDTH = 1080;
const PAGE_HEIGHT = 1440;
const CONTENT_BOTTOM_LIMIT = 1376;
const COVER_TOP = 145;
const BODY_TOP = 143;
const CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const TOOLBAR_CONTROLS = ["back", "undo", "redo", "share", "more"];
const require = createRequire(import.meta.url);

const memoCss = `
:root{--memo-paper:#fff;--memo-ink:#4a4a4a;--memo-strong:#444;--memo-gold:#d0ac2b;--memo-gray:#c5c5c5;--memo-line:#d7d7d7;--memo-font:"PingFang SC","Hiragino Sans GB","Noto Sans CJK SC","Microsoft YaHei",Arial,sans-serif}
*{box-sizing:border-box}html,body{margin:0;width:1080px;height:1440px;overflow:hidden;background:var(--memo-paper);color:var(--memo-ink);font-family:var(--memo-font);letter-spacing:0;-webkit-font-smoothing:antialiased;font-synthesis:none}
.memo-page{position:relative;width:1080px;height:1440px;overflow:hidden;background:#fff}
.memo-toolbar{position:absolute;top:29px;left:31px;right:52px;height:76px;display:flex;align-items:center;justify-content:space-between}
.memo-back{display:flex;align-items:center;width:117px;height:40px;color:var(--memo-gold);font-size:39px;font-weight:400;line-height:1}
.memo-back-icon{flex:0 0 31px;width:31px;height:40px;margin-right:8px}
.memo-back-label{flex:none;white-space:nowrap}
.memo-tools{display:flex;align-items:center;gap:0;color:var(--memo-gold)}
.memo-tool{display:inline-flex;align-items:center;justify-content:center;width:56px;height:56px;font-family:Arial,sans-serif}
.memo-icon{display:block;overflow:visible;fill:none;stroke:currentColor;stroke-width:4;stroke-linecap:round;stroke-linejoin:round}
.memo-arrow-icon,.memo-more-icon{width:56px;height:56px}
.memo-redo{margin-left:60px;color:var(--memo-gray)}
.memo-share{margin-left:88px;width:46px;height:52px}
.memo-share-icon{width:46px;height:52px}
.memo-more{margin-left:88px}
.memo-article{position:absolute;left:89px;right:73px}
.memo-cover .memo-article{top:145px}.memo-body-page .memo-article{top:143px}
.memo-title{margin:0 0 var(--memo-cover-title-gap,104px);max-width:900px;color:var(--memo-ink);font-size:76px;line-height:1.17;font-weight:750;letter-spacing:-1px;overflow-wrap:anywhere}
.memo-body{font-size:36px;line-height:1.48;color:var(--memo-ink);font-weight:400}
.memo-paragraph{margin:0 0 24px;overflow-wrap:break-word;white-space:normal}
.memo-paragraph:last-child{margin-bottom:0}
.memo-heading{margin:49px 0 55px;color:var(--memo-strong);font-size:49px;line-height:1.2;font-weight:800;letter-spacing:-1px;overflow-wrap:break-word}
.memo-heading:first-child{margin-top:0}
.memo-list{margin:0;padding:0;list-style:none}
.memo-list li{position:relative;margin:0 0 12px;padding-left:34px;overflow-wrap:break-word}
.memo-list li[data-list-last="true"]{margin-bottom:31px}.memo-list li::before{content:"–";position:absolute;left:0;top:0}
.memo-body strong{color:var(--memo-strong);font-weight:750;text-decoration:underline;text-decoration-thickness:3px;text-underline-offset:8px}
.memo-table-block{width:100%;margin:0}
.memo-table{width:100%;margin:0 0 30px;border-collapse:collapse;table-layout:fixed;color:var(--memo-ink);font-size:29px;line-height:1.42}
.memo-table,.memo-table th,.memo-table td{background:#fff}
.memo-table th,.memo-table td{padding:16px 14px;border:1px solid var(--memo-line);vertical-align:top;overflow-wrap:anywhere;word-break:break-word}
.memo-table th{color:var(--memo-strong);font-weight:750;text-align:left}
.memo-table [data-align="center"]{text-align:center}.memo-table [data-align="right"]{text-align:right}
.memo-tail-balanced .memo-body>:not(:last-child){padding-bottom:var(--memo-tail-block-gap,0)}
`;

function loadPlaywright() {
  const candidates = [
    "playwright",
    path.join(os.homedir(), ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright"),
  ];
  for (const candidate of candidates) {
    try {
      return require(candidate);
    } catch {}
  }
  throw new Error("Playwright is required to measure and render the memo package.");
}

export function chromeLaunchArguments(profileDirectory) {
  return [
    "--headless",
    "--no-sandbox",
    "--disable-gpu",
    "--disable-background-networking",
    "--disable-component-update",
    "--disable-default-apps",
    "--disable-extensions",
    "--disable-sync",
    "--metrics-recording-only",
    "--no-first-run",
    "--no-default-browser-check",
    "--password-store=basic",
    "--use-mock-keychain",
    "--hide-scrollbars",
    "--remote-debugging-port=0",
    `--user-data-dir=${profileDirectory}`,
    "about:blank",
  ];
}

async function launchChrome(profileDirectory, chromePath) {
  const child = spawn(chromePath, chromeLaunchArguments(profileDirectory), {
    detached: true,
    stdio: "ignore",
  });
  let launchError;
  child.once("error", error => { launchError = error; });
  const activePortFile = path.join(profileDirectory, "DevToolsActivePort");

  for (let attempt = 0; attempt < 150; attempt += 1) {
    if (launchError) throw launchError;
    try {
      const [port, browserPath] = fs.readFileSync(activePortFile, "utf8").trim().split(/\r?\n/);
      if (/^\d+$/.test(port) && browserPath?.startsWith("/devtools/browser/")) {
        return { groupId: child.pid, endpoint: `ws://127.0.0.1:${port}${browserPath}` };
      }
    } catch {}
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  await stopChrome(child.pid);
  throw new Error("Chrome debugging endpoint did not become available.");
}

function chromeGroupExists(groupId) {
  try {
    process.kill(-groupId, 0);
    return true;
  } catch {
    return false;
  }
}

async function stopChrome(groupId) {
  if (!groupId || !chromeGroupExists(groupId)) return;
  try { process.kill(-groupId, "SIGTERM"); } catch {}
  for (let attempt = 0; attempt < 10; attempt += 1) {
    await new Promise(resolve => setTimeout(resolve, 100));
    if (!chromeGroupExists(groupId)) return;
  }
  try { process.kill(-groupId, "SIGKILL"); } catch {}
  await new Promise(resolve => setTimeout(resolve, 100));
}

async function openBrowser(chromePath) {
  if (!fs.existsSync(chromePath)) throw new Error(`Google Chrome is unavailable at ${chromePath}.`);
  const profileDirectory = await fsp.mkdtemp(path.join(os.tmpdir(), "xhs-image-renderer-browser-"));
  const chrome = await launchChrome(profileDirectory, chromePath);
  let browser;
  try {
    const { chromium } = loadPlaywright();
    browser = await chromium.connectOverCDP(chrome.endpoint, { timeout: 15_000 });
    return {
      browser,
      context: browser.contexts()[0],
      async close() {
        await browser.close().catch(() => {});
        await stopChrome(chrome.groupId);
        await fsp.rm(profileDirectory, { recursive: true, force: true, maxRetries: 5, retryDelay: 100 });
      },
    };
  } catch (error) {
    if (browser) await browser.close().catch(() => {});
    await stopChrome(chrome.groupId);
    await fsp.rm(profileDirectory, { recursive: true, force: true, maxRetries: 5, retryDelay: 100 });
    throw error;
  }
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function renderInline(value) {
  return escapeHtml(value)
    .replace(/\*\*(.+?)\*\*/gs, "<strong>$1</strong>")
    .replaceAll("\n", "<br>");
}

function expandListItems(blocks) {
  let sourceListIndex = 0;
  return blocks.flatMap(block => {
    if (block.type !== "list") return [block];
    const markdownLines = block.markdown.split("\n");
    const listIndex = sourceListIndex;
    sourceListIndex += 1;
    return block.items.map((item, itemIndex) => ({
      type: "list-item",
      sourceListIndex: listIndex,
      sourceItemIndex: itemIndex,
      item,
      isLastItem: itemIndex === block.items.length - 1,
      markdown: markdownLines[itemIndex],
      renderedText: item,
    }));
  });
}

function expandSemanticUnits(blocks) {
  return expandListItems(splitParagraphsIntoSentences(blocks)).flatMap(block => {
    if (block.type !== "table") return [block];
    return block.rows.map((values, sourceTableRowIndex) => ({
      type: "table-row-unit",
      table: block,
      values,
      sourceTableRowIndex,
    }));
  });
}

function memoToolbar() {
  return `<header class="memo-toolbar" aria-label="备忘录工具栏">
    <span class="memo-back" data-memo-control="back"><svg class="memo-icon memo-back-icon" data-memo-icon="back" viewBox="0 0 31 40" aria-hidden="true"><path d="M24 4L8 20L24 36"></path></svg><span class="memo-back-label">返回</span></span>
    <span class="memo-tools">
      <span class="memo-tool memo-undo" data-memo-control="undo" aria-label="撤销"><svg class="memo-icon memo-arrow-icon" data-memo-icon="undo" viewBox="0 0 56 56" aria-hidden="true"><circle cx="28" cy="28" r="24"></circle><path d="M31 19H19M19 19L25 13M19 19L25 25M19 19C30 16 39 23 39 32C39 39 34 44 27 45"></path></svg></span>
      <span class="memo-tool memo-redo" data-memo-control="redo" aria-label="重做"><svg class="memo-icon memo-arrow-icon" data-memo-icon="redo" viewBox="0 0 56 56" aria-hidden="true"><circle cx="28" cy="28" r="24"></circle><path d="M25 19H37M37 19L31 13M37 19L31 25M37 19C26 16 17 23 17 32C17 39 22 44 29 45"></path></svg></span>
      <span class="memo-tool memo-share" data-memo-control="share" aria-label="分享"><svg class="memo-icon memo-share-icon" data-memo-icon="share" viewBox="0 0 46 52" aria-hidden="true"><path d="M14 18H6V48H40V18H32"></path><path d="M23 31V3M13 13L23 3L33 13"></path></svg></span>
      <span class="memo-tool memo-more" data-memo-control="more" aria-label="更多"><svg class="memo-icon memo-more-icon" data-memo-icon="more" viewBox="0 0 56 56" aria-hidden="true"><circle cx="28" cy="28" r="24"></circle><circle cx="19" cy="28" r="2.4" fill="currentColor" stroke="none"></circle><circle cx="28" cy="28" r="2.4" fill="currentColor" stroke="none"></circle><circle cx="37" cy="28" r="2.4" fill="currentColor" stroke="none"></circle></svg></span>
    </span>
  </header>`;
}

function renderTable(header, alignments, rows, attributes = "") {
  const headings = header.map((value, index) =>
    `<th data-align="${alignments[index] || "left"}">${renderInline(value)}</th>`).join("");
  const bodyRows = rows.map((values, rowIndex) =>
    `<tr data-table-row="${rowIndex}">${values.map((value, index) =>
      `<td data-align="${alignments[index] || "left"}">${renderInline(value)}</td>`).join("")}</tr>`).join("");
  return `<div class="memo-table-block" ${attributes}><table class="memo-table"><thead><tr>${headings}</tr></thead><tbody>${bodyRows}</tbody></table></div>`;
}

function renderContentBlock(block, attributes = "") {
  if (block.type === "paragraph") {
    return `<p class="memo-paragraph" ${attributes}>${renderInline(block.renderedText)}</p>`;
  }
  if (block.type === "heading") {
    return `<h2 class="memo-heading" ${attributes}>${renderInline(block.renderedText)}</h2>`;
  }
  if (block.type === "list") {
    return `<ul class="memo-list" ${attributes}>${block.items.map((item, index) =>
      `<li${block.lastItemFlags?.[index] ? ` data-list-last="true"` : ""}>${renderInline(item)}</li>`).join("")}</ul>`;
  }
  if (block.type === "table") {
    return renderTable(block.header, block.alignments, block.rows, attributes);
  }
  throw new Error(`Unsupported render block: ${block.type}`);
}

function measurementHtml(title, blocks) {
  const markup = blocks.map((block, index) => block.type === "list-item"
    ? `<ul class="memo-list"><li data-measure-block="${index}"${block.isLastItem ? ` data-list-last="true"` : ""}>${renderInline(block.item)}</li></ul>`
    : renderContentBlock(block, `data-measure-block="${index}"`)).join("");
  return `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><style>${memoCss}</style></head><body>
    <main class="memo-page memo-cover"><article class="memo-article">
      <h1 class="memo-title" data-measure-title>${renderInline(title)}</h1>
      <section class="memo-body">${markup}</section>
    </article></main></body></html>`;
}

async function measureLayout(context, title, blocks) {
  const page = await context.newPage();
  try {
    await page.setViewportSize({ width: PAGE_WIDTH, height: PAGE_HEIGHT });
    await page.setContent(measurementHtml(title, blocks), { waitUntil: "load", timeout: 15_000 });
    await page.evaluate(() => document.fonts.ready);
    return await page.evaluate(() => {
      const outerHeight = element => {
        const style = getComputedStyle(element);
        return Math.ceil(element.getBoundingClientRect().height
          + Number.parseFloat(style.marginTop || "0")
          + Number.parseFloat(style.marginBottom || "0"));
      };
      const titleHeight = outerHeight(document.querySelector("[data-measure-title]"));
      const blocks = [...document.querySelectorAll("[data-measure-block]")].map(element => {
        const table = element.querySelector("table");
        if (!table) return { height: outerHeight(element) };
        const tableStyle = getComputedStyle(table);
        return {
          headerHeight: Math.ceil(table.tHead.getBoundingClientRect().height
            + Number.parseFloat(tableStyle.marginTop || "0")
            + Number.parseFloat(tableStyle.marginBottom || "0") + 1),
          rowHeights: [...table.tBodies[0].rows].map(row => Math.ceil(row.getBoundingClientRect().height + 1)),
        };
      });
      return { titleHeight, blocks };
    });
  } finally {
    await page.close();
  }
}

function createMeasureFunction(blocks, measured) {
  const tableMeasurements = new Map();
  blocks.forEach((block, index) => {
    if (block.type !== "table") return;
    const rows = new Map(block.rows.map((row, rowIndex) => [row, measured.blocks[index].rowHeights[rowIndex]]));
    tableMeasurements.set(block, { header: measured.blocks[index].headerHeight, rows });
  });
  return block => {
    if (block.type === "table-header") return tableMeasurements.get(block.table).header;
    if (block.type === "table-row") return tableMeasurements.get(block.table).rows.get(block.values);
    const index = blocks.indexOf(block);
    return measured.blocks[index].height;
  };
}

function tableMarkdown(table) {
  const delimiter = table.alignments.map(alignment => alignment === "center" ? ":---:" : alignment === "right" ? "---:" : "---");
  return [table.header, delimiter, ...table.rows]
    .map(row => `| ${row.map(value => String(value).replaceAll("|", "\\|")).join(" | ")} |`)
    .join("\n");
}

function materializePage(layoutPage, index) {
  const blocks = [];
  for (const unit of layoutPage.blocks) {
    if (unit.type === "paragraph-sentence") {
      let current = blocks.at(-1);
      if (!current || current.type !== "paragraph" || current.sourceParagraphIndex !== unit.sourceParagraphIndex) {
        current = {
          type: "paragraph",
          sourceParagraphIndex: unit.sourceParagraphIndex,
          sourceSentenceIndexes: [],
          markdown: "",
          renderedText: "",
        };
        blocks.push(current);
      }
      current.sourceSentenceIndexes.push(unit.sourceSentenceIndex);
      current.markdown += unit.markdown;
      current.renderedText += unit.renderedText;
      continue;
    }
    if (unit.type === "list-item") {
      let current = blocks.at(-1);
      if (!current || current.type !== "list" || current.sourceListIndex !== unit.sourceListIndex) {
        current = {
          type: "list",
          sourceListIndex: unit.sourceListIndex,
          sourceItemIndexes: [],
          items: [],
          lastItemFlags: [],
          markdownLines: [],
        };
        blocks.push(current);
      }
      current.sourceItemIndexes.push(unit.sourceItemIndex);
      current.items.push(unit.item);
      current.lastItemFlags.push(unit.isLastItem);
      current.markdownLines.push(unit.markdown);
      continue;
    }
    if (unit.type === "table-row-unit") {
      let current = blocks.at(-1);
      if (!current || current.type !== "table"
        || current.tableIndex !== unit.table.tableIndex
        || current.tableGroupIndex !== unit.table.tableGroupIndex) {
        current = {
          type: "table",
          tableIndex: unit.table.tableIndex,
          tableGroupIndex: unit.table.tableGroupIndex,
          header: unit.table.header,
          alignments: unit.table.alignments,
          rows: [],
          sourceTableRowIndexes: [],
          sourceColumnIndexes: unit.table.sourceColumnIndexes,
          repeatedKeyColumn: unit.table.repeatedKeyColumn,
        };
        blocks.push(current);
      }
      current.rows.push(unit.values);
      current.sourceTableRowIndexes.push(unit.sourceTableRowIndex);
      continue;
    }
    if (unit.type === "table-header") {
      blocks.push({
        type: "table",
        tableIndex: unit.table.tableIndex,
        tableGroupIndex: unit.table.tableGroupIndex,
        header: unit.header,
        alignments: unit.alignments,
        rows: [],
        sourceColumnIndexes: unit.table.sourceColumnIndexes,
        repeatedKeyColumn: unit.table.repeatedKeyColumn,
      });
      continue;
    }
    if (unit.type === "table-row") {
      const current = blocks.at(-1);
      if (!current || current.type !== "table") throw new Error("Table row is missing its table header.");
      current.rows.push(unit.values);
      continue;
    }
    blocks.push({ ...unit });
  }

  for (const block of blocks) {
    if (block.type !== "list") continue;
    block.markdown = block.markdownLines.join("\n");
    block.renderedText = block.items.join("\n");
    delete block.markdownLines;
  }

  const sourceMarkdown = blocks.map(block => block.type === "table" ? tableMarkdown(block) : block.markdown).join("\n\n");
  const renderedText = blocks.map(block => block.type === "table"
    ? [block.header, ...block.rows].map(row => row.join(" | ")).join("\n")
    : block.renderedText).join("\n\n");
  return {
    page: index + 1,
    kind: index === 0 ? "cover" : "body",
    ...(index === 0 && Number.isFinite(layoutPage.coverTitleGap)
      ? { coverTitleGap: layoutPage.coverTitleGap }
      : {}),
    ...(Number.isFinite(layoutPage.tailBlockGap) && layoutPage.tailBlockGap > 0
      ? { tailBlockGap: layoutPage.tailBlockGap }
      : {}),
    source_markdown: sourceMarkdown,
    rendered_text: renderedText,
    char_count: renderedText.replace(/\s/g, "").length,
    blocks,
  };
}

async function measurePageUnits(probe, units, pageIndex, title, options = {}) {
  const semanticPage = materializePage({ blocks: units, ...options }, pageIndex);
  await probe.setContent(renderPageHtml(semanticPage, title), { waitUntil: "load", timeout: 15_000 });
  await probe.evaluate(() => document.fonts.ready);
  return probe.evaluate(limit => {
    const article = document.querySelector(".memo-article");
    const rect = article.getBoundingClientRect();
    return {
      contentTop: rect.top,
      contentBottom: rect.bottom,
      contentHeight: rect.height,
      availableHeight: limit - rect.top,
      fillRatio: rect.height / (limit - rect.top),
      overflow: rect.bottom > limit + 0.5 || article.scrollWidth > article.clientWidth,
    };
  }, CONTENT_BOTTOM_LIMIT);
}

async function paginateSemanticUnits(context, title, units) {
  const probe = await context.newPage();
  try {
    await probe.setViewportSize({ width: PAGE_WIDTH, height: PAGE_HEIGHT });
    const pages = [{ blocks: [], geometry: null }];
    for (const unit of units) {
      const current = pages.at(-1);
      const candidate = [...current.blocks, unit];
      const candidateGeometry = await measurePageUnits(probe, candidate, pages.length - 1, title);
      if (!candidateGeometry.overflow) {
        current.blocks = candidate;
        current.geometry = candidateGeometry;
        continue;
      }

      if (current.blocks.length === 0) {
        const error = new Error(pages.length === 1
          ? "The first source sentence does not fit below the cover title."
          : "A semantic unit exceeds the body page capacity.");
        error.code = pages.length === 1 ? "FIRST_BLOCK_DOES_NOT_FIT_COVER"
          : unit.type === "table-row-unit" ? "ROW_TOO_TALL" : "BLOCK_TOO_TALL";
        throw error;
      }

      const carry = current.blocks.at(-1)?.type === "heading" && current.blocks.length > 1
        ? [current.blocks.pop()]
        : [];
      if (carry.length > 0) {
        current.geometry = await measurePageUnits(probe, current.blocks, pages.length - 1, title);
      }
      const next = { blocks: [...carry, unit], geometry: null };
      next.geometry = await measurePageUnits(probe, next.blocks, pages.length, title);
      if (next.geometry.overflow) {
        const error = new Error("A semantic unit exceeds the body page capacity.");
        error.code = unit.type === "table-row-unit" ? "ROW_TOO_TALL" : "BLOCK_TOO_TALL";
        throw error;
      }
      pages.push(next);
    }
    await rebalanceAllPages(probe, pages, title);
    await balanceTailWhitespace(probe, pages, title);
    await balanceCoverWhitespace(probe, pages, title);
    return pages;
  } finally {
    await probe.close();
  }
}

async function balanceCoverWhitespace(probe, pages, title) {
  const cover = pages[0];
  const minimumFill = 0.78;
  const targetFill = 0.785;
  if (!cover || cover.geometry.overflow || cover.geometry.fillRatio >= minimumFill) return;

  const defaultGap = 104;
  const neededPixels = Math.ceil((targetFill - cover.geometry.fillRatio) * cover.geometry.availableHeight);
  const coverTitleGap = Math.min(220, defaultGap + Math.max(0, neededPixels));
  const geometry = await measurePageUnits(probe, cover.blocks, 0, title, { coverTitleGap });
  if (geometry.overflow || geometry.fillRatio <= cover.geometry.fillRatio) return;
  cover.coverTitleGap = coverTitleGap;
  cover.geometry = geometry;
}

async function balanceTailWhitespace(probe, pages, title) {
  const pageIndex = pages.length - 1;
  const tail = pages[pageIndex];
  const minimumFill = 0.67;
  const targetFill = 0.675;
  if (pageIndex < 1 || !tail || tail.geometry.overflow || tail.geometry.fillRatio >= minimumFill) return;

  const materialized = materializePage(tail, pageIndex);
  const gapCount = Math.max(0, materialized.blocks.length - 1);
  if (gapCount === 0) return;
  const neededPixels = Math.ceil((targetFill - tail.geometry.fillRatio) * tail.geometry.availableHeight);
  const tailBlockGap = Math.min(24, Math.max(0, Math.ceil(neededPixels / gapCount)));
  if (!tailBlockGap) return;

  const geometry = await measurePageUnits(probe, tail.blocks, pageIndex, title, { tailBlockGap });
  if (geometry.overflow || geometry.fillRatio + 0.005 < minimumFill) return;
  tail.tailBlockGap = tailBlockGap;
  tail.geometry = geometry;
}

async function rebalanceAllPages(probe, pages, title) {
  const epsilon = 0.005;
  const pageCount = pages.length;
  const minimumFill = pageIndex => pageIndex === 0 || pageIndex === pageCount - 1 ? 0.78 : 0.82;
  if (pageCount < 2 || pages.every((page, pageIndex) =>
    page.geometry.fillRatio + epsilon >= minimumFill(pageIndex))) return;

  const units = pages.flatMap(page => page.blocks);
  const averageFill = pages.reduce((sum, page) => sum + page.geometry.fillRatio, 0) / pageCount;
  const targetFill = Math.max(0.84, Math.min(0.94, averageFill));
  const geometryCache = new Map();
  const layoutCache = new Map();

  async function measureRange(start, end, pageIndex) {
    const pageKind = pageIndex === 0 ? "cover" : "body";
    const key = `${pageKind}:${start}:${end}`;
    if (!geometryCache.has(key)) {
      geometryCache.set(key, measurePageUnits(probe, units.slice(start, end), pageIndex, title));
    }
    return geometryCache.get(key);
  }

  function scorePage(geometry, pageIndex) {
    const minimum = minimumFill(pageIndex);
    return {
      minimumRatio: geometry.fillRatio / minimum,
      deficit: Math.max(0, minimum - geometry.fillRatio),
      raggedness: (targetFill - geometry.fillRatio) ** 2,
    };
  }

  function combineScores(pageScore, tailScore) {
    return {
      minimumRatio: Math.min(pageScore.minimumRatio, tailScore.minimumRatio),
      deficit: pageScore.deficit + tailScore.deficit,
      raggedness: pageScore.raggedness + tailScore.raggedness,
    };
  }

  function isBetterScore(candidate, current) {
    if (!current) return true;
    if (Math.abs(candidate.minimumRatio - current.minimumRatio) > 0.0001) {
      return candidate.minimumRatio > current.minimumRatio;
    }
    if (Math.abs(candidate.deficit - current.deficit) > 0.0001) {
      return candidate.deficit < current.deficit;
    }
    return candidate.raggedness < current.raggedness;
  }

  async function findLayout(pageIndex, start) {
    const stateKey = `${pageIndex}:${start}`;
    if (layoutCache.has(stateKey)) return layoutCache.get(stateKey);
    const lastPage = pageIndex === pageCount - 1;
    if (lastPage) {
      const geometry = await measureRange(start, units.length, pageIndex);
      const result = geometry.overflow ? null : {
        pages: [{ blocks: units.slice(start), geometry }],
        score: scorePage(geometry, pageIndex),
      };
      layoutCache.set(stateKey, result);
      return result;
    }

    const remainingPages = pageCount - pageIndex - 1;
    const latestEnd = units.length - remainingPages;
    const candidates = [];
    for (let end = start + 1; end <= latestEnd; end += 1) {
      const geometry = await measureRange(start, end, pageIndex);
      if (geometry.overflow) break;
      if (units[end - 1]?.type === "heading") continue;
      candidates.push({
        end,
        geometry,
        score: Math.abs(geometry.fillRatio - targetFill),
      });
    }
    candidates.sort((left, right) => left.score - right.score || right.end - left.end);

    let best = null;
    for (const candidate of candidates) {
      const tail = await findLayout(pageIndex + 1, candidate.end);
      if (tail) {
        const score = combineScores(scorePage(candidate.geometry, pageIndex), tail.score);
        if (isBetterScore(score, best?.score)) {
          best = {
            pages: [
              { blocks: units.slice(start, candidate.end), geometry: candidate.geometry },
              ...tail.pages,
            ],
            score,
          };
        }
      }
    }
    layoutCache.set(stateKey, best);
    return best;
  }

  const balanced = await findLayout(0, 0);
  if (balanced) pages.splice(0, pages.length, ...balanced.pages);
}

function removeOrphanTableHeaders(layoutPages) {
  return layoutPages.map(page => ({
    ...page,
    blocks: page.blocks.filter((unit, index, units) => {
      if (unit.type !== "table-header" || unit.table.rows.length === 0) return true;
      const next = units[index + 1];
      return next?.type === "table-row" && next.table === unit.table;
    }),
  }));
}

function renderPageHtml(page, title) {
  const isCover = page.kind === "cover";
  const styleValues = [];
  if (isCover && Number.isFinite(page.coverTitleGap)) styleValues.push(`--memo-cover-title-gap:${page.coverTitleGap}px`);
  if (Number.isFinite(page.tailBlockGap) && page.tailBlockGap > 0) styleValues.push(`--memo-tail-block-gap:${page.tailBlockGap}px`);
  const pageStyle = styleValues.length ? ` style="${styleValues.join(";")}"` : "";
  const content = page.blocks.map((block, index) => {
    const attributes = [
      `data-render-block="${block.type}"`,
      `data-render-block-id="${page.page}-${index}"`,
    ];
    if (block.type === "table") {
      attributes.push(`data-render-table-index="${block.tableIndex}"`);
      attributes.push(`data-render-table-group-index="${block.tableGroupIndex}"`);
    }
    if (block.type === "paragraph" && Number.isInteger(block.sourceParagraphIndex)) {
      attributes.push(`data-source-paragraph-index="${block.sourceParagraphIndex}"`);
    }
    return renderContentBlock(block, attributes.join(" "));
  }).join("");
  return `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=1080,initial-scale=1"><style>${memoCss}</style></head><body>
    <main class="memo-page ${isCover ? "memo-cover" : "memo-body-page"}${page.tailBlockGap ? " memo-tail-balanced" : ""}"${pageStyle}>
      ${memoToolbar()}
      <article class="memo-article">${isCover ? `<h1 class="memo-title" data-render-title>${renderInline(title)}</h1>` : ""}<section class="memo-body">${content}</section></article>
    </main></body></html>`;
}

function readPngDimensions(filePath) {
  const png = fs.readFileSync(filePath);
  if (png.toString("ascii", 1, 4) !== "PNG") throw new Error(`${path.basename(filePath)} is not a PNG file.`);
  return {
    bytes: png,
    width: png.readUInt32BE(16),
    height: png.readUInt32BE(20),
  };
}

async function renderScreenshot(context, outputDirectory, htmlPath, index) {
  const pageNumber = String(index + 1).padStart(2, "0");
  const filename = `${pageNumber}.png`;
  const pngPath = path.join(outputDirectory, filename);
  const page = await context.newPage();
  try {
    await page.setViewportSize({ width: PAGE_WIDTH, height: PAGE_HEIGHT });
    await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "load", timeout: 15_000 });
    await page.evaluate(() => document.fonts.ready);
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    const stats = await page.evaluate(limit => {
      const bounds = element => {
        const rect = element.getBoundingClientRect();
        return {
          left: Math.round(rect.left),
          top: Math.round(rect.top),
          right: Math.round(rect.right),
          bottom: Math.round(rect.bottom),
          width: Math.round(rect.width),
          height: Math.round(rect.height),
        };
      };
      const visibility = element => {
        const rect = element.getBoundingClientRect();
        const style = getComputedStyle(element);
        return style.display !== "none" && style.visibility === "visible"
          && Number.parseFloat(style.opacity) > 0 && rect.width > 0 && rect.height > 0;
      };
      const article = document.querySelector(".memo-article");
      const rect = article.getBoundingClientRect();
      const toolbarElement = document.querySelector(".memo-toolbar");
      const backLabelElement = document.querySelector(".memo-back-label");
      const backLabelRange = document.createRange();
      backLabelRange.selectNodeContents(backLabelElement);
      const toolbar = {
        bounds: bounds(toolbarElement),
        visible: visibility(toolbarElement),
        backLabel: {
          text: backLabelElement.textContent,
          lineCount: backLabelRange.getClientRects().length,
        },
        controls: [...document.querySelectorAll("[data-memo-control]")].map(element => ({
          name: element.dataset.memoControl,
          ...bounds(element),
          color: getComputedStyle(element).color,
          visible: visibility(element),
        })),
      };
      const tableRows = [...document.querySelectorAll(".memo-table tbody tr")].map(row => {
        const rowRect = row.getBoundingClientRect();
        return { top: Math.round(rowRect.top), bottom: Math.round(rowRect.bottom) };
      });
      return {
        contentTop: Math.round(rect.top),
        contentBottom: Math.round(rect.bottom),
        contentHeight: Math.round(rect.height),
        availableHeight: Math.round(limit - rect.top),
        fillRatio: rect.height / (limit - rect.top),
        contentBottomLimit: limit,
        toolbar,
        tableRows,
        overflow: rect.bottom > limit + 0.5 || article.scrollWidth > article.clientWidth,
      };
    }, CONTENT_BOTTOM_LIMIT);
    await page.screenshot({ path: pngPath, type: "png", animations: "disabled" });
    const image = readPngDimensions(pngPath);
    return {
      page: index + 1,
      filename,
      width: image.width,
      height: image.height,
      ...stats,
      overflow: Boolean(stats.overflow || image.width !== PAGE_WIDTH || image.height !== PAGE_HEIGHT
        || stats.tableRows.some(row => row.bottom > CONTENT_BOTTOM_LIMIT)),
      sha256: crypto.createHash("sha256").update(image.bytes).digest("hex"),
    };
  } finally {
    await page.close();
  }
}

function readSource(source) {
  const title = String(source.title ?? "");
  const body = String(source.body ?? "");
  if (!title.trim()) throw new Error("source.json must contain a non-empty title.");
  if (!body.trim()) throw new Error("source.json must contain a non-empty body.");
  return { title, body };
}

async function clearRenderedPageFiles(directory, workDirectory) {
  const rootEntries = await fsp.readdir(directory, { withFileTypes: true });
  await Promise.all(rootEntries
    .filter(entry => entry.isFile() && /^\d{2}\.png$/.test(entry.name))
    .map(entry => fsp.unlink(path.join(directory, entry.name))));

  await fsp.mkdir(workDirectory, { recursive: true });
  const workEntries = await fsp.readdir(workDirectory, { withFileTypes: true });
  await Promise.all(workEntries
    .filter(entry => entry.isFile() && /^page-\d{2}\.html$/.test(entry.name))
    .map(entry => fsp.unlink(path.join(workDirectory, entry.name))));
}

export async function renderPackage(outputDirectory, options = {}) {
  const directory = path.resolve(outputDirectory);
  const prepareOnly = options.prepareOnly === true;
  const chromePath = options.chromePath || CHROME_PATH;
  await clearValidationArtifacts(directory);
  const source = JSON.parse(await fsp.readFile(path.join(directory, "source.json"), "utf8"));
  const { title, body } = readSource(source);
  const sourceHash = crypto.createHash("sha256")
    .update(`${title.trim()}\n${body.replace(/\s+/gu, "").trim()}`)
    .digest("hex");
  let tableIndex = 0;
  const sourceBlocks = parseMarkdownBlocks(body).flatMap(block => {
    if (block.type !== "table") return [block];
    const currentTableIndex = tableIndex;
    tableIndex += 1;
    return splitWideTables([block], 4).map((group, tableGroupIndex) => ({
      ...group,
      tableIndex: currentTableIndex,
      tableGroupIndex,
    }));
  });
  if (sourceBlocks.length === 0) throw new Error("source.json body did not produce any renderable blocks.");
  const blocks = expandSemanticUnits(sourceBlocks);

  const browserSession = await openBrowser(chromePath);
  try {
    const layoutPages = await paginateSemanticUnits(browserSession.context, title, blocks);
    if (layoutPages[0]?.blocks.length === 0) {
      const error = new Error("The first source block does not fit below the cover title.");
      error.code = "FIRST_BLOCK_DOES_NOT_FIT_COVER";
      throw error;
    }
    const pages = layoutPages.filter(page => page.blocks.length > 0).map(materializePage);
    const workDirectory = path.join(directory, "_render-work");
    await clearRenderedPageFiles(directory, workDirectory);
    await Promise.all([
      fsp.writeFile(path.join(directory, "pages.json"), `${JSON.stringify(pages, null, 2)}\n`),
      fsp.writeFile(path.join(directory, "pagination.txt"), `${[title, ...pages.map(page => page.rendered_text)].filter(Boolean).join("\n\n")}\n`),
      ...pages.map((page, index) => {
        const pageNumber = String(index + 1).padStart(2, "0");
        return fsp.writeFile(path.join(workDirectory, `page-${pageNumber}.html`), renderPageHtml(page, title));
      }),
    ]);

    if (prepareOnly) {
      return {
        prepared: true,
        width: PAGE_WIDTH,
        height: PAGE_HEIGHT,
        pageCount: pages.length,
        filenames: [],
        toolbarControls: TOOLBAR_CONTROLS,
        overflowCount: 0,
        results: [],
      };
    }

    const results = [];
    for (let index = 0; index < pages.length; index += 1) {
      const pageNumber = String(index + 1).padStart(2, "0");
      results.push(await renderScreenshot(
        browserSession.context,
        directory,
        path.join(workDirectory, `page-${pageNumber}.html`),
        index,
      ));
    }
    const report = {
      template: "original-memo",
      sourceHash,
      toolbarControls: TOOLBAR_CONTROLS,
      width: PAGE_WIDTH,
      height: PAGE_HEIGHT,
      contentBottomLimit: CONTENT_BOTTOM_LIMIT,
      pageCount: results.length,
      filenames: results.map(result => result.filename),
      overflowCount: results.filter(result => result.overflow).length,
      generatedAt: new Date().toISOString(),
      results,
    };
    await fsp.writeFile(path.join(directory, "render-stats.json"), `${JSON.stringify(report, null, 2)}\n`);
    if (report.overflowCount > 0) {
      const error = new Error(`Rendered package contains ${report.overflowCount} overflowing page(s).`);
      error.report = report;
      throw error;
    }
    const validation = await validatePackage(directory);
    if (!validation.ok) {
      const error = new Error("Rendered package failed deterministic validation.");
      error.code = "PACKAGE_VALIDATION_FAILED";
      error.report = validation;
      throw error;
    }
    return { ...report, validation };
  } finally {
    await browserSession.close();
  }
}

async function runCli() {
  const [directoryArgument, ...flags] = process.argv.slice(2);
  if (!directoryArgument || flags.some(flag => flag !== "--prepare-only")) {
    throw new Error("Usage: node render-package.mjs <output-directory> [--prepare-only]");
  }
  const report = await renderPackage(directoryArgument, { prepareOnly: flags.includes("--prepare-only") });
  process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  await runCli();
}
