# 朋友圈内容写作：完整流程

输入：话题、想法或具体事件；业务知识库与客户原话；风格或已选框架。

交付：朋友圈正文或框架；可选口播逐字稿；可选小红书标题。

![完整流程图](../assets/workflow.svg)

[按原尺寸打开完整流程图](../assets/workflow.svg)

## 按什么顺序做

### 读取本人业务底座

复用成员身份、风格和产品资料，按需要补客户原话、故事或方法。

### 按五类输入与延伸路由

话题、知识库、粗想法、事件、转写分流；口播与标题独立延伸。

### 区分讨论与直接成稿

只在用户要求选框架或勾选时等选择；已授权代选或成稿直接继续。

### 选择并读取对应风格

一种主风格；转写按长度萃取，写前安排情绪路径。

### 写正文并逐项检查

三道关口、因果与行动、语气、合规及标点不通过则重写。

### 聊天交稿或授权保存

默认正文；保存才写既定位置并回读，不覆盖旧稿或自动发布。

## 验收

- 本人成员资料与风格文件实际读取
- 5类输入及2项延伸不混路由
- 只有用户要求讨论或筛选才停等选择
- 三道关口、情绪路径与事实合规通过
- 客户脱敏，不承诺效果或写具体收入金额
- 保存后读回，不覆盖或自动发布

成稿只交付内容，不自动发朋友圈。

## 对应规则

- [SKILL.md](../SKILL.md)
- [references/README.md](README.md)
- [references/team-setup.md](team-setup.md)

<details>
<summary>可编辑的流程源码</summary>

```mermaid
flowchart TB
  input(["话题、观点、事件或转写<br/>已有文案与输出要求"])
  base["读本人身份风格与产品<br/>无库时用本轮真实材料"]
  route{"输入属于哪条路线？"}
  topic["A话题：形成具体角度<br/>备选框架含风格与示例开头"]
  knowledge["B调库：整合真实观点<br/>按案例、方法、原话取材"]
  idea["C想法：选专家逻辑补全<br/>观点逻辑与本人语言分开"]
  event["D事件：提炼一条观点<br/>事件与观点因果自然"]
  length{"E转写稿长度？"}
  short["不足3000字<br/>完整读后选一条主线"]
  medium["3000–10000字<br/>先萃取10–15条信息点"]
  long["超过10000字<br/>分类观点、原话、案例数据"]
  choose{"用户明确要框架或素材筛选？"}
  options(["先交框架或可勾选素材<br/>等待用户选择再续写"])
  style["沿用已选角度和主风格<br/>必须读对应风格文件"]
  emotion["定开头、论证与结尾情绪<br/>一条只讲一件事"]
  draft["用真实案例与本人语气写<br/>短段落、因果、方向或行动"]
  spoken["延伸1：改口播逐字稿<br/>短句、一口气，估时60–80秒"]
  titles["延伸2：生成小红书标题<br/>按真实内容选择标题技巧"]
  qa{"事实、语气、逻辑与合规<br/>正文三道关口通过？"}
  rewrite["补真实依据或重写<br/>不造收入、案例和类比"]
  save{"已有明确保存授权？"}
  chat(["交付可直接使用正文<br/>保存与发布分别授权"])
  file[("新建版本稿并保留素材标注<br/>写后读回全文，不覆盖历史")]
  readback{"正文与素材来源读回一致？"}
  done(["交稿与实际文件<br/>不自动发朋友圈或小红书"])
  stop(["报告保存失败或事实缺口<br/>不称已保存或编内容"])
  enough{"现有材料足以真实写作？"}
  input --> base
  base --> enough
  route -->|"给话题"| topic
  route -->|"调知识库"| knowledge
  route -->|"粗糙想法"| idea
  route -->|"具体事件"| event
  route -->|"录音转写或已有整理稿"| length
  route -->|"已给文案要口播"| spoken
  route -->|"已有内容要标题"| titles
  topic --> choose
  knowledge --> choose
  idea --> choose
  event --> choose
  length -->|"少于3000字"| short
  length -->|"3000–10000字"| medium
  length -->|"超过10000字"| long
  short --> choose
  medium --> choose
  long --> choose
  choose -->|"是：只到讨论/勾选"| options
  choose -->|"否：直接成稿或已授权代选"| style
  style --> emotion
  emotion --> draft
  draft --> qa
  spoken --> qa
  titles --> qa
  qa -->|"不通过：改对应内容"| rewrite
  rewrite --> route
  qa -->|"通过"| save
  save -->|"无：默认聊天交付"| chat
  save -->|"有：沿用既定保存位置"| file
  file --> readback
  readback -->|"一致"| done
  readback -->|"不一致或未读回"| stop
  enough -->|"足够：无库亦可用当前材料"| route
  enough -->|"关键事实缺失：只核对该缺口"| stop
```

</details>
