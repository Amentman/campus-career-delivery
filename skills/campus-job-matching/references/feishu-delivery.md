# 飞书交付：本人CLI、既定表、独立回读

## 本人身份

使用者须在自己的私有配置中登记本人账号、预期 open_id 与 profile；本公开 Skill 不预设账号归属。

```bash
lark-cli auth status --verify --json
```

开工静默核对identities.user的登录状态、openId与profile/appId；同时显示的bot状态不代表操作身份。所有后续命令显式 `--as user`，正常不追问、不重复登录、不切换或改配置，不索取/打印token。

真实权限错误核对对象、表ID、本人访问权限和参数；只暂停受影响写入。不得换应用身份/tenant token/机器人/其他人，不自动加应用协作者，不新建替代表。

## 对象、字段与保护基线

解析Wiki/Base，核对唯一学生目录、父级、目标表、标题、所有者、权限与修订号。读真实字段ID、类型、选项、视图和全量分页，不混用Wiki/Base/table token。

先看当前CLI `--help`，不沿用旧OpenAPI形状。已有唯一投递表则只追加ready子集，不覆盖整表；确无表时按下节创建。写前保存全量记录、字段、权限、元信息快照。

按真实字段映射公司、岗位、接受城市、学历/毕业要求、入口/详情、JD、匹配证据、缺口、核验状态/时间、截止、行业、性质与批次。不存在的列不得猜名或自动创建。

人工审核、投递日期/人/截图、投递/面试/笔试状态、人工备注及已有优先级默认保护。初次新行是否写“已选岗”按现有约定；不得代填“审核通过/已投递”。

质检状态、时间、关键待确认项和证据入口必须可读。缺专列可用现有备注；不把说明塞进URL。无法在既有结构呈现关键缺口时，先准备最小字段方案再解决必要授权，不默默省略。

## 学生没有投递表：原格式建到本人学生目录

用户已明确授权这项选岗交付动作，无需再次确认账号、目录或建表许可。只做流程复盘/Skill维护时不实际创建学生表。

1. 优先读取私有入口配置 `~/.codex/campus-job-matching.local.json`（存在时）及学生已有入口，重新读取当前父链。本人个人知识库的既有路径是 **校招交付 → 学员交付知识库 → 学员档案 → 学生正式姓名**；“学生目录”指这条链下该生唯一页面，不是本地文件夹、团队空间根目录或“职业规划”。不能因为团队space-list没有个人库就新建空间。
2. 分页读完该学生子节点，同时检查学生正文、档案索引和既有交付入口中的外部Base链接。表也可能是Drive Base并未挂为Wiki子节点。按标题、学生归属、原始Base token核对；同一Base多个链接只算一个。唯一表存在则复用，多个不同表或学生节点有实质歧义才解决该冲突；列表未读全、403/404或搜索无命中均不能单独证明缺表。
3. 确认不存在后再找格式：用户指定模板优先，其次已确认的空白标准模板，再次参考同目录既有标准投递表。读取字段名称/类型/选项、列顺序、通用视图/筛选/排序，并保存来源与时间。保留公司、投递岗位、城市、岗位分类、行业/性质、直达链接、审核、投递进度、投递人/时间、笔试/面试状态和附件等原模板实际字段；不要用另造的简版替换原格式。城市/岗位分类选项按本生已确认意向适配，不继承参考学生的意向或把旧选项池当选岗白名单。不同模板冲突先选与本次已确认格式一致者，不能盲目取最近创建的学生表。
4. **仅复制结构。** 校验来源无自动发送/回写流程和学生专属关联后，干净模板可用 `base +base-copy --without-content --as user`。历史学生表含异常选项、日期批次视图、外部关联、自动化或学生内容时，改为从已读结构白名单建空表/字段/通用视图，不整份克隆。排除串列产生的错误选项，不复制岗位、审核/投递记录、附件、人员默认值、其他学生姓名、批次筛选或协作者权限。保留原模板不动。
5. 默认标题按现有惯例 `选岗/投递表 【姓名】`。Drive目录用已确认的 `--folder-token`；Wiki学生页用明确的space+parent创建bitable后配置结构，或把已建空Base移动到该学生页。个人库入口通过当前CLI解析，先确认真实space_id；不得把Wiki节点token传给folder-token，也不能省略父级落到根目录。

