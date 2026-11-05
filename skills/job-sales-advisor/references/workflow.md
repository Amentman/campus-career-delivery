# 求职咨询与销售跟进：完整流程

输入：客户问题与对话；最新产品与报价口径；相关案例和服务证据。

交付：客户判断与知识抓手；可发送微信话术；跟进动作与风险提醒。

![完整流程图](../assets/workflow.svg)

[按原尺寸打开完整流程图](../assets/workflow.svg)

## 按什么顺序做

### 按交付对象分流

普通回复和顾问方向引导由本 Skill 处理；正式学生规划、作品集转对应合同。

### 先检索当前成员知识库

读索引及直接相关全文，分清客户事实与库内依据；没有库时用本次材料继续并注明事实缺口。

### 诊断客户并选择任务路径

按问题处理短回复、方向建议或报价异议；技术与读博不套非技术模板，价格冲突不编数字。

### 组织可发内容与下一动作

只选一两个相关抓手，规划核心表可独立转发，复杂说明才配关系图。

### 核对承诺、案例与隐私

产品卖点回查当前定义；HC与Offer分开，输出话术不等于对外发送。

## 验收

- 卖点有当前来源
- 案例状态不夸大
- 不承诺必进或保 Offer

生成话术不代表已发送；正式学生规划转对应 Skill。

## 对应规则

- [SKILL.md](../SKILL.md)
- [references/knowledge-base-routing.md](knowledge-base-routing.md)
- [references/product-pricing-sources.md](product-pricing-sources.md)
- [references/technical-career-planning.md](technical-career-planning.md)

<details>
<summary>可编辑的流程源码</summary>

```mermaid
flowchart TB
  in(["客户原话、背景与当前问题<br/>本次交付对象和产品资料"])
  route{"本次要求什么交付？"}
  companion(["正式学生规划／作品集设计<br/>转对应 Skill，不用销售卡替代"])
  kb["定位当前成员知识库<br/>读取实际索引、提炼层检索词"]
  available{"有可访问的相关知识依据？"}
  evidence["完整读直接支撑回复的文件<br/>核对日期、定义与来源"]
  nokb["用本次材料与表达方法继续<br/>缺产品事实明确待补，不套作者资料"]
  customer["分清客户事实／共性／待核验<br/>判断阶段、顾虑与现实约束"]
  task{"当前主要问题？"}
  short["短输入先分客户层<br/>选择可发送回复与一个下一步"]
  price["读取当前报价／合同口径<br/>核对最新确认来源与适用条件"]
  pricegate{"报价事实最新且无冲突？"}
  priceopen["不填未确认价格数字<br/>回复已有依据部分并列待确认"]
  planning{"技术／读博还是业务方向？"}
  technical["拆技术方向、项目与知识树<br/>按目标比较就业／读博和主战场"]
  business["按真实经历收窄岗位与公司池<br/>补强动作写清产物和验收"]
  coretable["先给定位＋五列核心表<br/>公司池不等于当前HC"]
  visual{"说明稿含多路线／阶段／交付关系？"}
  draw["核心表保留，再就地用图解释关系<br/>不把计划画成学生成果"]
  compose["普通任务给销售行动卡<br/>只要可复制话术时仅给话术"]
  gate{"事实、承诺、案例状态与隐私通过？"}
  fix["回查来源并收缩不实表达<br/>不承诺必进、保Offer或复现案例结果"]
  out(["交付话术、一个下一动作与关键缺口<br/>生成内容不代表已发送"])
  in --> route
  route -->|"正式完整规划／作品集"| companion
  route -->|"销售回复／顾问方向引导"| kb
  kb --> available
  available -->|"有相关资料"| evidence
  available -->|"无可用库内依据"| nokb
  evidence --> customer
  nokb --> customer
  customer --> task
  task -->|"短回复／普通异议"| short
  task -->|"价格／合同／保障边界"| price
  task -->|"职业方向引导"| planning
  price --> pricegate
  pricegate -->|"已确认：按条件表达"| compose
  pricegate -->|"过期／冲突／缺口径"| priceopen
  priceopen --> compose
  planning -->|"技术岗／读博／工程背景"| technical
  planning -->|"业务／非技术方向"| business
  technical --> coretable
  business --> coretable
  coretable --> visual
  visual -->|"复杂说明关系"| draw
  visual -->|"短回复／简单线性"| compose
  draw --> compose
  short --> compose
  compose --> gate
  gate -->|"可核验且边界清楚"| out
  gate -->|"夸大／冲突／隐私未处理"| fix
  fix --> compose
```

</details>
