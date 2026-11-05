# 简历与面试故事：完整流程

输入：简历与项目证据；目标岗位或 JD；指定交付范围。

交付：证据与 JD 映射；简历要点或项目故事；面试问答与事实缺口。

![完整流程图](../assets/workflow.svg)

[按原尺寸打开完整流程图](../assets/workflow.svg)

## 按什么顺序做

### 按交付范围分流

完整模拟、专岗和真实复盘由专用 Skill 主导，本入口处理有边界的故事与表达。

### 先证据与业务，再锁故事

建立事实账本与 JD 映射，关键缺项先追问；项目讲不清时先教学。

### 按请求生成表达

简历要点、项目解释、技术模型及面试问答只生成本次所需部分。

### 按复杂度及交付面验收

复杂持久材料就地配图；简短要点不强配图，正式材料按已授权目标写入并回读。

## 验收

- 不编造个人贡献
- 业务解释可口述
- 交付只覆盖本次范围

公开公司知识只能补背景，不能改写成本人经历。

## 对应规则

- [SKILL.md](../SKILL.md)
- [references/intake-and-evidence.md](intake-and-evidence.md)
- [references/interview-framework.md](interview-framework.md)
- [references/resume-framework.md](resume-framework.md)
- [references/visual-story-contract.md](visual-story-contract.md)

<details>
<summary>可编辑的流程源码</summary>

```mermaid
flowchart TB
  in(["简历、项目证据、JD<br/>本次产物与交付范围"])
  route{"完整学生面试交付？"}
  companion(["转通用模拟／专岗／真实复盘<br/>本 Skill 提供证据表达方法"])
  ledger["完整读取选定资料<br/>分类事实、责任与结果"]
  critical{"缺项会改变核心故事？"}
  ask(["只问一个关键问题<br/>暂停依赖该事实的声称"])
  mapping["做 JD 证据映射<br/>按需查公司外部事实"]
  business["用白话讲问题、输入、本人动作<br/>产物、验证与结果边界"]
  understand{"本人能解释关键经历？"}
  teach["先重建业务理解<br/>不提前编面试脚本"]
  product{"本次需要哪类产物？"}
  bullets["写证据支持的简历要点<br/>做十秒筛选与版式检查"]
  qa["建立 S 故事／K 知识锚点<br/>按职责生成问答；技术按需"]
  explain["形成项目解释<br/>完整包只纳入所需部分"]
  visual{"持久材料有复杂关系？"}
  draw["业务图与 JD 矩阵就地放置<br/>区分个人动作与背景知识"]
  gate{"事实、范围与呈现通过？"}
  repair["回到事实或表达修正<br/>不补造数字／责任"]
  delivery{"正式飞书授权与目标齐备？"}
  write["写入对应唯一页面<br/>读回媒体、顺序与实际显示"]
  draft(["交付本次要点／聊天／导出稿<br/>目标缺失时注明未正式交付"])
  out(["交付正式材料与待确认项<br/>答案不超出履历事实"])
  in --> route
  route -->|"完整模拟／专岗／复盘"| companion
  route -->|"有边界的故事／要点任务"| ledger
  ledger --> critical
  critical -->|"核心职责／结果仍不明"| ask
  critical -->|"已确认／仅精度缺项"| mapping
  mapping --> business
  business --> understand
  understand -->|"讲不清"| teach
  teach --> business
  understand -->|"能解释"| product
  product -->|"简历要点／优化"| bullets
  product -->|"问答／完整包"| qa
  product -->|"项目解释"| explain
  bullets --> visual
  qa --> visual
  explain --> visual
  visual -->|"多步骤／角色／分支"| draw
  visual -->|"短答／单要点：记录无图理由"| gate
  draw --> gate
  gate -->|"未通过"| repair
  repair --> ledger
  gate -->|"通过适用项"| delivery
  delivery -->|"是：对应唯一页"| write
  delivery -->|"明确聊天／本地，或暂缺写入条件"| draft
  write --> out
```

</details>
