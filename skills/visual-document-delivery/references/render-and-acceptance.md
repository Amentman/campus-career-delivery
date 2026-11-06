# Render and Acceptance

## Completion sequence

先锁定目标格式，再按该格式完成结构读回和最终渲染验收；目标格式不同，视觉载体可以不同，但 `no_visual_reason` 和失败状态必须可追溯。

1. Render or export the actual target format.
2. Read back title hierarchy, visual count, visual position, caption, source, fact boundary, and media identifiers.
3. Inspect every rendered page for a full document, or every affected section for a local change, at normal desktop zoom. Apply the five figure-quality checks in [figure-quality.md](figure-quality.md) to every in-scope figure.
4. Batch fixes for observed meaning, logic, design, and display defects.
5. Render again and confirm the fixes in one further pass; unresolved defects remain incomplete rather than triggering unbounded cosmetic iterations.
6. Record the final result in `visual_contract` and run the shared validator.

## Format-specific checks

### Feishu

- 飞书讲解图默认用原生画板嵌入对应正文，紧邻讲解；检查画板token、节点、导出和正文实际阅读宽度，已有有效媒体保留。简单线性内容不强行配图，记录具体 `no_visual_reason`。画板内容、逻辑与视觉检查不能被图片数量或CLI成功替代。
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
    },
    "quality_review": [
      {
        "visual_id": "business-flow",
        "reader_question": "Who hands the order to whom?",
        "target_width_px": 760,
        "evidence": ["render/business-flow-at-760.png"],
        "checks": {
          "meaning": "Three service roles attach to their handoff stages.",
          "logic": "Failure ends with dispatch; success ends with delivery.",
          "hierarchy": "The main route is read before its two exception branches.",
          "legibility": "Branch labels are readable at 760px without zooming.",
          "visual_utility": "The route exposes the different owners of both outcomes."
        },
        "verdict": "pass",
        "issues": []
      }
    ]
  }
}
```

For a simple artifact without visuals, set `substantial` to `false`, keep `visual_plan` empty, and provide a concrete `no_visual_reason`.

Media readback may use a non-empty `token` or `src`, according to the actual returned block. Preserve the original identifier; do not invent a token for an image returned with `src`. The validator checks the manifest's declared fields only. It does not open media or prove that the stated page review occurred.

For a local change, `render_qa.scope` may be `affected_sections`. Record non-empty `required_sections`, all `checked_sections`, actual total `page_count`, and the inspected `checked_pages`; compare protected content separately. Otherwise scope defaults to the full `document` and requires every page. All planned figures still need their own `quality_review` record; a complete manifest is not a visual-quality certificate.

For AI-generated figures, inspect the final image at the actual reading width: every Chinese character, number, formula, arrow endpoint, decision branch, loop and terminal state must match the locked source logic. Fix errors before embedding, then inspect the embedded display again. A correct standalone image can still be clipped or too small in the document.

## Failure conditions

Delivery remains incomplete when any required visual is missing, both token and src are empty, a caption/source/fact boundary is absent, review does not cover the declared scope, figure-quality evidence is missing, a figure is marked `revise`/`unverified`, or any review issues remain unresolved. CLI success, HTTP 200, revision changes, syntax validation, or a static source screenshot do not override these failures.
