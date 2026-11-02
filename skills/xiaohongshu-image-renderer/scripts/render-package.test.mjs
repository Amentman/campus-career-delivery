import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import test from "node:test";

import * as renderer from "./render-package.mjs";

const { renderPackage } = renderer;

const rendererPath = fileURLToPath(new URL("./render-package.mjs", import.meta.url));

async function createFixture(t, source) {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), "xhs-image-renderer-test-"));
  t.after(() => fs.rm(directory, { recursive: true, force: true }));
  const lockedSource = { ...source };
  lockedSource.sourceHash ??= crypto.createHash("sha256")
    .update(`${String(lockedSource.title).trim()}\n${String(lockedSource.body).replace(/\s+/gu, "").trim()}`)
    .digest("hex");
  await fs.writeFile(path.join(directory, "source.json"), `${JSON.stringify(lockedSource, null, 2)}\n`);
  return directory;
}

function runCli(directory, prepareOnly = false) {
  const result = spawnSync(process.execPath, [rendererPath, directory, ...(prepareOnly ? ["--prepare-only"] : [])], {
    encoding: "utf8",
    timeout: 90_000,
    killSignal: "SIGKILL",
    maxBuffer: 16 * 1024 * 1024,
  });
  assert.equal(result.error?.code, undefined, result.error?.message);
  assert.equal(result.status, 0, result.stderr || result.stdout);
  return result;
}

function htmlText(markup) {
  return markup
    .replaceAll("<br>", "\n")
    .replace(/<[^>]+>/g, "")
    .replaceAll("&quot;", '"')
    .replaceAll("&gt;", ">")
    .replaceAll("&lt;", "<")
    .replaceAll("&amp;", "&");
}

function tagTexts(html, tagName) {
  const pattern = new RegExp(`<${tagName}\\b[^>]*>(.*?)<\\/${tagName}>`, "gs");
  return [...html.matchAll(pattern)].map(match => htmlText(match[1]));
}

test("测试浏览器启动时使用独立密码存储且不访问 macOS 钥匙串", () => {
  assert.equal(typeof renderer.chromeLaunchArguments, "function");
  const args = renderer.chromeLaunchArguments("/tmp/xhs-renderer-profile");

  assert.ok(args.includes("--password-store=basic"));
  assert.ok(args.includes("--use-mock-keychain"));
  assert.ok(args.includes("--user-data-dir=/tmp/xhs-renderer-profile"));
});

test("首个原子段落放不进封面剩余空间时以稳定错误码失败", async t => {
  const openingParagraph = "这是一句没有句末标点且必须保持完整的超长开场原文不能拆字改写或挪成标题空页".repeat(16);
  const directory = await createFixture(t, {
    title: "不能留下标题空页",
    body: openingParagraph,
  });

  await assert.rejects(
    () => renderPackage(directory, { prepareOnly: true }),
    error => error.code === "FIRST_BLOCK_DOES_NOT_FIT_COVER",
  );
});

test("连续 Markdown 列表按完整条目跨页且顺序内容不变", async t => {
  const items = Array.from({ length: 12 }, (_, index) =>
    `列表项 ${String(index + 1).padStart(2, "0")}：${"每个条目必须完整移动，不能拆分、改写、重复或丢失。".repeat(4)}`);
  const directory = await createFixture(t, {
    title: "长列表必须按条目分页",
    body: items.map(item => `- ${item}`).join("\n"),
  });

  const report = await renderPackage(directory, { prepareOnly: true });
  assert.ok(report.pageCount >= 3, `expected a multi-page list, got ${report.pageCount} page(s)`);

  const pages = JSON.parse(await fs.readFile(path.join(directory, "pages.json"), "utf8"));
  const listBlocks = pages.flatMap(page => page.blocks.filter(block => block.type === "list"));
  assert.ok(listBlocks.length >= 3, `expected per-page list blocks, got ${listBlocks.length}`);
  assert.deepEqual(listBlocks.flatMap(block => block.items), items);

  const htmlNames = (await fs.readdir(path.join(directory, "_render-work")))
    .filter(name => /^page-\d{2}\.html$/.test(name)).sort();
  const html = (await Promise.all(htmlNames.map(name =>
    fs.readFile(path.join(directory, "_render-work", name), "utf8")))).join("\n");
  const htmlItems = [...html.matchAll(/<li[^>]*>(.*?)<\/li>/g)].map(match => match[1]);
  assert.deepEqual(htmlItems, items);
});

