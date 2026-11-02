import crypto from "node:crypto";
import fsp from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import zlib from "node:zlib";

import { parseMarkdownBlocks, splitWideTables } from "./layout.mjs";

const PAGE_WIDTH = 1080;
const PAGE_HEIGHT = 1440;
const CONTENT_BOTTOM_LIMIT = 1376;
const FINAL_ARTIFACTS = ["validation.json", "manifest.json", "final-verification.json"];

function digest(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
}

function computeSourceHash(source) {
  const title = String(source?.title ?? "").trim();
  const body = String(source?.body ?? "").replace(/\s+/gu, "").trim();
  return digest(`${title}\n${body}`);
}

function normalizeText(value) {
  return String(value ?? "")
    .replace(/\r\n?/g, "\n")
    .replace(/\*\*(.+?)\*\*/gs, "$1")
    .replace(/__(.+?)__/gs, "$1")
    .replace(/~~(.+?)~~/gs, "$1")
    .replace(/`(.+?)`/gs, "$1")
    .replace(/\\([\\`*_[\]{}()#+.!|>~-])/g, "$1")
    .replace(/\s+/gu, " ")
    .trim();
}

function issue(code, message) {
  return { code, message };
}

function stableIssues(issues) {
  const unique = new Map(issues.map(item => [`${item.code}\u0000${item.message}`, item]));
  return [...unique.values()].sort((left, right) =>
    left.code.localeCompare(right.code) || left.message.localeCompare(right.message));
}

export async function clearValidationArtifacts(directory) {
  await Promise.all(FINAL_ARTIFACTS.map(async filename => {
    try {
      await fsp.unlink(path.join(directory, filename));
    } catch (error) {
      if (error.code !== "ENOENT") throw error;
    }
  }));
}

async function readJson(directory, filename, errors) {
  try {
    return JSON.parse(await fsp.readFile(path.join(directory, filename), "utf8"));
  } catch (error) {
    errors.push(issue("INVALID_PACKAGE_JSON", `${filename}: ${error.code || error.message}`));
    return null;
  }
}

function semanticTokens(blocks) {
  return blocks.flatMap(block => {
    if (block.type === "table") return [];
    if (block.type === "list") {
      return (block.items || []).map(value => ({ type: "list-item", text: normalizeText(value) }));
    }
    if (block.type === "paragraph" || block.type === "heading") {
      return [{ type: block.type, text: normalizeText(block.renderedText) }];
    }
    return [{ type: String(block.type || "unknown"), text: normalizeText(block.renderedText) }];
  });
}

function tableToken(tableIndex, tableGroupIndex) {
  return { type: "table", tableIndex, tableGroupIndex };
}

function sourceSemanticTokens(sourceBlocks) {
  let tableIndex = 0;
  return sourceBlocks.flatMap(block => {
    if (block.type !== "table") return semanticTokens([block]);
    const currentTableIndex = tableIndex;
    tableIndex += 1;
    return splitWideTables([block], 4).map((_, tableGroupIndex) => tableToken(currentTableIndex, tableGroupIndex));
  });
}

function renderedSemanticTokens(blocks) {
  const seenTables = new Set();
  const tokens = [];
  for (const block of blocks) {
    if (block.type === "paragraph" && Number.isInteger(block.sourceParagraphIndex)) {
      const previous = tokens.at(-1);
      if (previous?.type === "paragraph" && previous.sourceParagraphIndex === block.sourceParagraphIndex) {
        previous.rawText += String(block.renderedText ?? "");
      } else {
        tokens.push({
          type: "paragraph",
          sourceParagraphIndex: block.sourceParagraphIndex,
          rawText: String(block.renderedText ?? ""),
        });
      }
      continue;
    }
    if (block.type !== "table") {
      tokens.push(...semanticTokens([block]));
      continue;
    }
    const token = tableToken(block.tableIndex, block.tableGroupIndex);
    const key = `${token.tableIndex}:${token.tableGroupIndex}`;
    if (seenTables.has(key)) continue;
    seenTables.add(key);
    tokens.push(token);
  }
  return tokens.map(token => token.rawText === undefined ? token : ({
    type: token.type,
    text: normalizeText(token.rawText),
  }));
}

function decodeHtmlText(value) {
  return String(value)
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<[^>]+>/g, "")
    .replaceAll("&quot;", '"')
    .replaceAll("&gt;", ">")
    .replaceAll("&lt;", "<")
    .replaceAll("&amp;", "&");
}

function htmlAttribute(attributes, name) {
  return attributes.match(new RegExp(`\\b${name}="([^"]*)"`))?.[1];
}

async function finalHtmlSemanticTokens(directory, pageCount, errors) {
  const tokens = [];
  for (let index = 0; index < pageCount; index += 1) {
    const filename = `page-${String(index + 1).padStart(2, "0")}.html`;
    let html;
    try {
      html = await fsp.readFile(path.join(directory, "_render-work", filename), "utf8");
    } catch (error) {
      errors.push(issue("MISSING_FINAL_RENDER_HTML", `${filename}: ${error.code || error.message}`));
      continue;
    }
    const visibleText = decodeHtmlText(html
      .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, "")
      .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, "")
      .replace(/<svg\b[^>]*>[\s\S]*?<\/svg>/gi, ""));
    if (/\*\*/u.test(visibleText)) {
      errors.push(issue("RAW_MARKDOWN_MARKER", `${filename} exposes a raw Markdown emphasis marker.`));
    }
    for (const match of html.matchAll(/<(h1|p|h2|ul|div)\b([^>]*)>([\s\S]*?)<\/\1>/g)) {
      const [, tag, attributes, content] = match;
      if (/\bdata-render-title(?:\s|=|$)/.test(attributes)) {
        tokens.push({ type: "title", text: normalizeText(decodeHtmlText(content)) });
        continue;
      }
      const blockType = htmlAttribute(attributes, "data-render-block");
      if (blockType === "paragraph" || blockType === "heading") {
        const sourceParagraphIndex = Number(htmlAttribute(attributes, "data-source-paragraph-index"));
        const rawText = decodeHtmlText(content);
        const previous = tokens.at(-1);
        if (blockType === "paragraph" && Number.isInteger(sourceParagraphIndex)
          && previous?.type === "paragraph" && previous.sourceParagraphIndex === sourceParagraphIndex) {
          previous.rawText += rawText;
        } else if (blockType === "paragraph" && Number.isInteger(sourceParagraphIndex)) {
          tokens.push({ type: blockType, sourceParagraphIndex, rawText });
        } else {
          tokens.push({ type: blockType, text: normalizeText(rawText) });
        }
      } else if (blockType === "list") {
        for (const item of content.matchAll(/<li\b[^>]*>([\s\S]*?)<\/li>/g)) {
          tokens.push({ type: "list-item", text: normalizeText(decodeHtmlText(item[1])) });
        }
      } else if (blockType === "table") {
        tokens.push(tableToken(
          Number(htmlAttribute(attributes, "data-render-table-index")),
          Number(htmlAttribute(attributes, "data-render-table-group-index")),
        ));
      }
    }
  }
  const seenTables = new Set();
  return tokens.filter(token => {
    if (token.type !== "table") return true;
    const key = `${token.tableIndex}:${token.tableGroupIndex}`;
    if (seenTables.has(key)) return false;
    seenTables.add(key);
    return true;
  }).map(token => token.rawText === undefined ? token : ({
    type: token.type,
    text: normalizeText(token.rawText),
  }));
}

