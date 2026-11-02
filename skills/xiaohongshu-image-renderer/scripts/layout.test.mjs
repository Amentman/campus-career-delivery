import assert from "node:assert/strict";
import test from "node:test";

import {
  paginateMeasuredBlocks,
  parseMarkdownBlocks,
  splitParagraphsIntoSentences,
  splitWideTables,
} from "./layout.mjs";

const fiveColumnTable = {
  type: "table",
  markdown: "| 岗位 | 用户 | 场景 | 动作 | 指标 |\n| --- | --- | --- | --- | --- |\n| 运营 | 消费者 | 首页 | 引导 | 完播率 |",
  renderedText: "岗位 | 用户 | 场景 | 动作 | 指标\n运营 | 消费者 | 首页 | 引导 | 完播率",
  header: ["岗位", "用户", "场景", "动作", "指标"],
  alignments: ["left", "left", "left", "left", "left"],
  rows: [["运营", "消费者", "首页", "引导", "完播率"]],
  sourceColumnIndexes: [0, 1, 2, 3, 4],
  repeatedKeyColumn: false,
};

const table = {
  type: "table",
  markdown: "| 岗位 | 指标 |\n| --- | --- |\n| 运营 | 完播率 |\n| 产品 | 留存率 |\n| 销售 | 转化率 |",
  renderedText: "岗位 | 指标\n运营 | 完播率\n产品 | 留存率\n销售 | 转化率",
  header: ["岗位", "指标"],
  alignments: ["left", "left"],
  rows: [
    ["运营", "完播率"],
    ["产品", "留存率"],
    ["销售", "转化率"],
  ],
  sourceColumnIndexes: [0, 1],
  repeatedKeyColumn: false,
};

test("标准 Markdown 表格解析成真实结构块", () => {
  const blocks = parseMarkdownBlocks(`开头。\n\n| 岗位 | 用户 | 指标 |\n|:---|:---:|---:|\n| 运营 | 消费者 | 完播率 |`);

  assert.equal(blocks[1].type, "table");
  assert.deepEqual(blocks[1].header, ["岗位", "用户", "指标"]);
  assert.deepEqual(blocks[1].alignments, ["left", "center", "right"]);
  assert.deepEqual(blocks[1].rows, [["运营", "消费者", "完播率"]]);
});

test("解析器保留转义竖线并拒绝列数错误的表格行", () => {
  const [block] = parseMarkdownBlocks(`| 字段 | 内容 |\n| --- | --- |\n| 示例 | A\\|B |`);
  assert.deepEqual(block.rows, [["示例", "A|B"]]);

  const [emojiPrefixedBlock] = parseMarkdownBlocks("😀\\|内容\n---");
  assert.equal(emojiPrefixedBlock.type, "paragraph");

  assert.throws(
    () => parseMarkdownBlocks(`| 字段 | 内容 |\n| --- | --- |\n| 只有一列 |`),
    error => error.code === "MALFORMED_TABLE_ROW",
  );
});

test("长段落只在完整句号后拆分并逐字保留 Markdown", () => {
  const markdown = "第一句说明背景。第二句保留**关键判断**！第三句带英文 question? 第四句收束。";
  const [paragraph] = parseMarkdownBlocks(markdown);

  const units = splitParagraphsIntoSentences([paragraph]);

  assert.deepEqual(units.map(unit => unit.markdown), [
    "第一句说明背景。",
    "第二句保留**关键判断**！",
    "第三句带英文 question? ",
    "第四句收束。",
  ]);
  assert.equal(units.map(unit => unit.markdown).join(""), markdown);
  assert.ok(units.every(unit => unit.type === "paragraph-sentence"));
  assert.deepEqual(units.map(unit => unit.sourceSentenceIndex), [0, 1, 2, 3]);
  assert.equal(units.at(-1).isLastSentence, true);
});

test("句末后的下一句加粗标记不会被吞到前一句", () => {
  const markdown = "第一句结束。**第二句完整加粗。**第三句继续。";
  const [paragraph] = parseMarkdownBlocks(markdown);

  const units = splitParagraphsIntoSentences([paragraph]);

  assert.deepEqual(units.map(unit => unit.markdown), [
    "第一句结束。",
    "**第二句完整加粗。**",
    "第三句继续。",
  ]);
  assert.equal(units.map(unit => unit.markdown).join(""), markdown);
});

test("五列表格分成两组并只结构性重复首列", () => {
  const [first, second] = splitWideTables([fiveColumnTable], 4);

  assert.deepEqual(first.sourceColumnIndexes, [0, 1, 2, 3]);
  assert.deepEqual(second.sourceColumnIndexes, [0, 4]);
  assert.equal(second.repeatedKeyColumn, true);
  assert.deepEqual(second.header, ["岗位", "指标"]);
  assert.deepEqual(second.rows, [["运营", "完播率"]]);
});

test("表格行不跨页并在续页重复表头", () => {
  const pages = paginateMeasuredBlocks([table], {
    firstCapacity: 600,
    bodyCapacity: 900,
    measure: block => block.type === "table-row" ? 320 : 100,
  });

  assert.equal(pages.length, 2);
  assert.equal(pages[1].blocks[0].type, "table-header");
  assert.equal(
    pages.flatMap(page => page.blocks).filter(block => block.type === "table-row").length,
    table.rows.length,
  );
});

test("超过正文页容量的单个表格行以 ROW_TOO_TALL 失败", () => {
  assert.throws(
    () => paginateMeasuredBlocks([table], {
      firstCapacity: 600,
      bodyCapacity: 300,
      measure: block => block.type === "table-row" ? 320 : 100,
    }),
    error => error.code === "ROW_TOO_TALL",
  );
});
