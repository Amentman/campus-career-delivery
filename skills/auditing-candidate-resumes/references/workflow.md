# 候选人简历评估：完整流程

输入：简历与版本；岗位 JD 或筛选标准；资料截止时间。

交付：决策与证据摘要；时间线与岗位匹配；面试核验问题。

![完整流程图](../assets/workflow.svg)

[按原尺寸打开完整流程图](../assets/workflow.svg)

## 按什么顺序做

### 先分流并锁定口径

招聘方审查与候选人改写分流；无 JD 不猜岗位标准，多人保持同一标准。

### 完整读取并重建证据

记录缺页、日期精度、学历与经历，区分硬门槛未提及和明确不满足。

### 核对贡献、风险与建议

检查个人动作、指标、归因和矛盾，保留替代解释、核验问题与改变结论的新证据。

### 按格式验收后交付

先给招聘动作和最多三个决定性问题；正式报告逐页渲染，不可用格式如实保留未验收。

## 验收

- 判断连回简历原文
- 未提及不等于不具备
- 正式报告逐页渲染

只给基于当前证据的建议，招聘决定由人作出。

## 对应规则

- [SKILL.md](../SKILL.md)
- [references/audit-framework.md](audit-framework.md)
- [references/decision-first-report-design.md](decision-first-report-design.md)
- [references/output-contract.md](output-contract.md)

<details>
<summary>可编辑的流程源码</summary>

```mermaid
flowchart TB
  in(["简历、截止时间<br/>JD／用人标准（如有）"])
  route{"招聘方审查？"}
  rewrite(["转简历／故事修改 Skill"])
  scope["锁定资料与外核授权<br/>完整提取；缺页列待补"]
  jd{"有明确 JD／标准？"}
  rubric["统一硬门槛与核心能力<br/>多人共用同一标准"]
  nojd["只审时间线与证据质量<br/>具体岗位匹配待确认"]
  timeline["重建月级时间线<br/>核对动作、归因与指标"]
  external{"本轮获准外部核验？"}
  verify["读取可靠外部证据<br/>记录能证明的边界"]
  risk["分清材料缺失／岗位缺口／矛盾<br/>附替代解释与核验问题"]
  multi{"多候选人？"}
  compare["先逐人结论，再同标准比较<br/>按岗位证据强度排序"]
  report["给推进／初筛／补证／不推进建议<br/>首页最多三个决定性问题"]
  format{"能交付正式格式？"}
  render["制作决策备忘录<br/>逐页渲染与十秒首屏检查"]
  gate{"证据边界与适用格式通过？"}
  revise["修正原文与版式<br/>重新检查受影响报告"]
  out(["交付建议、证据与核验清单<br/>保留缺失及格式未验收项"])
  in --> route
  route -->|"是：审查"| scope
  route -->|"否：候选人改写"| rewrite
  scope --> jd
  jd -->|"有标准"| rubric
  jd -->|"无标准"| nojd
  rubric --> timeline
  nojd --> timeline
  timeline --> external
  external -->|"已授权且执行"| verify
  external -->|"未授权／仅审材料"| risk
  verify --> risk
  risk --> multi
  multi -->|"多人"| compare
  multi -->|"单人"| report
  compare --> report
  report --> format
  format -->|"正式且工具可用"| render
  format -->|"聊天／工具未接通：注明范围"| gate
  render --> gate
  gate -->|"通过适用项"| out
  gate -->|"证据／呈现有缺陷"| revise
  revise --> report
```

</details>
