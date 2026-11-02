# Original memo visual contract

The only approved references are the supplied original memo cover and body
screenshots. The renderer must preserve their plain, editorial character.

## Required appearance

- Canvas: exactly `1080 × 1440`, with a flat white paper background.
- Text: deep gray (`#4a4a4a`) in a single fixed-width article column.
- Every page has the original five controls, in this order: back, undo, redo,
  share, more. Back/undo/share/more are memo gold (`#d0ac2b`); redo is gray.
- The toolbar uses the same browser geometry on every page. Its right group
  starts near `x=578` with the wider native-memo spacing; all five controls use
  deterministic inline SVG paths rather than font glyphs or CSS pseudo-icons.
- Cover: large deep-gray title followed by the untouched source article below
  the same five-control toolbar; it must not become a title-only poster.
- If the first complete source sentence cannot fit below the cover title, fail with
  `FIRST_BLOCK_DOES_NOT_FIT_COVER`; never split or rewrite that block and never
  emit an empty cover.
- Typography and pagination are measured in the final browser font and layout.
  A paragraph may continue on a later page only between complete sentences;
  never split inside a sentence. A heading, list item, table header, or table
  row moves as a whole. Sentence fragments from the same source paragraph must
  reassemble byte-for-byte after pagination.
- Use normal document flow so paragraph and heading margins behave like the
  approved memo reference; do not turn the article body into a flex stack.
- For long-form sources with at least 1,200 non-whitespace characters and more
  than one page, globally optimize all page boundaries while preserving every
  semantic atom. Target `fillRatio` is `0.78` for cover/final pages and `0.82`
  for interior pages. Because a complete sentence, list item, or table row can
  make those targets mathematically unreachable, the publishable hard floors
  are `0.78` for the cover, `0.67` for the final page, and `0.72` for interior
  pages. Reject anything below those floors with `UNDERFILLED_PAGE` rather than
  returning an extra near-empty image. Shorter notes may keep intentional
  whitespace.
- If the final page remains only slightly below its hard floor after global
  semantic rebalancing, the renderer may distribute up to `24px` of additional
  vertical space across existing block boundaries on that final page. It must
  keep normal document flow, preserve every source byte and semantic atom, and
  leave the toolbar, font sizes, column geometry, and validation floors
  unchanged. If this bounded adjustment still cannot meet the floor, fail with
  `UNDERFILLED_PAGE`.
- Contiguous Markdown lists may continue across pages only between items. Each
  page reassembles its consecutive items into one `<ul>` without changing,
  duplicating, or reordering any item.
- Tables use real HTML table elements. Cells are white, borders are
  `1px solid #d7d7d7`, headers are bold deep gray, and text wraps readably.
  Tables wider than four columns split into groups that repeat only the first
  key column. Continuations repeat their header only when at least one row from
  that table is present on the page; do not emit orphan header-only fragments.
- Before writing a replacement package, remove only renderer-owned `NN.png`
  files and `_render-work/page-NN.html` files from the prior run.

## Prohibited output

- Do not turn the memo into a poster, card layout, dashboard, or a collection
  of cards.
- Do not add category tags, footers, page numbers, progress indicators,
  metadata, brand marks, divider bands, ornamental icons, illustrations, or
  any other decorative element.
- Do not use dark, tinted, colored, or gradient table headers or cells.
- Do not add, summarize, paraphrase, rewrite, reorder, or silently remove any
  source content. Structural repetition of a table header and its key column
  is the only permitted repetition.
- Do not render raw Markdown table delimiters as visible text.
- Do not use font-dependent undo or redo arrow glyphs.
