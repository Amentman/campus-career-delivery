const TABLE_DELIMITER = /^:?-{3,}:?$/;

export function parseMarkdownBlocks(markdown) {
  const lines = String(markdown).replace(/\r\n?/g, "\n").split("\n");
  const blocks = [];

  for (let index = 0; index < lines.length;) {
    if (!lines[index].trim()) {
      index += 1;
      continue;
    }

    if (isTableStart(lines, index)) {
      const header = splitTableCells(lines[index]);
      const delimiter = splitTableCells(lines[index + 1]);
      const rows = [];
      const tableLines = [lines[index], lines[index + 1]];
      index += 2;

      while (index < lines.length && lines[index].trim() && hasUnescapedPipe(lines[index])) {
        const row = splitTableCells(lines[index]);
        if (row.length !== header.length) {
          throw layoutError("MALFORMED_TABLE_ROW", "Table row width does not match its header.");
        }
        rows.push(row);
        tableLines.push(lines[index]);
        index += 1;
      }

      blocks.push(createTableBlock({
        markdown: tableLines.join("\n"),
        header,
        alignments: delimiter.map(parseAlignment),
        rows,
      }));
      continue;
    }

    const heading = lines[index].match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      blocks.push({ type: "heading", markdown: lines[index], renderedText: heading[2].trim(), level: heading[1].length });
      index += 1;
      continue;
    }

    if (/^\s*[-*+]\s+/.test(lines[index])) {
      const listLines = [];
      const items = [];
      while (index < lines.length && /^\s*[-*+]\s+/.test(lines[index])) {
        listLines.push(lines[index]);
        items.push(lines[index].replace(/^\s*[-*+]\s+/, "").trim());
        index += 1;
      }
      blocks.push({ type: "list", markdown: listLines.join("\n"), renderedText: items.join("\n"), items });
      continue;
    }

    const paragraphLines = [];
    while (index < lines.length && lines[index].trim() && !isTableStart(lines, index) && !/^(#{1,6})\s+/.test(lines[index]) && !/^\s*[-*+]\s+/.test(lines[index])) {
      paragraphLines.push(lines[index]);
      index += 1;
    }
    blocks.push({ type: "paragraph", markdown: paragraphLines.join("\n"), renderedText: paragraphLines.join("\n").trim() });
  }

  return blocks;
}

export function splitParagraphsIntoSentences(blocks) {
  let sourceParagraphIndex = 0;
  return blocks.flatMap(block => {
    if (block.type !== "paragraph") return [block];
    const paragraphIndex = sourceParagraphIndex;
    sourceParagraphIndex += 1;
    const sentences = splitSentenceMarkdown(block.markdown);
    return sentences.map((markdown, sourceSentenceIndex) => ({
      type: "paragraph-sentence",
      sourceParagraphIndex: paragraphIndex,
      sourceSentenceIndex,
      isLastSentence: sourceSentenceIndex === sentences.length - 1,
      markdown,
      renderedText: markdown,
    }));
  });
}

export function splitWideTables(blocks, maxColumns = 4) {
  if (!Number.isInteger(maxColumns) || maxColumns < 2) {
    throw new RangeError("maxColumns must be an integer of at least 2.");
  }

  return blocks.flatMap(block => {
    if (block.type !== "table" || block.header.length <= maxColumns) {
      return [block];
    }

    const sourceIndexes = block.sourceColumnIndexes ?? block.header.map((_, index) => index);
    const groups = [Array.from({ length: maxColumns }, (_, index) => index)];
    for (let index = maxColumns; index < block.header.length; index += maxColumns - 1) {
      groups.push([0, ...Array.from({ length: maxColumns - 1 }, (_, offset) => index + offset)
        .filter(columnIndex => columnIndex < block.header.length)]);
    }

    return groups.map((columnIndexes, groupIndex) => createTableBlock({
      markdown: tableMarkdown(
        columnIndexes.map(columnIndex => block.header[columnIndex]),
        columnIndexes.map(columnIndex => block.alignments[columnIndex]),
        block.rows.map(row => columnIndexes.map(columnIndex => row[columnIndex])),
      ),
      header: columnIndexes.map(columnIndex => block.header[columnIndex]),
      alignments: columnIndexes.map(columnIndex => block.alignments[columnIndex]),
      rows: block.rows.map(row => columnIndexes.map(columnIndex => row[columnIndex])),
      sourceColumnIndexes: columnIndexes.map(columnIndex => sourceIndexes[columnIndex]),
      repeatedKeyColumn: groupIndex > 0,
    }));
  });
}

