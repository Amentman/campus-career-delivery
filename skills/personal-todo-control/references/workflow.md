# 个人待办与跟进：完整流程

输入：当前聊天与真实记录；服务主表和项目状态；时间范围与完成反馈。

交付：综合待办与晨间顺序；责任人、检查点与等待项；延期和来源覆盖记录；授权模式下的次日协同台账。

![完整流程图](../assets/workflow.svg)

[按原尺寸打开完整流程图](../assets/workflow.svg)

## 按什么顺序做

### 锁定模式与覆盖范围

记录资料截止、适用日期、来源与写入授权；不把整理当更新。

### 读取当前权威证据

动态读来源与全量名册；微信现有快照优先，未覆盖和新鲜度缺口可见。

### 恢复事项与责任

四类工作只归一类；学生新请求无人实质承接由本人兜底。

### 排序并审计结转

P0–P3和八桶；等待不算拖延，同ID同目标日不重复累计。

### 按授权维护目标

普通更新限定字段；全量学生与双台账分别对账，协作模式按专用合同。

### 保护人工并最小写入

人工六字段不覆盖，稳定ID去重；批次读回、超时先查不盲重试。

### 分别验收与交付

覆盖、数量、修订、公式、未授权字段与缺口分别报告。

## 验收

- 截止与未覆盖范围明确
- 全量名册每行归入已写/无需变更/异常/未覆盖
- 学生无人接单与主动服务过5天兜底正确
- 稳定ID、人工勾选排除及同目标日结转去重
- 六人工字段零自动覆盖且默认视图无筛选
- 服务主表与索引按授权分别回读
- 超时先判实际结果，公式和历史资源保留

整理不授权对外发送；同步仅限已授权对象和字段。

## 对应规则

- [SKILL.md](../SKILL.md)
- [references/maintained-collaboration.md](maintained-collaboration.md)
- [references/team-setup.md](team-setup.md)

<details>
<summary>可编辑的流程源码</summary>

```mermaid
flowchart TB
  input(["待办整理、日结或更新请求<br/>本轮时间窗与已给入口"])
  scope["注明资料截止与适用日<br/>锁定允许读取和写入对象"]
  read["协作先读历史人工值<br/>再读可用来源，缺口可见"]
  extract["还原动作、责任、时间与证据<br/>按稳定事项去重"]
  student{"学生事项是否需要本人兜底？"}
  fallback["无人实质接单列本人P0<br/>过5天跟进仅限主动服务"]
  assigned["明确接手才转盯结果<br/>已发送但未验收转等待"]
  classify["四类工作、八桶与P0–P3<br/>每项一个主动作与完成标准"]
  rollover["继承真实计划与迁移计数<br/>等待/受阻不算拖延，同日去重"]
  mode{"本轮实际执行模式？"}
  summary(["输出完整执行清单与顺序<br/>外发版脱敏，列覆盖缺口"])
  ledgerread["读全部注册历史人工值<br/>云端为准，同日复用唯一台账"]
  ledgertarget{"本人身份、注册目标与权限可用？"}
  merge["排除历史勾选并继承人工值<br/>未完与新请求按稳定ID合并"]
  early{"提前导入的已完成副本？"}
  withdraw["无独立人工新改才备份撤副本<br/>有新改保留冲突，不删历史"]
  guard{"补丁只含白名单系统字段<br/>人工六字段保护检查通过？"}
  ledgerwrite[("复用或授权新建次日台账<br/>无筛选默认视图，全部未完")]
  objects["动态解析授权目标与字段<br/>服务表、索引分别名册对账"]
  unique{"行/档案唯一且字段已授权？"}
  diff["记录逐格前值、拟值与证据<br/>无新证据不写，保留公式历史"]
  revision{"写前修订仍与差异一致？"}
  reread["重读目标格并重算差异<br/>不覆盖并发人工修改"]
  update[("最小差异串行写入<br/>学生批次每批最多20行")]
  qa{"本批/台账完整独立回读通过？"}
  recover["按账本确认已写/未写/部分写<br/>只重试确认未写部分"]
  next{"验收后如何继续？"}
  done(["分别报告应处理、已写、无需变更<br/>异常、未覆盖及保护证据"])
  stop(["暂停异常对象或字段<br/>保留冲突与可用只读结果"])
  cache[("协作台账读回后<br/>原子保存注册与证据缓存")]
  input --> scope
  scope --> read
  read --> extract
  extract --> student
  student -->|"是：未接单或需主动跟进"| fallback
  student -->|"否：已接单/等待/其他事项"| assigned
  fallback --> classify
  assigned --> classify
  classify --> rollover
  rollover --> mode
  mode -->|"汇总/日结/脱敏且不写入"| summary
  mode -->|"已授权每日协作台账"| ledgerread
  mode -->|"已授权指定对象更新"| objects
  ledgerread --> ledgertarget
  ledgertarget -->|"否：对象异常不建替代"| stop
  ledgertarget -->|"是：已有对象或已授权父级"| merge
  merge --> early
  early -->|"是：核副本独立人工变化"| withdraw
  early -->|"否：正常增量"| guard
  withdraw --> guard
  guard -->|"通过：只补系统字段"| ledgerwrite
  guard -->|"拒绝：含受保护字段"| stop
  ledgerwrite --> qa
  objects --> unique
  unique -->|"否：身份、唯一性或授权缺口"| stop
  unique -->|"是：锁定白名单"| diff
  diff --> revision
  revision -->|"不一致：重算"| reread
  reread --> diff
  revision -->|"一致：仅写差异"| update
  update --> qa
  qa -->|"通过：含公式与只读锚点"| next
  qa -->|"超时、部分写或读回不一致"| recover
  recover -->|"已定位普通更新未写部分"| diff
  recover -->|"台账先重读云端再重算"| ledgerread
  recover -->|"无法判定或人工冲突"| stop
  next -->|"普通更新：还有批次或第二对象"| objects
  next -->|"普通更新：全部覆盖"| done
  next -->|"协作台账：全量回读通过"| cache
  cache --> done
```

</details>