test("单个长段落只按完整句子跨页并逐字还原", async t => {
  const sentences = Array.from({ length: 28 }, (_, index) =>
    `第 ${String(index + 1).padStart(2, "0")} 句说明项目判断必须回到用户、场景、动作和结果，不能只报平台名称。`);
  const body = sentences.join("");
  const directory = await createFixture(t, {
    title: "长段落也要按完整句子自然分页",
    body,
  });

  const report = await renderPackage(directory, { prepareOnly: true });
  assert.ok(report.pageCount >= 2);
  const pages = JSON.parse(await fs.readFile(path.join(directory, "pages.json"), "utf8"));
  const paragraphFragments = pages.flatMap(page => page.blocks.filter(block => block.type === "paragraph"));

  assert.ok(paragraphFragments.length >= 2, "expected the source paragraph to continue on a later page");
  assert.equal(paragraphFragments.map(block => block.markdown).join(""), body);
  assert.ok(paragraphFragments.slice(0, -1).every(block => /[。！？!?](?:[”’」』》）)\]】*]*)?\s*$/u.test(block.markdown)));
});

test("同目录长稿改短稿时只清理渲染器拥有的旧页面文件", async t => {
  const directory = await createFixture(t, {
    title: "先生成长稿",
    body: Array.from({ length: 20 }, (_, index) =>
      `长稿第 ${index + 1} 段用于生成多个旧页面，稍后必须清理对应的编号文件。`).join("\n\n"),
  });

  const longReport = await renderPackage(directory);
  assert.ok(longReport.pageCount >= 2);
  await fs.writeFile(path.join(directory, "keep.png"), "not renderer owned\n");
  await fs.writeFile(path.join(directory, "_render-work", "keep.html"), "not renderer owned\n");
  const shortSource = {
    title: "再生成短稿",
    body: "短稿只保留一个页面，而且不能留下旧的编号页面。",
  };
  shortSource.sourceHash = crypto.createHash("sha256")
    .update(`${shortSource.title.trim()}\n${shortSource.body.replace(/\s+/gu, "").trim()}`)
    .digest("hex");
  await fs.writeFile(path.join(directory, "source.json"), `${JSON.stringify(shortSource, null, 2)}\n`);

  const shortReport = await renderPackage(directory);
  assert.equal(shortReport.pageCount, 1);
  const numericPngs = (await fs.readdir(directory)).filter(name => /^\d{2}\.png$/.test(name)).sort();
  const pageHtml = (await fs.readdir(path.join(directory, "_render-work")))
    .filter(name => /^page-\d{2}\.html$/.test(name)).sort();
  assert.deepEqual(numericPngs, ["01.png"]);
  assert.deepEqual(pageHtml, ["page-01.html"]);
  await fs.access(path.join(directory, "keep.png"));
  await fs.access(path.join(directory, "_render-work", "keep.html"));
});