function sameIndexes(left, right) {
  return Array.isArray(left) && Array.isArray(right)
    && left.length === right.length && left.every((value, index) => value === right[index]);
}

function sameCells(left, right) {
  return Array.isArray(left) && Array.isArray(right)
    && left.length === right.length
    && left.every((value, index) => normalizeText(value) === normalizeText(right[index]));
}

function coordinate(tableIndex, rowIndex, sourceColumnIndex) {
  return `${tableIndex}:${rowIndex}:${sourceColumnIndex}`;
}

function tableLocation(tableIndex, rowIndex, sourceColumnIndex) {
  return `(tableIndex=${tableIndex},rowIndex=${rowIndex},sourceColumnIndex=${sourceColumnIndex})`;
}

function inspectRawTableParagraphs(pages, errors) {
  for (const page of pages) {
    for (const block of page.blocks || []) {
      if (block.type !== "paragraph") continue;
      const candidate = String(block.markdown ?? block.source_markdown ?? block.renderedText ?? "");
      try {
        if (parseMarkdownBlocks(candidate).some(parsed => parsed.type === "table")) {
          errors.push(issue(
            "RAW_MARKDOWN_TABLE_PARAGRAPH",
            `Page ${page.page ?? "?"} contains a Markdown table in a paragraph block.`,
          ));
        }
      } catch {
        errors.push(issue(
          "RAW_MARKDOWN_TABLE_PARAGRAPH",
          `Page ${page.page ?? "?"} contains malformed Markdown table syntax in a paragraph block.`,
        ));
      }
    }
  }
}

