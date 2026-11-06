# Visual Decision Matrix

## Decide from the relationship, not from a desired image count

先区分关系复杂度与目标格式。飞书讲解图默认使用正文原生画板；Word、PDF、Markdown、HTML 使用已验收画板导出或自身可稳定渲染的图表。保留已有有效媒体与原始来源。目标格式不改变事实边界，也不取消具体 `no_visual_reason` 的记录要求。

飞书阅读材料中的讲解图、流程图、关系图和方法总览默认使用飞书原生画板，嵌入对应正文并紧邻讲解；不再默认生成讲解图片。先锁定读者问题、准确文案、关系和阅读路径，再实际应用 `impeccable` 的 Read 模式处理信息层级、字体、对齐、间距、留白和配色。图只承担有助理解的关系，不把正文缩写塞进框，不做大字海报或装饰图凑数。逐字逐线检查，并核对原生节点、画板导出及正文实际阅读宽度；非空token、上传成功或导出成功均不替代视觉验收。非飞书文件使用已验收画板的清晰导出或适合该格式的图；真实统计图可用精确计算工具。用户明确要求图片或确需照片、插画时另选图像工具，并保留相同质量门。不默认把正文压进等大浅色圆角框，图的形状由关系决定。

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
