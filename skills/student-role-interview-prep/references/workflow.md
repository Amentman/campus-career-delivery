# 专岗面试准备：完整流程

输入：最新简历与已有材料；公司、岗位和 JD 或邀约；唯一专岗目标。

交付：独立专岗准备材料；公司与 JD 证据矩阵；示范稿、案例与训练任务。

![完整流程图](../assets/workflow.svg)

[按原尺寸打开完整流程图](../assets/workflow.svg)

## 按什么顺序做

### 先确定专岗对象与保护页

唯一同岗页原地更新，新岗独立；通用双端和其他专岗保持只读，图片验收续接不重做研究。

### 公司基本面与 JD 证据

先做独立公司调研和岗位含义，再映射直接证据、迁移证据与缺口；业务单元未知分支准备。

### 完整组织故事、知识和表达

S/K与四种表达身份分开，提供示范稿、案例及训练；短轮次先给速读仍保留完整底稿。

### 精准写入对应专岗页

图解先预览，直接嵌入对应正文；只修改已确定专岗，不扩写通用材料。

### 逐图与全文独立验收

结构和网页显示均核对；通道异常按恢复合同处理，已证实缺陷才局部修复。

## 验收

- 公司调研过完成门
- 事实与知识分开
- 正文图解和原页回读
- 图解直接嵌入正文并逐图实际检查

准备一个专岗不授权改通用双端；真实面试转复盘 Skill。

## 对应规则

- [SKILL.md](../SKILL.md)
- [references/company-fundamentals-research.md](company-fundamentals-research.md)
- [references/content-and-expression.md](content-and-expression.md)
- [references/feishu-boundary-and-acceptance.md](feishu-boundary-and-acceptance.md)
- [references/feishu-image-browser-recovery.md](feishu-image-browser-recovery.md)

<details>
<summary>可编辑的流程源码</summary>

```mermaid
flowchart TB
  in(["学生原简历、公司/JD/邀约<br/>本轮轮次、目标与已有材料"])
  route{"面试前专岗还是其他任务？"}
  companion(["通用模拟／真实复盘<br/>转对应独立 Skill"])
  locate["读真实资料与原页版本<br/>核对同公司、同岗位和职位号"]
  target{"学生与同岗页定位结果？"}
  stop(["列关键冲突，暂停依赖写入<br/>不另造整套档案或替代页"])
  scope{"当前只续图片验收／明确短稿？"}
  short["只做用户明确限定的短表达<br/>线性短稿记录无图理由"]
  company["独立研究当前公司基本面<br/>事实→岗位意义→表达／反问"]
  unit{"实际业务单元明确？"}
  branches["集团事实＋候选业务分支比较<br/>内部团队/KPI待确认，准备切换回答"]
  evidence["JD逐条映射直接／迁移／缺口<br/>排列学生核心经历优先级"]
  body["S故事＋K岗位知识＋案例路径<br/>示范口语、题卡和可验收任务"]
  round["最前提炼本轮速读与必练<br/>HR五分钟仍保留完整底稿"]
  images["生成并预览必要业务图／证据图／Case图<br/>对应章节直接显示，失败不插占位"]
  delivery{"本轮图解与写入条件齐备？"}
  draft(["交付用户指定短稿／可审阅材料<br/>缺写入条件不称正式专岗完成"])
  write["同岗原位更新；新岗独立创建<br/>只写授权专岗，分章读回"]
  inventory["读回全文、父级、媒体和保护页<br/>按清单打开对应章节逐图检查"]
  display{"网页图片通道可用且全部覆盖？"}
  recover["重核目标与会话，换可用通道<br/>只在已有授权内恢复，不重复上传"]
  partial(["记录媒体／结构已验及网页未验<br/>保留具体故障与缺项"])
  gate{"公司、内容、实际显示与保护通过？"}
  fix["仅修已证实缺项和受影响区块<br/>再回读、逐图与适用范围复验"]
  out(["交付独立专岗链接与修订<br/>公司资料截止日、原页保护及Open"])
  in --> route
  route -->|"通用训练／已发生面试"| companion
  route -->|"明确专岗面试前准备"| locate
  locate --> target
  target -->|"身份／目标多候选"| stop
  target -->|"唯一同岗：原地复用"| scope
  target -->|"新岗无匹配：锁定独立父级"| scope
  scope -->|"仅续接图片验收"| inventory
  scope -->|"用户明确只要短稿"| short
  scope -->|"完整准备／仅轮次短"| company
  company --> unit
  unit -->|"业务归属有证据"| evidence
  unit -->|"实际单元未知"| branches
  branches --> evidence
  evidence --> body
  body --> round
  round --> images
  images --> delivery
  short --> delivery
  delivery -->|"限定聊天／本地／暂缺写入条件"| draft
  delivery -->|"已授权且唯一"| write
  write --> inventory
  inventory --> display
  display -->|"逐图实际可见、覆盖齐全"| gate
  display -->|"超时／白屏／离屏／冲突"| recover
  recover -->|"恢复后重新观察"| inventory
  recover -->|"仍不可检查／需要未获授权前台"| partial
  gate -->|"本轮适用项全部通过"| out
  gate -->|"已证实内容／显示缺陷"| fix
  fix --> write
  delivery -->|"必需图未生成／预览不可读"| partial
```

</details>