function buildExpectedTables(sourceBlocks) {
  let tableIndex = 0;
  return sourceBlocks.filter(block => block.type === "table").map(table => {
    const index = tableIndex;
    tableIndex += 1;
    return {
      tableIndex: index,
      source: table,
      groups: splitWideTables([table], 4).map((group, groupIndex) => ({
        tableIndex: index,
        groupIndex,
        header: group.header,
        rows: group.rows,
        sourceColumnIndexes: group.sourceColumnIndexes,
      })),
    };
  });
}

function assignObservedTables(pages, expectedTables, errors) {
  const expectedGroups = expectedTables.flatMap(table => table.groups);
  const assignments = new Map(expectedGroups.map(group => [`${group.tableIndex}:${group.groupIndex}`, []]));
  const observed = pages.flatMap((page, pageIndex) => (page.blocks || [])
    .map((block, blockIndex) => ({ block, pageIndex, blockIndex }))
    .filter(item => item.block.type === "table"));

  for (const item of observed) {
    const { block } = item;
    let candidates = expectedGroups.filter(group => sameIndexes(group.sourceColumnIndexes, block.sourceColumnIndexes));
    if (Number.isInteger(block.tableIndex)) {
      candidates = candidates.filter(group => group.tableIndex === block.tableIndex);
    }
    if (Number.isInteger(block.tableGroupIndex)) {
      candidates = candidates.filter(group => group.groupIndex === block.tableGroupIndex);
    }
    const headerCandidates = candidates.filter(group => sameCells(group.header, block.header));
    if (headerCandidates.length > 0) candidates = headerCandidates;
    const group = candidates[0];
    if (!group) {
      errors.push(issue(
        "UNDECLARED_TABLE_FRAGMENT",
        `Page ${item.pageIndex + 1} block ${item.blockIndex + 1} does not match a source table group.`,
      ));
      continue;
    }
    assignments.get(`${group.tableIndex}:${group.groupIndex}`).push(item);
  }
  return assignments;
}

