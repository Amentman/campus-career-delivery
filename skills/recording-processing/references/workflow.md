# 录音与逐字稿整理：完整流程

输入：可信转写稿或录音；场景与发言人信息；整理或入库范围。

交付：整理稿与核心结论；决策、原话及后续行动；已授权知识库条目。

![完整流程图](../assets/workflow.svg)

[按原尺寸打开完整流程图](../assets/workflow.svg)

## 按什么顺序做

### 区分真实复盘与普通整理

真实正式面试转专用Skill；普通录音先确认可读转写。

### 选深度并完整读取

A重度区分自己主讲与别人分享；B轻量，全文读完再提取。

### 提取并组织整理稿

保留观点、方法、故事数字、原话、选题和待办，复杂关系按证据图解。

### 按范围选择交付面

默认对话整理；已授权保存沿用目标，学生正式归档定位唯一飞书。

### 仅有价值且授权时入库

按真实目录分流，近主题追加、无主题新建，待办不入库。

### 回读并报告实际结果

核保存内容、追加段落和来源；缺转写、目标或图解能力据实保留。

## 验收

- 完整读完后提取，逐份不混淆
- 真实面试转专用入口
- 未授权不落盘或入库
- 仅新建和追加，不改移删历史
- 写后回读来源、内容及真实显示

只有可信转写能力时才处理音频，不能猜内容。

## 对应规则

- [SKILL.md](../SKILL.md)
- [references/team-setup.md](team-setup.md)

<details>
<summary>可编辑的流程源码</summary>

```mermaid
flowchart TB
  input(["录音或完整转写稿<br/>场景、发言人与输出范围"])
  interview{"要求真实公司面试逐题复盘？"}
  handoff(["转实际面试复盘Skill<br/>不自动沉淀六大库"])
  transcript{"已有可读转写或识别能力？"}
  missing(["说明需可读转写<br/>不猜音频内容"])
  read["多份逐份完整读完<br/>保留发言人与来源边界"]
  mode{"长交流还是短备忘？"}
  heavy["A重度：完整提取<br/>本人判断或他人方法迁移"]
  light["B轻量：摘要与待办<br/>无内容栏目不写"]
  extract["提取六类要素<br/>原话、数字、时间线不漏"]
  complex{"重度且有可证复杂关系？"}
  visual["按证据画交接或决策图<br/>不支持渲染改关系表"]
  novisual["轻量或关系简单<br/>记录具体无图原因"]
  draft["完成可追溯整理稿<br/>区分原话、推断与行动"]
  destination{"本轮授权何种输出？"}
  chat(["对话交整理稿、待办<br/>及未确认项"])
  target{"目标唯一、权限<br/>及所需本人身份可用？"}
  blocked(["交可用稿并说明未归档<br/>不建替代页或冒称已入库"])
  valuable{"已授权入库且有可复用素材？"}
  archive[("按授权保存完整整理稿<br/>学生正式归档到对应唯一飞书页")]
  similar{"目标库已有近主题文件？"}
  append[("按实际目录追加或新建<br/>逐条来源/应用标签，待办不入库")]
  qa{"独立读回正文、来源<br/>图解及追加位置通过？"}
  done(["报告实际文件与素材条数<br/>列待办和未确认项"])
  input --> interview
  interview -->|"是：真实面试复盘"| handoff
  interview -->|"否：普通整理"| transcript
  transcript -->|"否：本技能不自带识别"| missing
  transcript -->|"是：取得可读文本"| read
  read --> mode
  mode -->|"A：长会谈/课程"| heavy
  mode -->|"B：短备忘"| light
  heavy --> extract
  light --> extract
  extract --> complex
  complex -->|"是：三项以上关系"| visual
  complex -->|"否：轻量或简单"| novisual
  visual --> draft
  novisual --> draft
  draft --> destination
  destination -->|"仅整理：不写库"| chat
  destination -->|"保存、入库或学生正式归档"| target
  target -->|"否：目标/能力有缺口"| blocked
  target -->|"是：沿用授权"| archive
  valuable -->|"否：仅存稿或流水账"| qa
  valuable -->|"是：分流到真实结构"| similar
  similar -->|"有：只追加"| append
  similar -->|"无：才新建"| append
  append --> qa
  qa -->|"通过"| done
  qa -->|"不通过：不称已保存"| blocked
  archive --> valuable
```

</details>
