# Render and Acceptance

## Completion sequence

先锁定目标格式，再按该格式完成结构读回和最终渲染验收；目标格式不同，视觉载体可以不同，但 `no_visual_reason` 和失败状态必须可追溯。

1. Render or export the actual target format.
2. Read back title hierarchy, visual count, visual position, caption, source, fact boundary, and media identifiers.
3. Inspect every rendered page or equivalent full surface at normal desktop zoom.
4. Fix clipping, overlap, tiny labels, broken legends, table overflow, bad page breaks, or visual/text separation.
5. Render again and repeat the full inspection.
6. Record the final result in `visual_contract` and run the shared validator.

## Format-specific checks

### Feishu

- 飞书中的讲解图默认以图片嵌入对应正文，紧邻讲解；保留既有有效画板。用户明确选择画板时按其范围处理，完整专岗仍以可见正文图片验收。简单线性内容可不配图，但写明具体 `no_visual_reason`。
- Use `lark-cli` for structural readback when available.
- 读回图片／画板块的非空 token 或 src、块顺序、标题、图注、父级章节和实际位置；再查看实际学生端、导出 PDF 或等价渲染，逐图／逐页检查可读性。非空 src 是有效的结构证据，但不证明图片已实际显示。
- Mermaid 或源码只能保留为可编辑来源；目标表面需显示清晰可读的成图。链接、附件和首屏预览不代替正文嵌入。
- Export to PDF or use an equivalent student-facing render for every-page inspection.

### Word and PDF

- Use the document/PDF workflow appropriate to the file type.
- Render the document to page images and inspect every page.
- Check page breaks, figure anchoring, table width, margins, font size, and captions.

### Markdown and HTML

- Keep diagram source or chart data traceable.
- Validate the rendered output, not only Markdown text or Mermaid syntax.
- If the target renderer does not support the diagram, export a readable image or use a native relationship table.

## Required manifest shape

```json
{
  "skill": "domain-skill-name",
  "visual_contract": {
    "substantial": true,
    "complexity_signals": ["multi_step_flow"],
    "required_visual_ids": ["business-flow"],
    "visual_plan": [
      {
        "id": "business-flow",
        "type": "flowchart",
        "reason": "Explains a branched workflow.",
        "section": "Business flow",
        "fact_boundary": "Inferred",
        "caption": "Public abstraction, not internal architecture.",
        "source_note": "Official public pages and supplied JD."
      }
    ],
    "readback": {
      "media_blocks": [
        {"visual_id": "business-flow", "token": "non-empty-token", "section": "Business flow"}
      ]
    },
    "render_qa": {
      "page_count": 3,
      "checked_pages": [1, 2, 3],
      "checked_items": ["clipping", "readability", "layout", "caption"],
      "issues": []
    }
  }
}
```

For a simple artifact without visuals, set `substantial` to `false`, keep `visual_plan` empty, and provide a concrete `no_visual_reason`.

Media readback may use a non-empty `token` or `src`, according to the actual returned block. Preserve the original identifier; do not invent a token for an image returned with `src`. The validator checks the manifest's declared fields only. It does not open media or prove that the stated page review occurred.

For AI-generated figures, inspect the final image at the actual reading width: every Chinese character, number, formula, arrow endpoint, decision branch, loop and terminal state must match the locked source logic. Fix errors before embedding, then inspect the embedded display again. A correct standalone image can still be clipped or too small in the document.

## Failure conditions

Delivery remains incomplete when any required visual is missing, both token and src are empty, a caption/source/fact boundary is absent, page review is partial, or render issues remain unresolved. CLI success, HTTP 200, revision changes, syntax validation, or a static source screenshot do not override these failures.
