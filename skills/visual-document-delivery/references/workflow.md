# 图文文档交付：完整流程

输入：权威正文与来源；读者、决策和目标格式；流程关系或可信数据。

交付：图文一致的正式文档；对应章节的图表；visual_contract 与验收记录。

![完整流程图](../assets/workflow.svg)

[按原尺寸打开完整流程图](../assets/workflow.svg)

## 按什么顺序做

### 锁定阅读任务与目标格式

先确认读者、决策、权威来源、修改范围和受保护基线。

### 选择视觉或说明无图

按关系复杂度决策，数据图必须有来源、定义、时段和单位。

### 规划信息与成图方式

先锁文案关系与阅读顺序；按精度和成图质量选原生、程序或图像生成。

### 正文就近嵌图

保留事实边界，图紧邻解释；飞书正文图片不被链接或附件代替。

### 按范围渲染并回读

整篇实质修订逐页检查，局部修改检查受影响阅读路径和保护内容。

### 失败修复重渲并记录

修裁切、字小、媒体缺失等，再按目标面检查，填manifest并运行校验。

## 验收

- 视觉类型匹配关系与目标格式
- 数据图四要素齐全，事实状态不混
- 首屏导航、层级、图文位置可读
- AI图中文字数字箭头及分支逐项核
- 实际目标格式结构与媒体回读
- 整篇或局部按范围检查且问题已修复重渲
- manifest校验不替代实际页面验收

飞书、Word、PDF 和 HTML 按各自格式验收，不能相互替代。

## 对应规则

- [SKILL.md](../SKILL.md)
- [references/layout-and-information-design.md](layout-and-information-design.md)
- [references/render-and-acceptance.md](render-and-acceptance.md)
- [references/team-setup.md](team-setup.md)
- [references/visual-decision-matrix.md](visual-decision-matrix.md)

<details>
<summary>可编辑的流程源码</summary>

```mermaid
flowchart TB
  input(["权威正文、来源与读者<br/>决策、目标格式和修改范围"])
  read["读当前正文及保护内容<br/>规划首屏导航与阅读顺序"]
  complex{"复杂关系或比较需要图表？"}
  none["简单线性内容保留文字<br/>记录具体no_visual_reason"]
  plan["按关系选流程/架构/时间线<br/>或比较表，锁文案与关系"]
  data{"是否为真实数据图？"}
  dataready{"来源、定义、时段<br/>单位或分母齐全？"}
  alternative["改来源陈述、证据表<br/>或明确标注的概念图"]
  tool{"成图需要何种精度与能力？"}
  native["精确数据或需可编辑<br/>使用原生/程序工具"]
  teaching["总览与教学图先做准确结构<br/>视觉弱时改用可用图像生成"]
  figure["逐字核中文、数字和连线<br/>分支、回路与终态不漏"]
  figqa{"成图文字与逻辑正确可读？"}
  fixfigure["定向修图或改载体<br/>不为美观改变逻辑"]
  embed["图表紧邻对应讲解<br/>保留来源、图注与事实边界"]
  surface{"本轮验收范围？"}
  full["渲染实际目标格式<br/>逐页/全表面检查"]
  local["渲染改动与受影响阅读路径<br/>对比保护媒体与原内容"]
  capability{"能完成目标面结构和视觉检查？"}
  stop(["说明缺失能力或未验收范围<br/>不以CLI/语法成功代替显示"])
  qa{"结构媒体、全页阅读<br/>裁切、字小、表格均通过？"}
  repair["修授权范围内显示缺陷<br/>不支持格式改图片或原生表"]
  manifest[("记录真实视觉计划、媒体<br/>页数、检查页及问题清单")]
  validate{"运行manifest校验通过？"}
  done(["交付目标格式图文文档<br/>及可追溯验收记录"])
  input --> read
  read --> complex
  complex -->|"否：图不增加理解"| none
  complex -->|"是：关系需要可视化"| plan
  none --> embed
  plan --> data
  data -->|"是：数据图"| dataready
  data -->|"否：关系或教学图"| tool
  dataready -->|"四项齐全"| native
  dataready -->|"有缺失：不画数据图"| alternative
  alternative --> tool
  tool -->|"精确数据/坐标/可编辑"| native
  tool -->|"总览或教学信息图"| teaching
  native --> figure
  teaching --> figure
  figure --> figqa
  figqa -->|"不通过"| fixfigure
  fixfigure --> figure
  figqa -->|"通过"| embed
  embed --> surface
  surface -->|"新建或实质修订整篇"| full
  surface -->|"局部修改"| local
  full --> capability
  local --> capability
  capability -->|"缺能力：不能验目标面"| stop
  capability -->|"具备且完成实际检查"| qa
  qa -->|"不通过：有显示缺陷"| repair
  repair -->|"修后重渲"| surface
  qa -->|"通过：需审页面无遗漏"| manifest
  manifest --> validate
  validate -->|"通过且真实验收完整"| done
  validate -->|"字段或记录缺陷：补真实证据"| manifest
  validate -->|"真实验收仍有缺口"| stop
```

</details>
