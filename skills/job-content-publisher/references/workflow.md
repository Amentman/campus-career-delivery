# 求职内容交付：完整流程

输入：已确认唯一母稿；目标图片包或飞书记录；本轮生产模式。

交付：已验证图片包；逐页完整文案；授权后的飞书写回回执。

![完整流程图](../assets/workflow.svg)

[按原尺寸打开完整流程图](../assets/workflow.svg)

## 按什么顺序做

### 确认母稿与执行模式

未确认只交母稿；已确认按本地图片、纯上传、完整飞书范围执行。

### 核对飞书与唯一记录

仅飞书分支检查本人、真实字段与关联；零匹配按已给授权创建，多匹配停止。

### 锁定源稿并交由图片技能

保留完整标题正文和身份字段，按合同计算哈希；依赖缺失不替换渲染器。

### 验包与附件幂等

两份校验通过、全文一致、零溢出、哈希与顺序一致才继续；冲突停止。

### 按顺序写回并读回

逐页全文与附件串行写入；校验后更新真实已定稿状态，不改发布值。

### 按实际模式交付

本地仅交包；飞书交链接与身份字段、附件读回和状态。

## 验收

- 唯一母稿和包哈希一致
- validation与final-verification均通过
- exactText=true且零溢出、页序一致
- 逐页全文含末句且每附件字段一张
- 身份关联及原权限回读，是否发布不误改

母稿未确认时先停在母稿；上传飞书不等于公开发布。

## 对应规则

- [SKILL.md](../SKILL.md)
- [references/content-generation-rules.md](content-generation-rules.md)
- [references/feishu-writeback-rules.md](feishu-writeback-rules.md)
- [references/team-setup.md](team-setup.md)

<details>
<summary>可编辑的流程源码</summary>

```mermaid
flowchart TB
  request(["已确认稿、待确认稿<br/>或已确认图片包"])
  approved{"母稿已确认？"}
  draft["按内容类型完成母稿<br/>定稿全文只补缺项"]
  wait(["交母稿等待确认<br/>不出图、不上传"])
  mode{"本轮执行哪种模式？"}
  identity["核本人身份与真实字段<br/>解析母稿及平台子表"]
  target{"唯一记录匹配结果？"}
  create["复查关联及未占用编号<br/>创建唯一子记录后读回"]
  generate{"还需生成图片？"}
  lock[("保留完整母稿和身份字段<br/>锁定source.json与哈希")]
  ready{"图片技能及运行依赖可用？"}
  render["调用图片技能<br/>分页、渲染、逐页验收"]
  existing["核现有包、源稿哈希<br/>manifest与校验结果"]
  package{"双校验、全文、哈希<br/>零溢出及顺序均通过？"}
  delivery{"是否包含飞书写回？"}
  local(["交本地图片包、顺序<br/>哈希与校验结果"])
  attachments{"附件字段处于哪种状态？"}
  write[("写逐页全文并串行上传<br/>不动无关附件和发布值")]
  readback["独立回读文字和附件<br/>不明结果先查实际记录"]
  qa{"页数、末句、顺序<br/>附件及原权限均一致？"}
  state["更新真实已定稿状态<br/>再次回读状态与附件"]
  done(["交飞书记录与验收回执<br/>公开发布仍需独立授权"])
  stop(["暂停对应动作并说明缺口<br/>冲突不盲重试或重复创建"])
  request --> approved
  approved -->|"否：母稿待确认"| draft
  draft --> wait
  approved -->|"是：沿用原授权"| mode
  mode -->|"只要本地图片"| lock
  mode -->|"完整飞书或纯上传"| identity
  identity --> target
  target -->|"匹配一条且身份字段可用"| generate
  target -->|"零匹配且已授权创建"| create
  target -->|"重复、身份或字段异常"| stop
  target -->|"零匹配且无创建授权"| stop
  create --> generate
  generate -->|"是：完整流程"| lock
  generate -->|"否：只上传现有包"| existing
  lock --> ready
  ready -->|"可用"| render
  ready -->|"缺依赖：保留母稿"| stop
  render --> package
  existing --> package
  package -->|"不通过"| stop
  package -->|"全部通过"| delivery
  delivery -->|"否：本地模式"| local
  delivery -->|"是：已含飞书范围"| attachments
  attachments -->|"全空或已明确替换范围"| write
  attachments -->|"全非空且无需追加"| readback
  attachments -->|"部分非空或替换冲突"| stop
  write --> readback
  readback --> qa
  qa -->|"一致"| state
  qa -->|"不一致：先查实际结果"| stop
  state --> done
```

</details>
