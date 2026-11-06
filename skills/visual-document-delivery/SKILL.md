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

飞书阅读材料中的讲解图、流程图、关系图和方法总览默认使用飞书原生画板，嵌入对应正文并紧邻讲解；不再默认生成讲解图片。先锁定读者问题、准确文案、关系和阅读路径，再实际应用 `impeccable` 的 Read 模式处理信息层级、字体、对齐、间距、留白和配色。图只承担有助理解的关系，不把正文缩写塞进框，不做大字海报或装饰图凑数。逐字逐线检查，并核对原生节点、画板导出及正文实际阅读宽度；非空token、上传成功或导出成功均不替代视觉验收。非飞书文件使用已验收画板的清晰导出或适合该格式的图；真实统计图可用精确计算工具。用户明确要求图片或确需照片、插画时另选图像工具，并保留相同质量门。

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
- 飞书讲解图默认原生画板，直接置于对应正文；既有有效画板、来源截图和用户指定图片保留。读回画板token、块顺序、章节及原生节点，并检查导出与学生实际阅读宽度；链接、附件和源码不能代替可见画板。不能为统一工具删除有效来源或把文字表格全部画图。
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
- For Feishu explanatory diagrams, use native whiteboards and apply the figure-quality gate. If a board looks weak, redesign the relationship, hierarchy or layout; switching tools alone is not a fix. Use precise computation for quantitative charts. Every label, value, connector, branch, loop and terminal state must match the source. Images are for explicit image requests or content that needs imagery, and require the same checks.
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
- Native board cannot be created or read back: preserve finished content, report the specific limitation, and do not silently substitute a generated poster. For non-Feishu exports use a checked board export or a suitable native table.
