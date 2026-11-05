# 求职内容创作：完整流程

输入：主题、问题或素材；目标读者与岗位；知识库和真实案例。

交付：求职内容母稿；岗位解释与案例表达；图文排版提示。

![完整流程图](../assets/workflow.svg)

[按原尺寸打开完整流程图](../assets/workflow.svg)

## 按什么顺序做

### 读取成员素材与索引

先读身份风格与产品；按主题从真实索引完整读取相关知识单元。

### 建立证据底盘

区分真实案例、个人观察、外部观点与待审线索，不冒用经历。

### 选证据充分的核心问题

从材料聚类并选1–3个支撑点；无支撑换角度，时效事实另行核验。

### 按请求交付选题或成稿

正文围绕一个核心判断，解释岗位具体工作、追问和证明产出。

### 设置图文排版重点

长图母稿保留准确标题、重点句与合格表格，不新增事实。

### 逐项审稿后交付

核标题力度、两个岗位特有判断与行动价值；不通过重写。

## 验收

- 素材按真实索引完整读取
- 待审结论不直接进入正文
- 标题与数字频率强度有证据
- 至少两个岗位特有判断、追问或场景
- 去掉CTA及排版标记仍独立有用

内容生产不等于图片已生成或平台已发布。

## 对应规则

- [SKILL.md](../SKILL.md)
- [references/team-setup.md](team-setup.md)

<details>
<summary>可编辑的流程源码</summary>

```mermaid
flowchart TB
  input(["主题、读者、岗位<br/>参考内容或真实素材"])
  persona["复用成员身份风格与产品<br/>无个人资料仅用当前材料"]
  materials["按真实索引完整读知识单元<br/>有管线时只取索引与提炼层"]
  status{"素材属于何种证据？"}
  trusted["真实案例脱敏<br/>观察与公开观点保留边界"]
  review["待审单元只作核验线索<br/>不直接写其结论"]
  angle["聚类选择一个核心判断<br/>挑1–3条最强材料"]
  support{"角度与标题有材料支撑？"}
  reselect["换成证据更扎实的角度<br/>不造学生、频率或结果"]
  fresh{"涉及最新公司、岗位<br/>薪资、政策或招聘？"}
  verify["另行核验时效事实<br/>保留来源与适用范围"]
  type{"本轮要选题还是正文？"}
  topics(["交可继续创作的选题策划<br/>问题、判断与证据具体"])
  draft["写一个判断与岗位场景<br/>给出可执行检查或下一步"]
  format["长图稿标小标题与关键句<br/>比较才用标准表格"]
  qa{"证据力度、岗位细节<br/>语言与行动价值通过？"}
  fix["按问题重写对应段落<br/>承接不自然则去掉"]
  done(["交付可用母稿<br/>不等于已出图或发布"])
  input --> persona
  persona --> materials
  materials --> status
  status -->|"可核验事实、观察或方法"| trusted
  status -->|"needs_review或仅线索"| review
  trusted --> angle
  review --> angle
  angle --> support
  support -->|"否：降低判断或换题"| reselect
  reselect --> angle
  support -->|"是：力度受证据约束"| fresh
  fresh -->|"是：核当前信息"| verify
  fresh -->|"否：沿用可靠材料"| type
  verify --> type
  type -->|"选题或策划"| topics
  type -->|"正文或参考改写"| draft
  draft --> format
  format --> qa
  qa -->|"不通过"| fix
  fix --> draft
  qa -->|"通过"| done
```

</details>
