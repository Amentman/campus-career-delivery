# 简历修改与交付：完整流程

输入：权威简历版本；目标方向、JD 或批注；版式与文件保护要求。

交付：定向简历或修改说明；批注及干净 Word / PDF；版本与验收记录。

![完整流程图](../assets/workflow.svg)

[按原尺寸打开完整流程图](../assets/workflow.svg)

## 按什么顺序做

### 锁定三种模式与保护范围

诊断、文本修改、文件交付分别定完成门，不把小范围请求扩成整套产物。

### 按顺序取证并处理冲突

定向读取用户点名来源，建立事实、原文与版本记录；关键冲突先停止依赖改写。

### 共用事实、分方向改写

保留原文动作，记录原文—改文—理由—证据，方向变化只改变强调不改变事实。

### 文件模式派生同源 Word/PDF

每方向唯一母版生成批注 Word 与干净 PDF，只处理明确授权的旧文件。

### 按模式真实验收

诊断验判断，文本验改文；文件必须机器检查加目标查看器、字体分页和同源对照。

## 验收

- 事实与来源一致
- 受保护内容保留
- 目标应用与视觉检查

优化不等于重写；不编造经历和指标。

## 对应规则

- [SKILL.md](../SKILL.md)
- [references/evidence-and-content.md](evidence-and-content.md)
- [references/qa-contract.md](qa-contract.md)
- [references/source-intake-and-traceability.md](source-intake-and-traceability.md)
- [references/word-pdf-delivery.md](word-pdf-delivery.md)

<details>
<summary>可编辑的流程源码</summary>

```mermaid
flowchart TB
  in(["权威源简历、批注与目标<br/>修改范围、版式与文件要求"])
  scope["锁定诊断／文本／文件模式<br/>保护原稿、其他方向与版式"]
  sources["按点名顺序定向读真实来源<br/>登记来源、事实与冲突"]
  mode{"本轮执行模式？"}
  diagnosis(["只给有证据的问题和建议<br/>缺 JD 仅保留匹配待确认"])
  unique{"改写所需身份、版本与事实唯一？"}
  stop(["继续可做的只读核对<br/>列关键冲突，暂停依赖改写"])
  ledger["建立共享事实及原文处置记录<br/>各方向只改变重点与表达"]
  rewrite["按问题→本人动作→验证→结果改写<br/>逐条记原文、理由和证据"]
  filemode{"需要实际文件交付？"}
  textqa["回读本次改文与事实<br/>核对原文要点及保护内容"]
  textout(["交付改文与修改依据<br/>不声称 Word/PDF 文件已验收"])
  mother[("每方向建立唯一内容与布局母版<br/>记录版式指纹和文件血缘")]
  derive["派生真实批注＋改字红色 Word<br/>同正文干净母版导出 PDF"]
  qa["机器检查＋目标 WPS/Word 实看<br/>PDF 渲染与字体分页逐项对照"]
  pass{"同源、事实、版式与查看器通过？"}
  repair["回到方向母版修复<br/>重新派生同源 Word/PDF"]
  unverified(["报告已完成与原始异常<br/>查看器不可用则对应项未验收"])
  clean{"要求清理且旧文件归属明确？"}
  backup["新版通过后可恢复移动旧稿<br/>读回文件名、大小与去向"]
  out(["交付本轮官方文件与方向用途<br/>报告真实验收、Open 与旧版去向"])
  textgate{"本次改文与原文保护通过？"}
  in --> scope
  scope --> sources
  sources --> mode
  mode -->|"诊断：只读"| diagnosis
  mode -->|"文本修改"| unique
  mode -->|"文件交付"| unique
  unique -->|"身份／基线／关键事实冲突"| stop
  unique -->|"已唯一；非关键缺项保守处理"| ledger
  ledger --> rewrite
  rewrite --> filemode
  filemode -->|"只改文本"| textqa
  filemode -->|"交付 Word／PDF"| mother
  mother --> derive
  derive --> qa
  qa --> pass
  pass -->|"已证实可修缺陷"| repair
  repair --> derive
  pass -->|"能力缺失／冲突无法解决"| unverified
  pass -->|"所有适用项通过"| clean
  clean -->|"明确授权且归属已确认"| backup
  clean -->|"未要求／来源不明：不处理"| out
  backup --> out
  textqa --> textgate
  textgate -->|"事实与授权范围通过"| textout
  textgate -->|"本次改文／要点保留未通过"| rewrite
```

</details>