function validateTables(expectedTables, assignments, errors) {
  const expectedCounts = new Map();
  const actualCounts = new Map();
  let repeatedTableHeaderCount = 0;

  for (const table of expectedTables) {
    for (let rowIndex = 0; rowIndex < table.source.rows.length; rowIndex += 1) {
      for (let sourceColumnIndex = 0; sourceColumnIndex < table.source.header.length; sourceColumnIndex += 1) {
        const key = coordinate(table.tableIndex, rowIndex, sourceColumnIndex);
        const structuralCount = table.groups.filter(group => group.sourceColumnIndexes.includes(sourceColumnIndex)).length;
        expectedCounts.set(key, structuralCount);
      }
    }

    for (const group of table.groups) {
      const fragments = assignments.get(`${group.tableIndex}:${group.groupIndex}`) || [];
      if (fragments.length === 0) {
        errors.push(issue(
          "MISSING_TABLE_GROUP",
          `Source table ${table.tableIndex} group ${group.groupIndex} was not rendered.`,
        ));
      }

      fragments.forEach((fragment, fragmentIndex) => {
        if (!Array.isArray(fragment.block.rows) || fragment.block.rows.length === 0) {
          errors.push(issue(
            "HEADER_ONLY_TABLE_FRAGMENT",
            `Source table ${table.tableIndex} group ${group.groupIndex} has a header without rows on page ${fragment.pageIndex + 1}.`,
          ));
        }
        if (fragmentIndex > 0) {
          const previous = fragments[fragmentIndex - 1];
          if (fragment.pageIndex <= previous.pageIndex) {
            errors.push(issue(
              fragment.pageIndex === previous.pageIndex ? "DUPLICATED_TABLE_GROUP_ON_PAGE" : "INVALID_TABLE_CONTINUATION_ORDER",
              `Source table ${table.tableIndex} group ${group.groupIndex} repeats before a later page.`,
            ));
          } else if (Array.isArray(fragment.block.rows) && fragment.block.rows.length > 0) {
            repeatedTableHeaderCount += 1;
          }
        }
        if (sameCells(fragment.block.header, group.header)) return;
        errors.push(issue(
          fragmentIndex > 0 ? "MISSING_REPEATED_TABLE_HEADER" : "TABLE_HEADER_MISMATCH",
          `Source table ${table.tableIndex} group ${group.groupIndex} has an invalid header on page ${fragment.pageIndex + 1}.`,
        ));
      });

      const renderedRows = fragments.flatMap(fragment => fragment.block.rows || []);
      renderedRows.forEach((row, renderedRowIndex) => {
        let sourceRowIndex = renderedRowIndex;
        if (renderedRowIndex >= group.rows.length) {
          sourceRowIndex = group.rows.findIndex(expectedRow => sameCells(expectedRow, row));
          if (sourceRowIndex < 0) {
            errors.push(issue(
              "UNDECLARED_TABLE_ROW",
              `Source table ${table.tableIndex} group ${group.groupIndex} contains an undeclared extra row.`,
            ));
            return;
          }
        }
        const expectedRow = group.rows[sourceRowIndex];
        for (let cellIndex = 0; cellIndex < group.sourceColumnIndexes.length; cellIndex += 1) {
          const sourceColumnIndex = group.sourceColumnIndexes[cellIndex];
          const key = coordinate(table.tableIndex, sourceRowIndex, sourceColumnIndex);
          if (cellIndex < row.length && normalizeText(row[cellIndex]) === normalizeText(expectedRow[cellIndex])) {
            actualCounts.set(key, (actualCounts.get(key) || 0) + 1);
          } else if (cellIndex < row.length) {
            errors.push(issue(
              "TABLE_CELL_TEXT_MISMATCH",
              `Rendered cell differs from source ${tableLocation(table.tableIndex, sourceRowIndex, sourceColumnIndex)}.`,
            ));
          }
        }
        if (row.length > group.sourceColumnIndexes.length) {
          errors.push(issue(
            "UNDECLARED_TABLE_CELL",
            `Source table ${table.tableIndex} group ${group.groupIndex} row ${sourceRowIndex} has extra cells.`,
          ));
        }
      });
    }
  }

  for (const [key, expectedCount] of expectedCounts) {
    const [tableIndex, rowIndex, sourceColumnIndex] = key.split(":").map(Number);
    const actualCount = actualCounts.get(key) || 0;
    if (actualCount < expectedCount) {
      errors.push(issue(
        "LOST_TABLE_CELL",
        `Expected ${expectedCount}, found ${actualCount} for ${tableLocation(tableIndex, rowIndex, sourceColumnIndex)}.`,
      ));
    } else if (actualCount > expectedCount) {
      errors.push(issue(
        "DUPLICATED_TABLE_CELL",
        `Expected ${expectedCount}, found ${actualCount} for ${tableLocation(tableIndex, rowIndex, sourceColumnIndex)}.`,
      ));
    }
  }
  return repeatedTableHeaderCount;
}

