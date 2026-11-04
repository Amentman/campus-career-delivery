# Skill 来源全量清单

2026-11-04盘点本机32个非系统Skill。18个既有公开业务Skill加知识库采访、朋友圈写作、腾讯会议导出，合计21个随本仓库提供。微信本地能力作为可选连接器单独交接，不把密钥捕获、数据库和运行环境复制进本包。另10个通用Skill记录上游，不改名纳入本包版权。

“本人维护”描述当前维护与授权范围，不把引用的第三方方法或工具版权算成作者独有。现有LICENSE覆盖本包作者有权分发的材料；第三方工具按其上游许可安装。腾讯会议导出为本机维护的定制脚本，保留原注释；未携带真实账号、录制链接、密码或状态。

| # | Skill | 分类与公开处理 | 证据 |
|---:|---|---|---|
|1|auditing-candidate-resumes|既有用户维护公开业务包，保留MIT|公开目录；LICENSE:3；PROVENANCE:3|
|2|building-resume-interview-stories|同上|同上|
|3|campus-job-matching|同上；外部架构借鉴应保留链接|references/source-adapters.md:5-7|
|4|campus-recommend|同上；兼容入口|SKILL.md:8|
|5|delivering-student-career-plans|既有用户维护公开业务包|LICENSE/PROVENANCE|
|6|designing-student-portfolio-products|同上|同上|
|7|job-content-publisher|同上|同上|
|8|job-sales-advisor|同上|同上|
|9|multi-source-todo-control|同上|同上|
|10|personal-todo-control|同上|同上|
|11|recording-processing|同上|同上|
|12|revising-and-delivering-resumes|同上|同上|
|13|student-interview-review-delivery|同上|同上|
|14|student-job-content|同上|同上|
|15|student-mock-interview-delivery|同上|同上|
|16|student-role-interview-prep|同上|同上|
|17|visual-document-delivery|同上|同上|
|18|xiaohongshu-image-renderer|同上|同上|
|19|jihui-interview|已纳入：用户品牌业务Skill，不携带知识库|本地 SKILL.md:4-7,11,21 明确寂辉品牌|
|20|pengyouquan-copywriting|已纳入：用户内容体系Skill，私人案例改为明确模拟示例|本地 SKILL.md:12“由寂辉53篇已发布朋友圈实战版提炼”|
|21|tencent-meeting-cloud-export|已纳入：本机业务定制维护范围，保留原注释与浏览器能力限制；不宣称未知上游版权归作者|SKILL.md:12-14,18-35；scripts/export.py:1-4；无LICENSE/NOTICE/source|
|22|yichen-wechat-local-vault|只列私有可选连接器依赖，暂不整包分发|本地SKILL:13-16称吸收外部工具；无LICENSE/来源；既有公开PROVENANCE:17明确不分发私人解析器|
|23|miniprogram-development|第三方 Tencent CloudBase，上游依赖/安装来源，不归入自有业务MIT|本地SKILL.md:12-19明确上游；官方GitHub LICENSE=MIT（2026 TencentCloudBase）|
|24|browser-use|第三方 browser-use/browser-harness，仅记上游|本地SKILL.md:8；官方repo显示MIT；个人补丁不改变上游所有权|
|25|deep-research|第三方199-biotechnologies，仅记上游|本地README.md:9,117-119；官方README宣称MIT，但独立LICENSE URL返回404|
|26|figma-cli|第三方silships/figma-cli，仅记上游|本地SKILL.md:72-77；官方LICENSE=MIT，2026 Sil Bormüller|
|27|file-organizer|疑似ComposioHQ/awesome-claude-skills派生；只记候选上游并标未完成对应，不复制|本地无源/许可证；本轮上游LICENSE(master)404；不可据同名强行认定|
|28|find-skills|第三方Vercel skills，仅记上游|本地description与官方skills/find-skills/SKILL.md一致；官方LICENSE=MIT，2026 Vercel|
|29|frontend-design|第三方/本地改写；Apache2，不直接放入自有MIT|本地SKILL:4指向LICENSE.txt；LICENSE完整Apache2；精确上游revision未记录|
|30|impeccable|第三方Paul Bakaus，仅记上游|本地scripts/concept-seed.mjs:71,99指impeccable.style；官方LICENSE=Apache2，2025 Paul Bakaus；本地缺许可证|
|31|jupyter-notebook|第三方OpenAI skill，本地Apache2|本地LICENSE.txt完整Apache2；公开OpenAI来源需精确revision核对；非业务自有|
|32|ui-ux-pro-max|第三方NextLevelBuilder，仅记上游|官方skill.json声明作者、repo、MIT；官方LICENSE=2024 Next Level Builder；本地无license|


## 外部能力怎么接入

微信来源优先使用成员已配置且获授权的连接器或明确导出的聊天文件。需要刷新、导出或密钥/环境操作时按该动作单独授权；无法读取图片时不描述图中内容，读取失败不等于没有新消息。原有本地私有解析能力保留，不因公开包优化而删除或重装。

浏览器、设计、Word/PDF、聊天与知识库能力按任务需要配置；已安装同等能力可直接使用，不要求所有成员复制制作者的完整工具栈。上游入口如下：

- Browser Harness：https://github.com/browser-use/browser-harness
- Deep Research：https://github.com/199-biotechnologies/claude-deep-research-skill
- Figma CLI：https://github.com/silships/figma-cli
- Find Skills：https://github.com/vercel-labs/skills
- Impeccable：https://github.com/pbakaus/impeccable
- CloudBase：https://github.com/TencentCloudBase/cloudbase-skills
- UI UX Pro Max：https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
- OpenAI自带文档与Notebook能力：由运行器或其官方技能包提供，保留原许可。

file-organizer与本地改写的frontend-design不凭同名猜精确上游版本；保留当前安装与其已有许可，获取来源后再决定是否分发。此清单不承诺第三方仓库可用性或本地副本与最新上游一致。
