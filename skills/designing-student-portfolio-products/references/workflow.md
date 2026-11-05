# AI 作品集规划：完整流程

输入：学生履历与能力缺口；目标岗位或业务问题；时间与数据限制。

交付：前置学习材料；完整 PRD 与可操作 Demo；后续实践验收标准。

![完整流程图](../assets/workflow.svg)

[按原尺寸打开完整流程图](../assets/workflow.svg)

## 按什么顺序做

### 锁定业务与事实边界

读取学生经历、目标岗位、现有作品和素材，区分既有实践、演示和待开发。

### 设计资料、PRD 与责任

固定三份必看和一次工具小任务；PRD 十二槽位完整，规则、AI 与人工职责明确。

### 制作首图与可操作 Demo

首图讲清产品用户问题功能；Demo 真实可点并覆盖正常、空错、加载、复核和失败。

### 交付学生后续验收标准

规定真实调用、Prompt 迭代、Bad Case、复测和现场修改证据，不预填学生已完成。

### 按授权独立落位并回读

独立作品集页按首图—Demo—阶段—四件套排列，验证正文图片和实际使用效果。

## 验收

- 业务承接与 AI 实践兼具
- Demo 与 PRD 一致
- 演示与真实能力分开
- 首屏产品总览图实际可见且可读
- 三份固定必看材料保留

这里交付规划四件套；学生后续开发与实践另行完成。

## 对应规则

- [SKILL.md](../SKILL.md)
- [references/product-plan-contract.md](product-plan-contract.md)

<details>
<summary>可编辑的流程源码</summary>

```mermaid
flowchart TB
  in(["学生履历、岗位／业务问题<br/>时间、数据和当前交付阶段"])
  unique{"身份、业务方向与边界明确？"}
  stop(["先消除关键歧义<br/>暂停依赖该信息的交付"])
  ledger["建立事实与岗位映射<br/>锁定一个用户、一条流程、一个结果"]
  data{"真实业务素材足够？"}
  sample["缩小结论与范围<br/>用有来源的公开／模拟小样本"]
  ai{"核心结果需要 AI？"}
  aiplan["规划真实调用、解析与失败复现<br/>规则及人工负责确定性与最终判断"]
  rules["使用规则／人工完成<br/>不为展示强行接模型"]
  learn["三份固定必看＋工具小任务<br/>其他资料按需查阅"]
  prd["完成 PRD 十二槽位<br/>闭合来源、处理、复核、产物与反馈"]
  demo["制作产品首图与可操作 Demo<br/>标明演示数据、未接接口和状态"]
  standards["列学生后续提交与验收标准<br/>代码、真实调用、复测与现场讲解"]
  capability{"首图清晰、Demo 真能操作？"}
  partial(["交付已完成规划部分<br/>图片／交互缺项保持未完成"])
  delivery{"飞书授权、本人及目标唯一？"}
  local(["交付指定本地／对话规划包<br/>无托管可用离线 HTML Demo"])
  write["复用独立作品集页或按目标创建<br/>首图→Demo→阶段→四件套"]
  gate{"正文、首图、Demo 与原页保护通过？"}
  fix["修正已证实缺项<br/>重新读回并检查显示"]
  out(["交付可执行规划包<br/>学生开发、真实调用与效果仍待实践"])
  in --> unique
  unique -->|"关键歧义未消除"| stop
  unique -->|"明确"| ledger
  ledger --> data
  data -->|"不足"| sample
  data -->|"足够"| ai
  sample --> ai
  ai -->|"需要 AI"| aiplan
  ai -->|"规则／人工足够"| rules
  aiplan --> learn
  rules --> learn
  learn --> prd
  prd --> demo
  demo --> standards
  standards --> capability
  capability -->|"缺图片或实际交互验证"| partial
  capability -->|"适用项已检查"| delivery
  delivery -->|"限定本地／无写入条件"| local
  delivery -->|"已授权且唯一"| write
  write --> gate
  gate -->|"全部适用项通过"| out
  gate -->|"缺图／阶段错／不可读"| fix
  fix --> write
```

</details>