function readPng(bytes) {
  const signature = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
  if (bytes.length < 8 || !bytes.subarray(0, 8).equals(signature)) return null;
  let offset = 8;
  let header = null;
  const dataChunks = [];
  let seenData = false;
  let seenEnd = false;
  while (offset < bytes.length) {
    if (offset + 12 > bytes.length) return null;
    const length = bytes.readUInt32BE(offset);
    const dataStart = offset + 8;
    const dataEnd = dataStart + length;
    const crcOffset = dataEnd;
    if (dataEnd > bytes.length - 4) return null;
    const type = bytes.toString("ascii", offset + 4, offset + 8);
    const data = bytes.subarray(dataStart, dataEnd);
    if (bytes.readUInt32BE(crcOffset) !== crc32(Buffer.concat([Buffer.from(type), data]))) return null;
    if (seenEnd) return null;
    if (type === "IHDR") {
      if (header || length !== 13 || offset !== 8) return null;
      header = {
        width: data.readUInt32BE(0),
        height: data.readUInt32BE(4),
        bitDepth: data[8],
        colorType: data[9],
        compression: data[10],
        filter: data[11],
        interlace: data[12],
      };
    } else if (type === "IDAT") {
      if (!header || seenEnd) return null;
      seenData = true;
      dataChunks.push(data);
    } else if (type === "IEND") {
      if (!header || !seenData || length !== 0 || crcOffset + 4 !== bytes.length) return null;
      seenEnd = true;
    } else if (seenData) {
      return null;
    }
    offset = crcOffset + 4;
  }
  if (!header || !seenData || !seenEnd || header.width === 0 || header.height === 0
    || header.bitDepth !== 8 || header.compression !== 0 || header.filter !== 0 || header.interlace !== 0) return null;
  const channels = { 0: 1, 2: 3, 4: 2, 6: 4 }[header.colorType];
  if (!channels) return null;
  try {
    const decoded = zlib.inflateSync(Buffer.concat(dataChunks));
    if (decoded.length !== header.height * (header.width * channels + 1)) return null;
  } catch {
    return null;
  }
  return header;
}

function crc32(bytes) {
  let value = 0xffffffff;
  for (const byte of bytes) {
    value ^= byte;
    for (let bit = 0; bit < 8; bit += 1) value = (value >>> 1) ^ (value & 1 ? 0xedb88320 : 0);
  }
  return (value ^ 0xffffffff) >>> 0;
}

function hasValidGeometry(result) {
  return Number.isFinite(result?.contentTop)
    && Number.isFinite(result?.contentBottom)
    && Number.isFinite(result?.contentHeight)
    && Number.isFinite(result?.availableHeight)
    && Number.isFinite(result?.fillRatio)
    && result?.contentBottomLimit === CONTENT_BOTTOM_LIMIT
    && Array.isArray(result?.tableRows)
    && result.tableRows.every(row => Number.isFinite(row?.top) && Number.isFinite(row?.bottom));
}

function recomputeFillRatio(result) {
  const availableHeight = CONTENT_BOTTOM_LIMIT - Number(result?.contentTop);
  const contentHeight = Number(result?.contentBottom) - Number(result?.contentTop);
  return availableHeight > 0 ? contentHeight / availableHeight : Number.NaN;
}

function isOverflow(result, image) {
  const contentOverflow = Number(result?.contentBottom) > CONTENT_BOTTOM_LIMIT;
  const rowOverflow = Array.isArray(result?.tableRows)
    && result.tableRows.some(row => Number(row.bottom) > CONTENT_BOTTOM_LIMIT);
  return result?.overflow === true || contentOverflow || rowOverflow
    || image?.width !== PAGE_WIDTH || image?.height !== PAGE_HEIGHT;
}

