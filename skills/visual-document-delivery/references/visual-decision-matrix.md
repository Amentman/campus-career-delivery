# Visual Decision Matrix

## Decide from the relationship, not from a desired image count

先区分关系复杂度与目标格式。飞书中的讲解图默认作为图片嵌入对应正文；Word、PDF、Markdown、HTML 使用其自身可读的图、表或导出图像。保留既有有效画板，用户明确需要可编辑画板时按范围使用。目标格式不改变事实边界，也不取消 `no_visual_reason` 的记录要求。

先确定准确文字、关系和阅读路径，再选工具。方法论总览、教学信息图可使用高质量的图像生成，但每字和每条连接都要验收；真实数据、精确坐标或后续编辑优先用原生／程序工具。不默认把正文压进等大浅色圆角框，图的形状由关系决定。

| Observable relationship | Use | Do not use |
| --- | --- | --- |
| Multiple steps, branches, loops, or failure recovery | Flowchart or sequence diagram | A paragraph that hides branches |
| Inputs, processing, modules, data, and outputs | Architecture diagram | An undirected concept cloud |
| Roles, departments, or upstream/downstream handoffs | Swimlane or collaboration map | A flat list of role names |
| Time stages, application rhythm, or growth path | Timeline or route map | Repeated month lists |
| Options, roles, evidence, gaps, or priorities | Matrix or compact comparison table | A full article inside table cells |
| Metric change, trend, distribution, or composition | Data chart | Any chart without trustworthy numbers |
| Facts, inference, and unresolved items | Evidence card or layered relationship | Color that makes uncertainty look confirmed |
| One conclusion or simple linear explanation | Short prose, quote, or information card | A diagram added only for decoration |

## Complexity test

A substantial document needs a visual plan. A visual is normally required when at least one condition is true:

- three or more dependent steps, components, actors, stages, or routes;
- a branch, loop, failure, fallback, handoff, or state change;
- the reader must compare multiple options or evidence paths together;
- verified quantitative data is central to the decision.

If none applies, record a specific `no_visual_reason`. “The document is short” is insufficient when it still contains a complex relationship.

## Evidence boundary

Every visual node or series must carry one of these meanings:

- `Confirmed`: supported student/client action, output, or result;
- `Externally verified`: supported public company, market, JD, or research fact;
- `Inferred`: a labelled interpretation or abstraction;
- `Knowledge supplement`: teaching or domain knowledge, not personal experience;
- `Open`: unresolved, planned, or awaiting evidence.

The formal categories belong in the internal evidence ledger. Student-facing nodes, captions and prose may use natural Chinese source and uncertainty cues; the meaning must remain clear without mechanically displaying internal English labels or generation steps.

Do not merge these categories through layout or color. A team result cannot become a personal result, a public business flow cannot become an internal product architecture, and a project plan cannot appear as completed work.

## Data-chart gate

Create a chart only when all four fields are available:

1. source or dataset identity;
2. metric definition;
3. time range;
4. unit or denominator.

If any field is missing, use a sourced statement, evidence matrix, or explicitly labelled conceptual diagram instead.
