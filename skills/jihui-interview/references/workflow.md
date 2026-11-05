# 知识库采访：完整流程

输入：业务本人回答；现有知识库路径（如有）；业务与内容背景。

交付：业务知识库骨架；产品与客户原话素材；文件路径及资料缺口。

![完整流程图](../assets/workflow.svg)

[按原尺寸打开完整流程图](../assets/workflow.svg)

## 按什么顺序做

### 复用入口与采访进度

使用当前成员材料；已有回答计入覆盖，每次只问一题。

### 追问具体事实

客户原话和卖点人话优先；单题最多追问两次，缺项待补。

### 完成六类采访与目标定位

逐组记录覆盖；第19题沿用或补齐既有库与保存位置。

### 按真实结构归位

已有库先只读结构，只新建补充；无库才新建六大库。

### 按复杂度安排总览

复杂关系在适合的新补充或新README中展示，简单业务记录无图原因。

### 逐项回读并报告

核位置、来源、缺项和旧文件未动；不可写时只交整理稿。

## 验收

- 19题均有覆盖或待补记录
- 每题最多两次追问且保留原话
- 只新建，原文件零修改移动删除
- 逐项读回位置、来源与真实覆盖
- 复杂关系在目标渲染器中可读；缺依赖不称已验收

采访内容按既有授权归档，不向外部自动发送。

## 对应规则

- [SKILL.md](../SKILL.md)
- [references/team-setup.md](team-setup.md)

<details>
<summary>可编辑的流程源码</summary>

```mermaid
flowchart TB
  request(["建库请求<br/>业务材料与已知入口"])
  known["开场并复用已知回答<br/>按六组建立19题覆盖表"]
  covered{"本题已有明确答案？"}
  ask["一次一题<br/>追原话、例子与人话卖点"]
  specific{"回答具体且有用？"}
  follow["换角度追问<br/>每题最多两次"]
  record["记录已覆盖或待补<br/>组末说明实际缺项"]
  progress{"继续、收尾或暂停？"}
  pause(["记录断点<br/>仅向已授权位置保存"])
  existing{"已有知识库？"}
  structure["只读原目录<br/>找到对应分类或采访补充"]
  newplan["规划六大库与新README<br/>保留原话与来源"]
  target{"保存目标唯一且可写？"}
  draft(["交付可用整理稿<br/>说明缺入口或尚未保存"])
  complex{"复杂关系且有合适总览位置？"}
  visual["按采访证据画关系<br/>检查Mermaid或改关系表"]
  novisual["简单业务不强画<br/>无位置或缺依赖据实说明"]
  write[("仅新建采访文件<br/>新库加入说明与来源双标签")]
  verify{"新文件读回、旧文件未动？"}
  incomplete(["报告未通过项<br/>不称全覆盖或已验收"])
  done(["交付文件映射与实际覆盖<br/>列出六库缺项"])
  visualready{"共享图解能力可用？"}
  request --> known
  known --> covered
  covered -->|"是：复用答案"| record
  covered -->|"否：单题采访"| ask
  ask --> specific
  specific -->|"是：记录原话"| record
  specific -->|"否：尚未追问两次"| follow
  specific -->|"否：已达上限，待补"| record
  follow --> ask
  record --> progress
  progress -->|"尚有未覆盖题"| covered
  progress -->|"19题覆盖完毕"| existing
  progress -->|"用户暂停"| pause
  existing -->|"有：融入原结构"| structure
  existing -->|"无：按指定位置建库"| newplan
  structure --> target
  newplan --> target
  target -->|"否：补位置或连接能力"| draft
  target -->|"是：继续落盘"| complex
  complex -->|"是：有证据和位置"| visualready
  complex -->|"否：简单或无合适位置"| novisual
  visual --> write
  novisual --> write
  write --> verify
  verify -->|"通过"| done
  verify -->|"不通过"| incomplete
  visualready -->|"可用：成图并实测"| visual
  visualready -->|"缺依赖：仅文字稿，图解待补"| novisual
```

</details>
