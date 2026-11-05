---
name: campus-recommend
description: Use when continuing a previous task that explicitly references the legacy campus-recommend entrypoint.
---

# 旧入口兼容

<!-- skill-workflow-link -->
[查看完整流程图与操作说明](references/workflow.md)
<!-- /skill-workflow-link -->

首次供团队成员使用时，先读 [团队配置与依赖](references/team-setup.md)，只配置当前任务所需能力。

本入口只是旧任务兼容别名，不是独立写回技能。安装时必须同时安装 `campus-job-matching` 完整目录，两者放在同一级 Skills 目录；插件整包安装会包含主技能。只复制本目录不能执行选岗。找不到主技能时说明缺少该依赖，先补齐，不发明旧规则或创建替代表。

本入口不再维护独立选岗、评分、公司上限或写回规则。读取并执行唯一主Skill：[当前安装的 campus-job-matching Skill 目录/SKILL.md](../campus-job-matching/SKILL.md)。

沿用已有学生、城市、方向、求职模式与对应条件、历史岗位键及原投递表／默认视图；新增岗位只在原表末尾去重追加，不另建页面、子表或批次视图。校招/实习/社招按主Skill分流，不重建档案、不重置公司数。飞书使用当前成员绑定的本人 `lark-cli --as user`；配置路径与共享池 owner 分离规则由主技能 [运行配置](../campus-job-matching/references/runtime-config.md) 定义。未核验线索不计作合格岗位。