```bash
lark-cli base +base-copy --help
lark-cli base +base-create --help
lark-cli base +table-create --help
lark-cli wiki +node-create --help
lark-cli wiki +move --help
# 干净模板在Drive目录：所有占位符均先由真实读取解析
lark-cli base +base-copy --base-token TEMPLATE --name '选岗/投递表 【姓名】' \
  --without-content --folder-token STUDENT_DRIVE_FOLDER --time-zone Asia/Shanghai --as user
# Wiki目录可直接创建bitable；不能省略space和parent
lark-cli wiki +node-create --space-id SPACE --parent-node-token STUDENT_NODE \
  --obj-type bitable --title '选岗/投递表 【姓名】' --as user
# 若先建Drive空Base，则移动已有对象，不重建第二张
lark-cli wiki +move --obj-type bitable --obj-token NEW_BASE \
  --target-space-id SPACE --target-parent-token STUDENT_NODE --as user
```

创建前再次列目录排除并发新建；创建/复制一返回就保存Base、table、node token及创建响应。超时先搜索/列目录/查询已有任务，确认实际结果后续接同一个对象；不能盲重试新建、不能因挂载失败再建第二张。

写岗位前验收：本人owner/creator、唯一标题与正确父链、字段类型/选项和列顺序、通用视图、**全表零业务记录/零历史附件**、权限不超出该学生目录原有已授权范围且没有复制来源协作者。复杂关联或默认值无法安全复现时先处理具体差异，不带病写入。新表ID登记回已有本地入口/本次manifest，历史快照为 `[]`；已有表读取全量真实历史。新建通过不表示岗位质检通过，后续仍只写ready。

## 写入

- 从ready.json生成字段白名单，确认画像/岗位/简历指纹未变、证据未过期、独立终审通过。备注/已有匹配列呈现终审结论、简历证据、JD要求、差距与关键Open；完整简历/审计材料保留本地，不整份粘进岗位表。不能绕过报告直接从原候选写入。
- 三种模式沿用同一学生投递表和历史，不因社招/BOSS另建重复表；按现有分类/备注区分模式、平台与表单/沟通入口。选岗只能按原约定标“已选岗”；不把ready或沟通按钮可见写成已联系、已发简历、已投递。沟通/投递状态须有实际事件证据，保留原人工值，不为本轮扩展改旧表字段或权限。
- 15–25条一批串行，单次API最多200条，实际CLI限制以help为准；每批读回后再写下一批。
- 当前 `+record-batch-update` 是对一组record_id用同一patch；每行不同值不能硬塞旧records数组。选择实际支持的逐条upsert等能力。
- 不整行空值覆盖、不删除用户空行；公司上限和去重用全量标准历史，不用当前视图代替全表。
- 频控串行退避，仅重试未完成对象。超时先回读确认实际结果，不盲目重建/重复上传。

## 附件与视图：改用CLI原生能力

旧token版上传和视图脚本已移出运行目录。附件先核对真实attachment字段、record_id、已有附件和本地文件；不自动建字段，不用公司子串或岗位前四字模糊配图。使用record_id+岗位键明确映射，解决无命中/多命中再上传。

```bash
lark-cli base +record-upload-attachment --help
lark-cli base +record-upload-attachment --base-token BASE --table-id TABLE \
  --record-id RECORD --field-id ATTACHMENT_FIELD --file /absolute/path/JD.png --as user
```

该命令追加附件，重跑先读已有项避免重复；替换/删除旧附件按授权处理。写后回读file_token、文件名、数量和目标；必要时CLI下载比对哈希/尺寸并实际看图，success不替代可访问性与内容验收。

```bash
lark-cli base +view-get-visible-fields --help
lark-cli base +view-set-visible-fields --help
```

视图修改前保存原配置。visible_fields同时改可见性和列顺序，需提供完整目标列表，不是行排序。行排序用 `+view-set-sort`，筛选用 `+view-set-filter`；均 `--as user`，写后get核对。仅追加优先保留原视图，不为排序建重复字段或改权限。

## 独立验收

重新分页读全表和本批record_id，分两类结果：

1. 业务质检：每条对应ready与新鲜的本模式条件/岗位/表单或沟通入口证据；合格、待核验、受阻、剔除分别计数，并说明实际核验范围，主字段非空不是有效可投。
2. 写入一致性：新增ID/字段与计划一致，截图/链接对应，累计公司限额与去重正确；历史人工字段、标题/父级/所有者/权限/结构未意外变化。并发人工编辑单列，不回滚别人的改动。

实际查看飞书行、链接打开、附件和长文本阅读路径。后台浏览器受阻时分别说明数据已验与视觉未验，不冒充全部通过。最终报告修改对象、只读对象、本地文件、未触碰对象与Open项。
