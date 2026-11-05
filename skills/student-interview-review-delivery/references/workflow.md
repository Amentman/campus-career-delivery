# 真实面试复盘：完整流程

输入：已发生面试的完整逐字稿；学生简历与场次信息；明确复盘对象。

交付：逐题面试复盘；跨题结论与训练任务；唯一复盘页及来源附件。

![完整流程图](../assets/workflow.svg)

[按原尺寸打开完整流程图](../assets/workflow.svg)

## 按什么顺序做

### 核对真实面试及场次

已有面试证据才复盘；邀约/JD转专岗，学生、场次和唯一页不明时暂停依赖写入。

### 完整读取并分清说话人

通读逐字稿，保留时间戳或行号；发言人不明停止人物归因，不猜音频内容。

### 逐题纠正并提供完整练答

原答、反馈、诊断和知识分开，每题给答题逻辑、完整答案、追问应对与训练，相关题按英语要求补版本。

### 形成结论与简历建议

稳定能力至少两处独立证据，只提简历建议，保留具体事实冲突和下一轮风险。

### 独立交付与范围验收

复用同场页并保留原简历和全文附件；本地字段门加逐题人工门、远端读回和显示检查。

## 验收

- 真实与模拟分开
- 无反馈不冒充导师
- 原页和附件保留

只改目标复盘页；简历建议不等于授权改简历。

## 对应规则

- [SKILL.md](../SKILL.md)
- [references/feishu-boundary-and-acceptance.md](feishu-boundary-and-acceptance.md)
- [references/review-content-contract.md](review-content-contract.md)

<details>
<summary>可编辑的流程源码</summary>

```mermaid
flowchart TB
  in(["面试录音／完整转写／问答<br/>学生简历、公司岗位与场次"])
  route{"有已发生的真实面试证据？"}
  prepare(["只有邀约/JD转专岗准备<br/>通用模拟转独立训练 Skill"])
  unique{"学生、源件、场次与目标唯一？"}
  stop(["列身份／场次冲突<br/>停止依赖该信息的写入"])
  read["完整通读可读面试材料<br/>音频仅在可信转写能力下处理"]
  speaker{"说话人能可靠区分？"}
  open["停止不可靠的人物归因<br/>标Open，不把示范当学生原答"]
  ledger["按时间戳／行号建立事实账本<br/>原答、反馈、纠正和AI建议分开"]
  cards["按本次题组逐题复盘<br/>原答→纠正→逻辑→完整练答→追问→任务"]
  english{"岗位明确要求相关题英语？"}
  enanswers["为相关核心题补英文可练答案<br/>个人事实与中文证据一致"]
  cross["两处独立证据才称稳定能力<br/>列事实冲突、简历建议与训练任务"]
  contentgate{"范围内答案可口述且事实正确？"}
  repair["保持原题号、原答和证据<br/>只补本轮答案、逻辑与追问"]
  delivery{"已授权飞书且唯一挂载点？"}
  draft(["交付限定题组／聊天／本地复盘<br/>注明证据覆盖与未验证部分"])
  write["只写同场唯一复盘页<br/>默认学生版下，保留原简历和全文附件"]
  qa["回读父级、修订、完整正文及附件<br/>检查实际显示与受保护原页"]
  gate{"本轮内容、附件、显示与保护通过？"}
  fix["修正本次授权缺项后重新读回<br/>响应不明先核实，不重复新建"]
  partial(["列具体缺项与最小所需信息<br/>不以字段脚本／修订增加称完成"])
  out(["交付独立复盘页、训练任务与Open<br/>原简历及通用、专岗页保持保护"])
  in --> route
  route -->|"尚未面试／通用训练"| prepare
  route -->|"真实已发生"| unique
  unique -->|"不唯一"| stop
  unique -->|"唯一"| read
  read --> speaker
  read -->|"音频无法可信转写且无足够文本"| partial
  speaker -->|"无法可靠归属"| open
  speaker -->|"可区分"| ledger
  open --> ledger
  ledger --> cards
  cards --> english
  english -->|"相关题明确要求英语"| enanswers
  english -->|"无该语言要求"| cross
  enanswers --> cross
  cross --> contentgate
  contentgate -->|"缺答案／不自然／超出事实"| repair
  repair --> cards
  contentgate -->|"本轮人工门与适用字段门通过"| delivery
  delivery -->|"限定只读／本地／缺挂载条件"| draft
  delivery -->|"授权且目标唯一"| write
  write --> qa
  qa --> gate
  gate -->|"适用项全部通过"| out
  gate -->|"本轮可修缺项"| fix
  gate -->|"必需能力／证据受阻"| partial
  fix --> qa
```

</details>