export function paginateMeasuredBlocks(blocks, options) {
  const { firstCapacity, bodyCapacity, measure } = options;
  if (typeof measure !== "function") {
    throw new TypeError("measure must be a function.");
  }

  const pages = [];
  let page = null;

  const newPage = capacity => {
    page = { blocks: [], capacity, used: 0 };
    pages.push(page);
  };
  const ensurePage = () => {
    if (!page) newPage(firstCapacity);
  };
  const append = block => {
    const size = measure(block);
    ensurePage();
    if (size > page.capacity - page.used) {
      if (size > bodyCapacity) throw layoutError("BLOCK_TOO_TALL", "Block exceeds page capacity.");
      newPage(bodyCapacity);
    }
    page.blocks.push(block);
    page.used += size;
  };

  for (const block of blocks) {
    if (block.type !== "table") {
      append(block);
      continue;
    }

    const header = { type: "table-header", table: block, header: block.header, alignments: block.alignments };
    const headerSize = measure(header);
    if (headerSize > bodyCapacity) throw layoutError("TABLE_HEADER_TOO_TALL", "Table header exceeds page capacity.");

    const startTablePage = () => {
      ensurePage();
      if (headerSize > page.capacity - page.used) newPage(bodyCapacity);
      page.blocks.push(header);
      page.used += headerSize;
    };

    startTablePage();
    for (const values of block.rows) {
      const row = { type: "table-row", table: block, values };
      const rowSize = measure(row);
      if (rowSize > bodyCapacity) throw layoutError("ROW_TOO_TALL", "Table row exceeds body page capacity.");
      if (rowSize > page.capacity - page.used) {
        newPage(bodyCapacity);
        if (headerSize + rowSize > bodyCapacity) {
          throw layoutError("ROW_TOO_TALL", "Table row cannot fit with its repeated header.");
        }
        page.blocks.push(header);
        page.used += headerSize;
      }
      page.blocks.push(row);
      page.used += rowSize;
    }
  }

  return pages;
}

function isTableStart(lines, index) {
  if (index + 1 >= lines.length || !hasUnescapedPipe(lines[index])) return false;
  const header = splitTableCells(lines[index]);
  const delimiter = splitTableCells(lines[index + 1]);
  return header.length > 0 && delimiter.length === header.length && delimiter.every(cell => TABLE_DELIMITER.test(cell));
}

function splitSentenceMarkdown(markdown) {
  const source = String(markdown);
  const sentences = [];
  let start = 0;
  for (let index = 0; index < source.length; index += 1) {
    if (!/[。！？!?]/u.test(source[index])) continue;
    let end = index + 1;
    while (end < source.length && /[”’」』》）)\]】]/u.test(source[end])) end += 1;
    const openBoldMarker = (source.slice(start, end).match(/\*\*/g) || []).length % 2 === 1;
    if (openBoldMarker && source.startsWith("**", end)) end += 2;
    while (end < source.length && /\s/u.test(source[end])) end += 1;
    sentences.push(source.slice(start, end));
    start = end;
    index = end - 1;
  }
  if (start < source.length) sentences.push(source.slice(start));
  return sentences.length > 0 ? sentences : [source];
}

function splitTableCells(line) {
  const source = line.trim();
  const cells = [];
  let cell = "";
  let escaped = false;

  for (const character of source) {
    if (character === "|" && !escaped) {
      cells.push(cell.trim().replace(/\\\|/g, "|"));
      cell = "";
      continue;
    }
    cell += character;
    escaped = character === "\\" ? !escaped : false;
  }
  cells.push(cell.trim().replace(/\\\|/g, "|"));

  if (source.startsWith("|")) cells.shift();
  if (source.endsWith("|") && !isEscaped(source, source.length - 1)) cells.pop();
  return cells;
}

function hasUnescapedPipe(line) {
  for (let index = 0; index < line.length; index += 1) {
    if (line[index] === "|" && !isEscaped(line, index)) return true;
  }
  return false;
}

function isEscaped(value, index) {
  let slashes = 0;
  for (let cursor = index - 1; cursor >= 0 && value[cursor] === "\\"; cursor -= 1) slashes += 1;
  return slashes % 2 === 1;
}

function parseAlignment(delimiter) {
  const left = delimiter.startsWith(":");
  const right = delimiter.endsWith(":");
  if (left && right) return "center";
  if (right) return "right";
  return "left";
}

function createTableBlock({ markdown, header, alignments, rows, sourceColumnIndexes = header.map((_, index) => index), repeatedKeyColumn = false }) {
  return {
    type: "table",
    markdown,
    renderedText: [header, ...rows].map(row => row.join(" | ")).join("\n"),
    header,
    alignments,
    rows,
    sourceColumnIndexes,
    repeatedKeyColumn,
  };
}

function tableMarkdown(header, alignments, rows) {
  const delimiter = alignments.map(alignment => alignment === "center" ? ":---:" : alignment === "right" ? "---:" : ":---");
  return [header, delimiter, ...rows]
    .map(row => `| ${row.map(value => String(value).replace(/\|/g, "\\|")).join(" | ")} |`)
    .join("\n");
}

function layoutError(code, message) {
  const error = new Error(message);
  error.code = code;
  return error;
}