function reportTextIsExact(errors) {
  const textCodes = new Set([
    "INVALID_SOURCE_MARKDOWN",
    "NON_TABLE_TEXT_MISMATCH",
    "RAW_MARKDOWN_TABLE_PARAGRAPH",
    "RAW_MARKDOWN_MARKER",
    "MISSING_TABLE_GROUP",
    "UNDECLARED_TABLE_FRAGMENT",
    "UNDECLARED_TABLE_ROW",
    "UNDECLARED_TABLE_CELL",
    "TABLE_HEADER_MISMATCH",
    "MISSING_REPEATED_TABLE_HEADER",
    "TABLE_CELL_TEXT_MISMATCH",
    "LOST_TABLE_CELL",
    "DUPLICATED_TABLE_CELL",
  ]);
  return !errors.some(error => textCodes.has(error.code));
}

async function writeFinalArtifacts(directory, report, source, sourceHash, images) {
  const imageHashes = images.map(image => ({
    filename: image.filename,
    sha256: image.sha256,
    width: image.width,
    height: image.height,
  }));
  const validation = {
    ok: true,
    exact_text: true,
    table_count: report.tableCount,
    table_row_count: report.tableRowCount,
    repeated_table_header_count: report.repeatedTableHeaderCount,
    overflow_count: report.overflowCount,
    page_count: report.pageCount,
    filenames: report.filenames,
    source_hash: sourceHash,
    image_hashes: imageHashes,
    errors: [],
    warnings: report.warnings,
  };
  const manifest = {
    recordId: source.platformRecordId ?? source.recordId ?? "",
    contentId: source.platformContentId ?? source.contentId ?? "",
    masterRecordId: source.masterRecordId ?? source.recordId ?? "",
    masterContentId: source.masterContentId ?? source.contentId ?? "",
    jobId: source.jobId ?? "",
    sourceHash,
    width: PAGE_WIDTH,
    height: PAGE_HEIGHT,
    pageCount: report.pageCount,
    filenames: report.filenames,
    overflowCount: report.overflowCount,
    exactText: report.exactText,
    tableCount: report.tableCount,
    tableRowCount: report.tableRowCount,
    repeatedTableHeaderCount: report.repeatedTableHeaderCount,
    imageHashes,
  };
  const finalVerification = {
    ok: true,
    localPreview: true,
    publicPublishTriggered: false,
    sourceHash,
    exactText: report.exactText,
    tableCount: report.tableCount,
    tableRowCount: report.tableRowCount,
    repeatedTableHeaderCount: report.repeatedTableHeaderCount,
    overflowCount: report.overflowCount,
    pageCount: report.pageCount,
    filenames: report.filenames,
    imageHashes,
  };
  await Promise.all([
    fsp.writeFile(path.join(directory, "validation.json"), `${JSON.stringify(validation, null, 2)}\n`),
    fsp.writeFile(path.join(directory, "manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`),
    fsp.writeFile(path.join(directory, "final-verification.json"), `${JSON.stringify(finalVerification, null, 2)}\n`),
  ]);
}

export async function validatePackage(packageDirectory) {
  const directory = path.resolve(packageDirectory);
  await clearValidationArtifacts(directory);
  const errors = [];
  const warnings = [];
  const [source, pages, stats, entries] = await Promise.all([
    readJson(directory, "source.json", errors),
    readJson(directory, "pages.json", errors),
    readJson(directory, "render-stats.json", errors),
    fsp.readdir(directory, { withFileTypes: true }),
  ]);
  const pageList = Array.isArray(pages) ? pages : [];
  const expectedFilenames = pageList.map((_, index) => `${String(index + 1).padStart(2, "0")}.png`);
  const filenames = entries
    .filter(entry => entry.isFile() && /^\d{2}\.png$/.test(entry.name))
    .map(entry => entry.name)
    .sort();
  let sourceBlocks = [];
  let expectedTables = [];
  let repeatedTableHeaderCount = 0;
  let sourceHash = "";

  if (source) {
    sourceHash = computeSourceHash(source);
    if (typeof source.sourceHash !== "string" || !/^[0-9a-f]{64}$/.test(source.sourceHash)) {
      errors.push(issue("INVALID_SOURCE_HASH", "source.json sourceHash must be a 64-character lowercase hexadecimal SHA-256."));
    } else if (source.sourceHash !== sourceHash) {
      errors.push(issue("SOURCE_HASH_MISMATCH", "source.json sourceHash does not match its current title and body."));
    }
    if (stats?.sourceHash && stats.sourceHash !== sourceHash) {
      errors.push(issue("RENDER_SOURCE_HASH_MISMATCH", "render-stats.json was produced from a different source hash."));
    }
    try {
      sourceBlocks = parseMarkdownBlocks(String(source.body ?? ""));
      expectedTables = buildExpectedTables(sourceBlocks);
    } catch (error) {
      errors.push(issue("INVALID_SOURCE_MARKDOWN", error.code || error.message));
    }
  }

  if (!Array.isArray(pages)) {
    errors.push(issue("INVALID_PAGES", "pages.json must contain an array."));
  } else {
    const pageNumbers = pages.map(page => page.page);
    const expectedPageNumbers = pages.map((_, index) => index + 1);
    if (JSON.stringify(pageNumbers) !== JSON.stringify(expectedPageNumbers)) {
      errors.push(issue("NON_CONTINUOUS_PAGE_NUMBERS", "pages.json page numbers are not continuous from 1."));
    }
    inspectRawTableParagraphs(pages, errors);
    const sourceTokens = [{ type: "title", text: normalizeText(source?.title) }, ...sourceSemanticTokens(sourceBlocks)];
    const renderedTokens = [{ type: "title", text: normalizeText(source?.title) }, ...renderedSemanticTokens(pages.flatMap(page => page.blocks || []))];
    if (JSON.stringify(sourceTokens) !== JSON.stringify(renderedTokens)) {
      errors.push(issue("NON_TABLE_TEXT_MISMATCH", "Rendered blocks do not match source order and content."));
    }
    const finalTokens = await finalHtmlSemanticTokens(directory, pages.length, errors);
    if (JSON.stringify(renderedTokens) !== JSON.stringify(finalTokens)
      || JSON.stringify(sourceTokens) !== JSON.stringify(finalTokens)) {
      errors.push(issue("FINAL_HTML_SEMANTIC_MISMATCH", "Final rendered HTML does not match source and pages.json semantic order."));
    }
    const assignments = assignObservedTables(pages, expectedTables, errors);
    repeatedTableHeaderCount = validateTables(expectedTables, assignments, errors);
  }

  const missing = expectedFilenames.filter(filename => !filenames.includes(filename));
  const extra = filenames.filter(filename => !expectedFilenames.includes(filename));
  for (const filename of missing) errors.push(issue("MISSING_PAGE_IMAGE", `${filename} is missing.`));
  for (const filename of extra) errors.push(issue("EXTRA_UNDECLARED_PAGE_IMAGE", `${filename} is not declared by pages.json.`));
  const continuousForActualCount = filenames.map((_, index) => `${String(index + 1).padStart(2, "0")}.png`);
  if (JSON.stringify(filenames) !== JSON.stringify(continuousForActualCount)) {
    errors.push(issue("NON_CONTINUOUS_PAGE_FILENAMES", "Numbered PNG filenames are not continuous from 01.png."));
  }

  if (stats) {
    if (Number(stats.pageCount) !== pageList.length) {
      errors.push(issue("RENDER_STATS_PAGE_COUNT_MISMATCH", "render-stats.json pageCount differs from pages.json."));
    }
    if (JSON.stringify(stats.filenames) !== JSON.stringify(expectedFilenames)) {
      errors.push(issue("RENDER_STATS_FILENAME_MISMATCH", "render-stats.json filenames differ from pages.json."));
    }
  }
  const resultList = Array.isArray(stats?.results) ? stats.results : [];
  const resultByFilename = new Map();
  for (const result of resultList) {
    if (resultByFilename.has(result.filename)) {
      errors.push(issue("DUPLICATED_RENDER_RESULT", `${result.filename} appears more than once in render-stats.json.`));
    } else {
      resultByFilename.set(result.filename, result);
    }
  }

  const images = [];
  let overflowCount = 0;
  const enforceLongFormDensity = expectedFilenames.length > 1
    && String(source?.body ?? "").replace(/\s+/gu, "").length >= 1200;
  for (let pageIndex = 0; pageIndex < expectedFilenames.length; pageIndex += 1) {
    const filename = expectedFilenames[pageIndex];
    if (!filenames.includes(filename)) continue;
    const bytes = await fsp.readFile(path.join(directory, filename));
    const header = readPng(bytes);
    if (!header) {
      errors.push(issue("INVALID_PNG_STRUCTURE", `${filename} is not a complete, decodable PNG.`));
      continue;
    }
    const sha256 = digest(bytes);
    const image = { filename, ...header, sha256 };
    images.push(image);
    if (header.width !== PAGE_WIDTH || header.height !== PAGE_HEIGHT) {
      errors.push(issue("INVALID_PNG_DIMENSIONS", `${filename} is ${header.width}x${header.height}, expected ${PAGE_WIDTH}x${PAGE_HEIGHT}.`));
    }
    const result = resultByFilename.get(filename);
    if (!result) {
      errors.push(issue("MISSING_RENDER_RESULT", `${filename} has no render-stats.json result.`));
      continue;
    }
    if (result.sha256 !== sha256) {
      errors.push(issue("PNG_HASH_MISMATCH", `${filename} SHA-256 differs from render-stats.json.`));
    }
    if (Number(result.width) !== header.width || Number(result.height) !== header.height) {
      errors.push(issue("RENDER_RESULT_DIMENSION_MISMATCH", `${filename} dimensions differ from render-stats.json.`));
    }
    if (!hasValidGeometry(result)) {
      errors.push(issue("INVALID_RENDER_GEOMETRY", `${filename} lacks finite geometry using content bottom ${CONTENT_BOTTOM_LIMIT}.`));
    } else if (enforceLongFormDensity) {
      const minimum = pageIndex === 0 ? 0.78
        : pageIndex === expectedFilenames.length - 1 ? 0.67 : 0.72;
      const fillRatio = recomputeFillRatio(result);
      if (fillRatio + 0.005 < minimum) {
        errors.push(issue(
          "UNDERFILLED_PAGE",
          `${filename} fill ratio ${fillRatio.toFixed(3)} is below ${minimum.toFixed(2)}.`,
        ));
      }
    }
    if (isOverflow(result, image)) overflowCount += 1;
  }
  if (overflowCount > 0) {
    errors.push(issue("RENDER_OVERFLOW", `${overflowCount} rendered page(s) exceed the final geometry limits.`));
  }
  if (stats && Number(stats.overflowCount) !== overflowCount) {
    errors.push(issue("RENDER_STATS_OVERFLOW_MISMATCH", "render-stats.json overflowCount differs from recomputed geometry."));
  }

  const sortedErrors = stableIssues(errors);
  const sortedWarnings = stableIssues(warnings);
  const report = {
    ok: sortedErrors.length === 0,
    exactText: reportTextIsExact(sortedErrors),
    tableCount: expectedTables.length,
    tableRowCount: expectedTables.reduce((count, table) => count + table.source.rows.length, 0),
    repeatedTableHeaderCount,
    overflowCount,
    pageCount: pageList.length,
    filenames,
    errors: sortedErrors,
    warnings: sortedWarnings,
  };
  if (report.ok) await writeFinalArtifacts(directory, report, source, sourceHash, images);
  return report;
}

async function runCli() {
  const [directory, ...extra] = process.argv.slice(2);
  if (!directory || extra.length > 0) throw new Error("Usage: node validate-package.mjs <package-directory>");
  const report = await validatePackage(directory);
  process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
  if (!report.ok) process.exitCode = 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  await runCli();
}
