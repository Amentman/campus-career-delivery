# 学生职业规划：完整流程

输入：学生简历与背景；目标城市与方向；问卷与已有规划（如有）。

交付：学生职业规划；方向与分层公司池；差距补强与行动时间线。

![完整流程图](../assets/workflow.svg)

[按原尺寸打开完整流程图](../assets/workflow.svg)

## 按什么顺序做

### 先判断阶段与受保护母版

架构对焦只给结构；标准版完整展开；扩展研究和白皮书只按明确要求增加。

### 建立证据并排序方向

从学生经历、偏好和门槛收敛 1—3 个可投方向，说明取舍与切换条件。

### 研究具体岗位、公司与待遇

每路线关联真实岗位、城市阶段、薪酬待遇与分层公司池，缺薪酬继续查可比样本。

### 按证据准备度安排补强与投递

已有证据支持的岗位可先准备简历投递；依赖新项目的能力写明达标后进入条件。

### 完成正文与交付验收

先审内容，再写授权唯一页面；保护母版等价性，回读全文、附件、媒体并渲染。

## 验收

- 方向有履历依据
- 岗位差距对应行动
- 交付正文与图表可读

白皮书不是默认前置；未完成项目不写成履历成果。

## 对应规则

- [SKILL.md](../SKILL.md)
- [references/evidence-and-input-contract.md](evidence-and-input-contract.md)
- [references/external-career-plan-standard.md](external-career-plan-standard.md)
- [references/feishu-delivery.md](feishu-delivery.md)
- [references/industry-research-contract.md](industry-research-contract.md)
- [references/planning-and-project-contract.md](planning-and-project-contract.md)

<details>
<summary>可编辑的流程源码</summary>

```mermaid
flowchart TB
  in(["学生简历、偏好与约束<br/>参考规划／原页／当前请求"])
  mode{"本轮规划阶段？"}
  outline(["只交目录、核心表字段与顺序<br/>不提前写正文或飞书"])
  research["按明确范围扩展 JD／赛道<br/>白皮书单独复用或研究"]
  evidence["完整读材料、隔离他人事实<br/>登记原简历与受保护版本"]
  roles["比较日常、门槛、偏好与证据<br/>收敛 1—3 条可投路线"]
  market["每路线查岗位—公司—城市／阶段<br/>薪酬待遇、来源与分层公司池"]
  salary{"每路线有同口径薪酬依据？"}
  salarygap["继续找同职业可比样本<br/>仍缺则标薪资研究未完成"]
  projects["按岗位缺口选补强产物<br/>社招优先深挖已有经历"]
  ready{"核心申请证据准备度？"}
  now["现有证据足够：规划可投版本<br/>申请准备与补强并行"]
  later["依赖新项目：列任务与进入条件<br/>达标后再写成果、投对应岗"]
  body["按八章写完整规划与时间线<br/>图解紧邻对应解释"]
  content{"方向、市场与行动链讲清？"}
  repair["只修本轮缺口<br/>保留已确认结构与有效内容"]
  deliver{"飞书授权且唯一落点？"}
  draft(["交付可审阅正文／指定本地形式<br/>保留薪资及事实未完成项"])
  write["核对本人、父级与版本后局部写<br/>保留母版等价、首屏原简历"]
  readback["回读全文、公司薪资、媒体与附件<br/>对照母版，逐页检查最终渲染"]
  gate{"本轮适用验收全部通过？"}
  out(["交付规划页与行动顺序<br/>列明未确认及未验证项"])
  in --> mode
  mode -->|"先讨论架构"| outline
  mode -->|"明确扩展研究／白皮书"| research
  mode -->|"标准学生版／局部完善"| evidence
  research --> evidence
  evidence --> roles
  roles --> market
  market --> salary
  salary -->|"有同口径依据"| projects
  salary -->|"未披露／证据不足"| salarygap
  salarygap --> projects
  projects --> ready
  ready -->|"现有经历已支持"| now
  ready -->|"需新增项目证据"| later
  now --> body
  later --> body
  body --> content
  content -->|"未讲清／链条不对应"| repair
  repair --> roles
  content -->|"内容可用"| deliver
  deliver -->|"未授权／限定本地／目标待确认"| draft
  deliver -->|"已授权且唯一"| write
  write --> readback
  readback --> gate
  gate -->|"适用项均通过"| out
  gate -->|"缺项／不等价／显示失败"| repair
  gate -->|"研究／显示仍受阻：仅交付已完成部分"| draft
```

</details>