test("准备每页都有五控件且封面延续母稿正文的原生备忘录 DOM", async t => {
  const paragraphs = Array.from({ length: 18 }, (_, index) =>
    `第 ${index + 1} 段保留母稿原文，用于验证浏览器实测分页会生成正文页。`).join("\n\n");
  const directory = await createFixture(t, {
    title: "海外营销，不是把国内爆款翻译成英文",
    body: paragraphs,
  });

  assert.equal(typeof renderPackage, "function");
  runCli(directory, true);

  const workDirectory = path.join(directory, "_render-work");
  const htmlNames = (await fs.readdir(workDirectory)).filter(name => /^page-\d{2}\.html$/.test(name)).sort();
  assert.ok(htmlNames.length >= 2, `expected a cover and body page, got ${htmlNames.join(", ")}`);
  const coverHtml = await fs.readFile(path.join(workDirectory, htmlNames[0]), "utf8");
  const bodyHtml = await fs.readFile(path.join(workDirectory, htmlNames[1]), "utf8");
  const controlsByPage = await Promise.all(htmlNames.map(async name => {
    const html = await fs.readFile(path.join(workDirectory, name), "utf8");
    return [...html.matchAll(/data-memo-control="([^"]+)"/g)].map(match => match[1]);
  }));

  assert.match(coverHtml, /<h1 class="memo-title" data-render-title>海外营销，不是把国内爆款翻译成英文<\/h1>/);
  assert.match(coverHtml, /第 1 段保留母稿原文/);
  for (const controls of controlsByPage) {
    assert.deepEqual(controls, ["back", "undo", "redo", "share", "more"]);
  }
  assert.match(coverHtml, />返回</);
  assert.match(bodyHtml, />返回</);
  for (const html of [coverHtml, bodyHtml]) {
    for (const control of ["back", "undo", "redo", "share", "more"]) {
      assert.match(
        html,
        new RegExp(`data-memo-control="${control}"[^>]*>[\\s\\S]*?<svg\\b[^>]*data-memo-icon="${control}"`),
        `${control} must use its own stable SVG`,
      );
    }
    assert.equal([...html.matchAll(/data-memo-icon="(?:back|undo|redo|share|more)"/g)].length, 5);
  }
  assert.doesNotMatch(bodyHtml, /[↶↷]/);
  assert.doesNotMatch(bodyHtml, /page-number|progress|category-tag|<hr/);
  assert.match(bodyHtml, /--memo-paper:#fff/);
  assert.match(bodyHtml, /--memo-ink:#4a4a4a/);
  assert.match(bodyHtml, /--memo-gold:#d0ac2b/);
  await fs.access(path.join(directory, "pages.json"));
  await fs.access(path.join(directory, "pagination.txt"));
});

test("五列表格准备成两个白底真实 table DOM 并重复关键列", async t => {
  const directory = await createFixture(t, {
    title: "渠道选择要能经得起追问",
    body: [
      "同一个目标，在不同渠道需要不同证据。",
      [
        "| 岗位 | 用户 | 场景 | 动作 | 指标 |",
        "| --- | --- | --- | --- | --- |",
        "| 海外运营 | 消费者 | 首页 | 引导完成观看 | 完播率 |",
      ].join("\n"),
    ].join("\n\n"),
  });

  runCli(directory, true);

  const workDirectory = path.join(directory, "_render-work");
  const htmlNames = (await fs.readdir(workDirectory)).filter(name => /^page-\d{2}\.html$/.test(name)).sort();
  const html = (await Promise.all(htmlNames.map(name => fs.readFile(path.join(workDirectory, name), "utf8")))).join("\n");
  const tableCount = [...html.matchAll(/<table\b/g)].length;
  const tableHeadCount = [...html.matchAll(/<thead\b/g)].length;
  const keyColumnCount = [...html.matchAll(/<th[^>]*>岗位<\/th>/g)].length;

  assert.equal(tableCount, 2);
  assert.equal(tableHeadCount, 2);
  assert.equal(keyColumnCount, 2);
  assert.match(html, /\.memo-table,.memo-table th,.memo-table td\{background:#fff/);
  assert.doesNotMatch(html, /(?:\.memo-table|\.memo-table th|\.memo-table thead)[^{]*\{[^}]*background:(?!#fff|white|transparent)/);
  assert.doesNotMatch(html, /\|\s*:?-{3,}:?\s*\|/);
});

test("母稿段落、多页列表与表格按顺序完整进入 pages 和 HTML", async t => {
  const paragraphs = ["顺序段落 P01。", "顺序段落 P02。", "顺序段落 P03。"];
  const heading = "顺序标题 H01";
  const items = Array.from({ length: 10 }, (_, index) =>
    `顺序列表 L${String(index + 1).padStart(2, "0")}：${"完整条目跨页但内部不拆分。".repeat(4)}`);
  const tableHeader = ["岗位键", "用户列", "场景列", "动作列", "指标列"];
  const tableRows = [
    ["岗位 R01", "用户 U01", "场景 S01", "动作 A01", "指标 M01"],
    ["岗位 R02", "用户 U02", "场景 S02", "动作 A02", "指标 M02"],
  ];
  const tableMarkdown = [
    `| ${tableHeader.join(" | ")} |`,
    "| --- | --- | --- | --- | --- |",
    ...tableRows.map(row => `| ${row.join(" | ")} |`),
  ].join("\n");
  const directory = await createFixture(t, {
    title: "按母稿顺序验证完整渲染",
    body: [
      paragraphs[0],
      paragraphs[1],
      items.map(item => `- ${item}`).join("\n"),
      paragraphs[2],
      `## ${heading}`,
      tableMarkdown,
    ].join("\n\n"),
  });

  await renderPackage(directory, { prepareOnly: true });
  const pages = JSON.parse(await fs.readFile(path.join(directory, "pages.json"), "utf8"));
  const semanticText = pages.flatMap(page => page.blocks.flatMap(block => {
    if (block.type === "list") return block.items;
    if (block.type === "paragraph" || block.type === "heading") return [block.renderedText];
    return [];
  }));
  assert.deepEqual(semanticText, [paragraphs[0], paragraphs[1], ...items, paragraphs[2], heading]);
  assert.ok(pages.filter(page => page.blocks.some(block => block.type === "list")).length >= 2);

  const expectedTableGroups = [
    {
      header: tableHeader.slice(0, 4),
      rows: tableRows.map(row => row.slice(0, 4)),
    },
    {
      header: [tableHeader[0], tableHeader[4]],
      rows: tableRows.map(row => [row[0], row[4]]),
    },
  ];
  const pageTables = pages.flatMap(page => page.blocks.filter(block => block.type === "table"));
  for (const table of pageTables) {
    assert.ok(expectedTableGroups.some(group =>
      JSON.stringify(table.header) === JSON.stringify(group.header)));
    assert.ok(table.rows.length > 0, "unexpected header-only table repeat");
  }
  for (const group of expectedTableGroups) {
    const matching = pageTables.filter(table => JSON.stringify(table.header) === JSON.stringify(group.header));
    assert.ok(matching.length >= 1);
    const matchingPages = pages.filter(page => page.blocks.some(block =>
      block.type === "table" && JSON.stringify(block.header) === JSON.stringify(group.header)));
    assert.equal(matching.length, matchingPages.length, "duplicate table header on one page");
    assert.deepEqual(matching.flatMap(table => table.rows), group.rows);
  }

  const htmlNames = (await fs.readdir(path.join(directory, "_render-work")))
    .filter(name => /^page-\d{2}\.html$/.test(name)).sort();
  const htmlPages = await Promise.all(htmlNames.map(name =>
    fs.readFile(path.join(directory, "_render-work", name), "utf8")));
  const html = htmlPages.join("\n");
  assert.deepEqual(tagTexts(html, "p"), paragraphs);
  assert.deepEqual(tagTexts(html, "li"), items);
  assert.deepEqual(tagTexts(html, "h2"), [heading]);

  let priorPosition = -1;
  for (const value of [paragraphs[0], paragraphs[1], ...items, paragraphs[2], heading]) {
    const position = html.indexOf(value, priorPosition + 1);
    assert.ok(position > priorPosition, `missing or reordered HTML content: ${value}`);
    priorPosition = position;
  }

  const htmlTables = htmlPages.flatMap(pageHtml => [...pageHtml.matchAll(/<table\b.*?<\/table>/gs)]
    .map(match => ({
      header: tagTexts(match[0], "th"),
      rows: [...match[0].matchAll(/<tr data-table-row="\d+">(.*?)<\/tr>/gs)]
        .map(row => tagTexts(row[1], "td")),
    })));
  assert.deepEqual(htmlTables, pageTables.map(table => ({ header: table.header, rows: table.rows })));
});

test("真实截图连续输出且表格行不越过正文底线", async t => {
  const rows = Array.from({ length: 10 }, (_, index) =>
    `| 场景 ${index + 1} | 海外用户的具体问题与限制条件 | 内容触达 | 对比后行动 | 指标 ${index + 1} |`).join("\n");
  const directory = await createFixture(t, {
    title: "渠道策略必须回到用户任务",
    body: [
      ...Array.from({ length: 8 }, (_, index) => `第 ${index + 1} 段说明渠道选择背后的用户任务和证据链。`),
      "## 渠道证据表",
      [
        "| 岗位 | 用户 | 场景 | 动作 | 指标 |",
        "| --- | --- | --- | --- | --- |",
        rows,
      ].join("\n"),
      "表格之后的结论仍然保持原文，不添加任何页脚或解释。",
    ].join("\n\n"),
  });

  runCli(directory);

  const imageNames = (await fs.readdir(directory)).filter(name => /^\d{2}\.png$/.test(name)).sort();
  assert.ok(imageNames.length >= 3, `expected cover, body and table pages, got ${imageNames.join(", ")}`);
  assert.deepEqual(imageNames, imageNames.map((_, index) => `${String(index + 1).padStart(2, "0")}.png`));
  for (const imageName of imageNames) {
    const png = await fs.readFile(path.join(directory, imageName));
    assert.equal(png.toString("ascii", 1, 4), "PNG");
    assert.equal(png.readUInt32BE(16), 1080);
    assert.equal(png.readUInt32BE(20), 1440);
  }

  const stats = JSON.parse(await fs.readFile(path.join(directory, "render-stats.json"), "utf8"));
  assert.equal(stats.overflowCount, 0);
  assert.deepEqual(stats.filenames, imageNames);
  assert.ok(stats.results.every(result => result.toolbar), "expected final-browser toolbar geometry on every page");
  assert.ok(stats.results.every(result => Number.isFinite(result.availableHeight) && Number.isFinite(result.fillRatio)));
  const expectedToolbar = {
    left: 31, top: 29, right: 1028, bottom: 105, width: 997, height: 76,
  };
  const expectedControls = [
    { name: "back", left: 31, top: 47, right: 148, bottom: 87, width: 117, height: 40, color: "rgb(208, 172, 43)" },
    { name: "undo", left: 578, top: 39, right: 634, bottom: 95, width: 56, height: 56, color: "rgb(208, 172, 43)" },
    { name: "redo", left: 694, top: 39, right: 750, bottom: 95, width: 56, height: 56, color: "rgb(197, 197, 197)" },
    { name: "share", left: 838, top: 41, right: 884, bottom: 93, width: 46, height: 52, color: "rgb(208, 172, 43)" },
    { name: "more", left: 972, top: 39, right: 1028, bottom: 95, width: 56, height: 56, color: "rgb(208, 172, 43)" },
  ];
  for (const result of stats.results) {
    assert.deepEqual(result.toolbar.bounds, expectedToolbar);
    assert.deepEqual(result.toolbar.controls.map(control => ({
      name: control.name,
      left: control.left,
      top: control.top,
      right: control.right,
      bottom: control.bottom,
      width: control.width,
      height: control.height,
      color: control.color,
    })), expectedControls);
    assert.ok(result.toolbar.visible);
    assert.ok(result.toolbar.controls.every(control => control.visible));
    assert.equal(result.toolbar.backLabel.text, "返回");
    assert.equal(result.toolbar.backLabel.lineCount, 1, "back label must stay on one horizontal line");
  }
  const tableRows = stats.results.flatMap(result =>
    (result.tableRows || []).map(row => ({ ...row, limit: result.contentBottomLimit })));
  assert.ok(tableRows.length >= 10);
  assert.equal(tableRows.filter(row => row.bottom > row.limit).length, 0);
});

test("长结构化母稿不会生成稀疏尾页", async t => {
  const sections = Array.from({ length: 5 }, (_, sectionIndex) => [
    `## 第 ${sectionIndex + 1} 个判断`,
    ...Array.from({ length: 5 }, (_, paragraphIndex) =>
      `第 ${sectionIndex + 1} 组第 ${paragraphIndex + 1} 段说明岗位判断必须落到具体用户、业务场景、本人动作、交付结果和可验证证据，不能只报平台名称。`),
  ].join("\n\n"));
  const directory = await createFixture(t, {
    title: "长稿不能多出空尾页",
    body: [
      "很多同学会先报岗位名称，却没有说明自己能解决什么问题。",
      "真正需要比较的是用户、场景、动作、结果和证据。",
      ...sections,
    ].join("\n\n"),
  });

  try {
    await renderPackage(directory);
  } catch (error) {
    assert.fail(JSON.stringify(error.report || { code: error.code, message: error.message }));
  }
  const stats = JSON.parse(await fs.readFile(path.join(directory, "render-stats.json"), "utf8"));
  assert.ok(stats.pageCount >= 3);
  assert.ok(stats.results.at(-1).fillRatio >= 0.78, `sparse final page: ${stats.results.at(-1).fillRatio}`);
});

test("首图语义块无法继续容纳时自动平衡留白并通过封面密度校验", async t => {
  const source = JSON.parse(await fs.readFile(
    new URL("./fixtures/underfilled-cover-source.json", import.meta.url),
    "utf8",
  ));
  const directory = await createFixture(t, source);

  let report;
  try {
    report = await renderPackage(directory);
  } catch (error) {
    assert.fail(JSON.stringify(error.report || { code: error.code, message: error.message }));
  }
  assert.equal(report.validation.ok, true);
  assert.ok(report.results[0].fillRatio >= 0.78, `sparse cover: ${report.results[0].fillRatio}`);
  assert.equal(report.validation.exactText, true);
});

test("真实长稿会全局平衡而不是留下近空尾页", async t => {
  const directory = await createFixture(t, {
    title: "27届秋招提前批启动后，先把这3件事做成“可投状态”",
    body: [
      "一篇8月2日的小红书笔记称：“上周新开98家，近3天新开66家。”",
      "很多27届看到这种节奏，第一反应是：赶紧多投。",
      "但如果届次、岗位和简历还没对齐，投得早不等于投得准。**提前批启动后，最重要的不是把投递量拉满，而是先把校招身份、目标岗位池和首版材料连成一条可验证的求职链。**",
      "## 先别给自己盖“27届”的章，企业认的是具体毕业日期",
      "“27届”是方便交流的标签，不是自动生效的校招资格。真正影响网申的是学校确认的毕业日期、企业写明的招聘对象，以及你能否赶上提前批、正式秋招、补录和春招的具体窗口。",
      "一年制硕士、海外毕业或特殊学制尤其要逐家公司核验。不要只在群里问一句“我算哪届”，要把学校确认的毕业年月、企业官方口径、申请截止时间、预计入职时间和待确认项放进同一张时间表。",
      "比如你准备投AI产品经理提前批，岗位页面如果只写“面向2027届”，却没有覆盖你的毕业月份，就先把它标成待确认项，通过企业官方招聘渠道核验。**资格没确认前，海投不会增加有效机会，只会更早制造错届申请。**",
      "## 公司收藏夹不是岗位池，十份真实JD才开始说明问题",
      "收藏了几十家公司，不等于你知道自己要投什么。先从2—4个可能方向里选出主线和备选，比较背景匹配、现有证据、市场机会、进入门槛和准备成本，再决定资源往哪里放。",
      "接着抽取至少10份仍可核验的真实JD，记录岗位要解决的业务问题、服务对象、协作方、必备能力、招聘状态和信息日期。公司池只是研究与投递范围，不代表这些岗位当前一定有HC。",
      "同样叫AI产品经理，有的岗位要解决海外ToB销售提效，有的岗位要搭建模型评测平台。前者会追问销售流程、用户触点和业务取舍；后者更关心评测集、指标设计和模型问题定位。**岗位名相同，企业要买的能力可能完全不同。**",
      "所以，同名岗位只要职责明显不同，就重新分组。你的岗位池至少要能回答：主投哪一类问题、现有哪项经历能证明、还缺什么，以及用哪次投递或访谈验证判断。",
      "## 能直接投的简历，要让HR快速找到四个答案",
      "首版简历先解决检索问题：毕业时间是什么，求职方向是什么，实习时间线是否清楚，哪段经历最能证明岗位匹配。招聘方需要翻找的信息越多，你的真实优势越容易被版式和通用表述埋掉。",
      "然后把高优先级JD要求逐条映射到真实项目、实习、课程或作品：这条要求由哪项事实证明，放在简历哪里，还有什么缺口。一份简历服务一个主投方向，不要让一版“万能简历”同时回答产品、数据和运营三个不同问题。",
      "比如数据分析岗要解决经营异常定位，并把结论交给运营或业务团队。简历里只写“熟练SQL、Python、Tableau”还不够；更有效的证据是你定义过什么指标、怎样定位异常、产出了什么分析报告，以及结论被谁用于什么决策。",
      "**可投不是“排版完成”，而是JD上的关键问题都能在简历中找到真实答案。**定稿后再检查PDF预览、分页和文件名，确保提交出去的版本与自己确认的版本一致。",
      "## 写进简历的能力，先用“为什么做”验一次真",
      "有一位主投AI产品方向的校招生，在参加30多场暑期实习面试后复盘：技术追问并非主要卡点，真正难的是面试官继续问“为什么做、为谁做、为什么这样选”。这不是说技术不重要，而是说明术语能换来追问，换不来可信度。",
      "如果简历写“设计销售Agent”，面试官可能继续问：原流程卡在哪里？服务的是销售、客户还是管理者？为什么先做这个节点？Demo和MVP分别验证了什么？谁看过交付，结果怎样确认？",
      "每段重点经历都要说清五件事：任务从哪里来，本人边界是什么，做了哪些关键判断与动作，交付给谁，结果如何验证。数字还要区分目标、预估和已实现，不能把业务测算写成落地收益。",
      "**答不出的内容，不该被包装成已经具备的能力。**可以删掉、降级成参与项，或先补流程图、分析报告、原型、评测结果等证据，再决定是否写回简历。",
      "## 用72小时跑通一次，再开始小批量投递",
      "- 当天：向学校确认毕业日期，逐个查看目标企业的官方招聘对象，把提前批、正式秋招、补录、春招、截止时间和待确认项写进一张时间表。\n\n- 第二天：完成至少10份真实JD的岗位池，按职责重新分组，定下一条主线和一条备选；每条线都写清现有证据、关键缺口和下一步验证动作。\n\n- 第三天：输出一份主投方向的PDF简历，并为两段重点项目写追问提纲。至少覆盖“为什么做、为谁做、本人做了什么、为什么这样选、结果如何验证”。",
      "随后再小批量投递，记录岗位、版本、结果和追问。过筛反馈差，就检查届次、岗位或材料是否错位；进入面试后卡在业务深挖，就回到证据和项目逻辑继续补。",
      "最后提醒：开头两个数字只是那篇笔记作者对其整理范围的陈述，统计口径和覆盖范围不明。公司是否开放、27届认定范围，以及提前批失败是否影响后续批次，都以企业官方页面为准。**这三件事不能保证过筛，但能让你的每次投递更接近一次有效验证。**",
    ].join("\n\n"),
  });

  let report;
  try {
    report = await renderPackage(directory);
  } catch (error) {
    assert.fail(JSON.stringify(error.report || { code: error.code, message: error.message }));
  }
  assert.equal(report.validation.ok, true);
  assert.ok(report.results.at(-1).fillRatio >= 0.67);
});

test("真实表格长稿会在不改字的前提下平衡尾页纵向节奏", async t => {
  const source = JSON.parse(await fs.readFile(
    new URL("./fixtures/underfilled-tail-source.json", import.meta.url),
    "utf8",
  ));
  const directory = await createFixture(t, source);

  let report;
  try {
    report = await renderPackage(directory);
  } catch (error) {
    assert.fail(JSON.stringify(error.report || { code: error.code, message: error.message }));
  }
  assert.equal(report.validation.ok, true);
  assert.ok(report.results.at(-1).fillRatio >= 0.67);
  assert.equal(report.validation.exactText, true);
  const pages = JSON.parse(await fs.readFile(path.join(directory, "pages.json"), "utf8"));
  assert.ok(pages.at(-1).tailBlockGap > 0 && pages.at(-1).tailBlockGap <= 24);
});
