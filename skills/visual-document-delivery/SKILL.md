---
name: visual-document-delivery
description: Use when creating or substantially revising a durable Feishu, Word, PDF, Markdown, or HTML document whose content contains multi-step flows, module relationships, role handoffs, state changes, timelines, comparisons, or trustworthy quantitative data.
---

# Visual Document Delivery

<!-- skill-workflow-link -->
[查看完整流程图与操作说明](references/workflow.md)
<!-- /skill-workflow-link -->

首次供团队成员使用时，先读 [团队配置与依赖](references/team-setup.md)，只配置当前任务所需能力。

## Overview

Turn complex document content into a readable information system. Use diagrams and compact tables only when they make a real relationship easier to understand; visual polish never changes the evidence status of a claim.

## Required references

- Read [visual-decision-matrix.md](references/visual-decision-matrix.md) before choosing a visual or deciding that none is needed.
- Read [layout-and-information-design.md](references/layout-and-information-design.md) when planning a substantial document's hierarchy and reading rhythm.
- Read [render-and-acceptance.md](references/render-and-acceptance.md) before delivery in the target format.
- Read [figure-quality.md](references/figure-quality.md) before drawing or reviewing substantive figures. It defines the comprehension and design gate, separate from upload/render checks.

## First use and available tools

The bundled validator and tests require only Python 3. Rendering, Feishu access, image generation and editable canvases are supplied by the current environment; installing this directory does not connect them. Use available tools according to the target format, and report any missing capability before claiming that surface was inspected.

For a substantial document or figure, apply `impeccable` in Read mode when installed: organize the reading order, hierarchy, typography, alignment, whitespace and color for comprehension. Its upstream package is an external dependency, not part of this directory. Without it, use this directory's layout reference for the authorized work and disclose that the named design tool was unavailable; if the current task explicitly requires that tool, resolve the dependency before claiming compliance.

## Delivery contract

1. Identify the reader, decision, target format, and complex relationships.
2. Create a visual plan before drafting. Use `no_visual_reason` when the artifact is simple and no visual improves comprehension.
3. Draft domain content from its authoritative sources. Keep the meanings of `Confirmed`, `Externally verified`, `Inferred`, `Knowledge supplement`, and `Open` distinguishable. Keep formal labels in the internal evidence ledger; student-facing prose and figures use natural Chinese wording, source notes and clear uncertainty cues, without exposing internal audit or generation steps.
4. Place each visual next to the section it explains. Do not collect unrelated figures at the end.
5. Review figure meaning and design before embedding; after embedding, inspect actual reading width and the affected reading path. For a new or substantially revised document inspect every rendered page. For a local edit compare protected content/media and inspect all affected sections. Batch the observed fixes and confirm them in a second pass; unresolved defects remain explicit rather than entering open-ended polishing.
6. Record the result in a `visual_contract` manifest and run:

```bash
python3 <this-skill-directory>/scripts/validate_visual_manifest.py path/to/visual-manifest.json
```

Resolve `scripts/...` from this Skill's directory; do not assume the caller's current working directory.

## Target-format visual contract

- 先锁定读者、决策和**目标格式**。相同内容在不同交付面可以使用不同的视觉载体，但不能跳过目标格式的结构读回和最终渲染验收。
- 飞书默认把讲解图作为清晰可见的图片嵌入正文对应章节，紧邻讲解；首屏预览、链接、附件或画板不能代替正文图片。保留既有有效画板。用户明确选择可编辑画板时按其范围交付；专岗材料仍需遵守其正文图片要求。读回图片／画板的媒体标识、块顺序与所属章节，再检查实际学生端显示。
- 如果目标格式是 Word、PDF、Markdown 或 HTML，使用该格式能稳定呈现且可读的图、表或关系结构；不要把飞书画板规则强行套到非飞书输出，也不要用不可渲染的 Mermaid 充当验收证据。
- 简单线性内容可以没有视觉，但必须在 `visual_contract` 写出具体 `no_visual_reason`；复杂关系即使篇幅很短也不能以“文档短”为理由省略必要图解。

## When a visual is required

Use the matching visual when the document contains any of these observable signals:

- three or more dependent steps, components, actors, or routes;
- a branch, loop, failure, fallback, handoff, or state transition;
- a time-dependent plan or sequence;
- a comparison whose trade-offs must be read together;
- quantitative change with verified source, definition, period, and units.

Do not force a diagram into a short answer, one resume bullet, a simple script, or a linear explanation that is already clearer in prose.

## Non-negotiable boundaries

- Never invent internal architecture, ownership, metrics, company data, or student experience to complete a figure.
- Label abstractions and inferences inside the figure or caption.
- Choose the tool from the relationship and required precision. For methodology overviews or teaching infographics, lock the exact wording and reading path first; if native or scripted drawing is visually weak, use available GPT image generation instead of repeatedly polishing a poor box diagram. Use precise native/programmatic tools for real quantitative charts, exact coordinates and editable figures. Check every generated label, number, arrow, branch, loop and terminal state before embedding; never change the logic for appearance. If the tool does not expose the model version, do not claim a verified version.
- A successful command, valid Mermaid syntax, non-empty token, or HTTP response is not visual acceptance.
- Unresolved clipping, tiny labels, broken legends, missing captions, empty media, or incomplete page review keeps delivery incomplete.

## Quick reference

| Need | Default form |
| --- | --- |
| Steps, branches, fallback | Flowchart or sequence |
| Inputs, modules, outputs | Architecture |
| Roles and handoffs | Swimlane or collaboration map |
| Stages and dates | Timeline or route map |
| Options, evidence, gaps | Matrix or short comparison table |
| Verified quantitative change | Data chart |
| Fact status and uncertainty | Evidence card or layered relationship |

## Common mistakes

- Decorative image with no explanatory job: remove it.
- Long prose copied into boxes: shorten nodes and return detail to the body.
- Tables used as paragraph containers: keep comparison fields in the table and explanation in prose.
- Figure separated from its explanation: move it to the relevant section.
- Renderer cannot display the chosen format: export a readable image or use a compact native table instead.
