# 通用模拟面试：完整流程

输入：学生身份与源简历；已有双端页面；岗位意向与训练范围。

交付：老师内部指导版；学生准备与训练版；问题目录、附件与图解。

![完整流程图](../assets/workflow.svg)

[按原尺寸打开完整流程图](../assets/workflow.svg)

## 按什么顺序做

### 先分流并锁定整册或局部

明确公司/JD和已发生面试转专用 Skill；局部请求只改目标块及必要双端关联。

### 定位唯一身份、页面及保护清单

复用双端原页与历史恢复点，完整读取源简历，保留附件、有效媒体和手工内容。

### 建立证据并选场次路线

先做事实、JD矩阵、个性化锚点；按口述等级选讲解、训练或模拟，按岗位选路线。

### 组织双端及前置图解

三档匹配JD、关键指标、S/K和问题目录一致；复杂图先成功预览再写，学生版不泄漏内部字段。

### 直写、读回与范围验收

整册执行远端全册和逐页验收；局部只验本次范围与保护清单，响应不明先读回。

## 验收

- 双端目录一致
- 学生版不含内部备注
- 手工内容与原图保留

未提供真实 JD 时只用明确标注的代表画像，不虚构邀约。

## 对应规则

- [SKILL.md](../SKILL.md)
- [references/feishu-delivery-contract.md](feishu-delivery-contract.md)
- [references/interview-content-contract.md](interview-content-contract.md)
- [references/interview-quality-contract.md](interview-quality-contract.md)
- [references/interview-session-contract.md](interview-session-contract.md)

<details>
<summary>可编辑的流程源码</summary>

```mermaid
flowchart TB
  in(["学生身份、原简历与本轮范围<br/>原双端页、岗位意向（如有）"])
  route{"本次属于哪类面试任务？"}
  companion(["转专岗／真实复盘 Skill<br/>分别确定独立交付对象"])
  scope{"整册还是局部？"}
  precheck["定位唯一主页与双端，读版本<br/>登记正文、附件、媒体和手工保留清单"]
  unique{"学生、源件与目标唯一？"}
  stop(["列冲突并暂停依赖写入<br/>不猜身份、不另建替代页"])
  facts["完整读简历；事实／JD证据映射<br/>无真实JD则明确代表画像"]
  level{"最弱关键经历口述等级？"}
  explain["0级：履历讲解<br/>先重建事实、术语与项目地图"]
  train["1级：结构化训练<br/>补输入、产出、Bad Case与边界"]
  simulate["2级以上：完整模拟<br/>有明确JD可定向；追问证据"]
  body["按业务／产品／技术／混合路线组织<br/>双端三档JD、指标、S/K及共用题序"]
  visual{"用户点图或存在复杂链路？"}
  preview["先生成、导出并逐图预览<br/>图解在问题前，紧邻解释"]
  imagegate{"本次必需图成功且可读？"}
  partial(["列具体未完成项<br/>不得插坏图或声称完整交付"])
  delivery{"已授权飞书且能力可用？"}
  limited(["交付明确要求的聊天／分析<br/>本地副本仅在明确要求时"])
  write["直写授权区块；正确附件保留<br/>分批后立即读回，响应不明先查"]
  qa["整册：远端全册＋逐页渲染<br/>局部：目标块、双端关联与保留核对"]
  gate{"本轮范围、图解与保护清单通过？"}
  repair["仅修本轮新增／授权缺陷<br/>未确认写入先读回，不盲目重试"]
  out(["交付主页与双端链接、修订<br/>报告Open、URL变化及图解验收"])
  in --> route
  route -->|"公司/JD定向／真实面后复盘"| companion
  route -->|"通用模拟"| scope
  scope -->|"整册：完整双端合同"| precheck
  scope -->|"局部：锁定块与关联题号"| precheck
  precheck --> unique
  unique -->|"不唯一／目标冲突"| stop
  unique -->|"唯一"| facts
  facts --> level
  level -->|"0级／关键事实大量缺失"| explain
  level -->|"1级；有JD也先训练"| train
  level -->|"2—3级；按JD决定是否定向"| simulate
  explain --> body
  train --> body
  simulate --> body
  body --> visual
  visual -->|"必需图"| preview
  visual -->|"简单线性：记录具体无图理由"| delivery
  preview --> imagegate
  imagegate -->|"失败／不可读"| partial
  imagegate -->|"成功"| delivery
  delivery -->|"明确只读／聊天／本地"| limited
  delivery -->|"缺必要写入／渲染能力"| partial
  delivery -->|"已授权且可用"| write
  write --> qa
  qa --> gate
  gate -->|"本次适用项全部通过"| out
  gate -->|"本轮／授权缺陷"| repair
  gate -->|"必要验收被阻塞"| partial
  repair --> write
```

</details>
