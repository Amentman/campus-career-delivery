# 校招交付 Skills 目录

这套目录把22项学生求职与配套服务拆成可独立发现、可组合调用的 Agent Skills。先按用户请求选择一个主入口；需要资料整理、复杂文档或岗位核验时，再调用对应辅助 Skill。岗位搜索和写回必须保留来源、核验时间、证据等级与待确认项。

| Skill | 主入口 | 适用请求 |
| --- | --- | --- |
| `auditing-candidate-resumes` | 候选人审查 | 从 HR/招聘方视角比较简历、识别时间线与岗位匹配风险 |
| `building-resume-interview-stories` | 证据化表达 | 简历要点、JD 映射、项目解释、STAR 故事与面试题 |
| `campus-job-matching` | 校招选岗主入口 | 找真实在招岗位、匹配简历、生成投递清单与截图包 |
| `campus-recommend` | 旧入口兼容 | 仅续接明确引用旧入口的任务，实际依赖campus-job-matching |
| `delivering-student-career-plans` | 职业规划 | 方向地图、公司池、薪资、项目补强、简历分版与时间线 |
| `designing-student-portfolio-products` | 作品集规划 | 基于真实业务设计可落地的作品集前置资料、PRD、Demo 与验收 |
| `recording-processing` | 录音整理 | 会议、课程、咨询或语音备忘的转写整理与获授权知识库分流 |
| `revising-and-delivering-resumes` | 简历修改交付 | 简历诊断、改写、Word/PDF 版本与投递验收 |
| `student-interview-review-delivery` | 真实面试复盘 | 飞书妙记／腾讯会议原稿读取、完整性与漏题对照、逐题纠正与训练 |
| `student-job-content` | 求职内容 | 岗位认知、求职文章、学校与企业差距、项目能力和面试判断 |
| `student-mock-interview-delivery` | 通用模拟面试 | 无明确公司/JD 的老师版、学生版和训练工作簿 |
| `student-role-interview-prep` | 专岗面试准备 | 已有公司、岗位、JD 或邀约的定向准备 |
| `writing-readable-documents` | 文档写作与飞书正文 | 中文文章、讲义和方案的成文、深度改写、参考学习与实际正文审稿 |
| `visual-document-delivery` | 复杂文档验收 | 含流程、关系、时间线、比较或可信数据的文档图解与渲染验收 |
| `multi-source-todo-control` | 学生多源跟进 | 对齐学生群、私聊、导师协作与服务记录，明确缺口和下一步 |
| `personal-todo-control` | 综合待办 | 汇总、日结与协作台账，保护人工字段、历史完成和权限 |
| `job-sales-advisor` | 求职销售咨询 | 依据使用者自己的知识库，整理方向建议、咨询话术与异议回应 |
| `job-content-publisher` | 内容生产写回 | 确认母稿后连续出图、上传飞书与读回，平台公开发布单独授权 |
| `xiaohongshu-image-renderer` | 小红书出图 | 保留完整母稿，分页、渲染、校验并交付本地图片包 |

| `jihui-interview` | 知识库采访 | 逐题访谈，获授权后创建/补充使用者自己的业务知识库 |
| `pengyouquan-copywriting` | 朋友圈写作 | 用使用者真实素材与风格方法写成稿，公开发布另按授权 |
| `tencent-meeting-cloud-export` | 会议资料导出 | 按已登录成员的范围清点/导出，核对账号与后台能力 |

## 路由顺序

1. 用户只说“找校招岗位、筛岗、投递清单”时进入 campus-job-matching；旧任务明确引用 campus-recommend 时转同一主流程。
2. 用户要职业方向和投递节奏时进入 delivering-student-career-plans；不要把真实岗位搜索结果写成静态公司池。
3. 用户要简历改写、排版或投递版文件时进入 revising-and-delivering-resumes；只要解释项目或准备表达，可使用 building-resume-interview-stories。
4. 没有明确公司/JD 的面试训练进入 student-mock-interview-delivery；面试前已有公司/JD 进入 student-role-interview-prep；面试已经发生并有逐字稿进入 student-interview-review-delivery。
5. 录音只做整理时使用 recording-processing；它不能替代真实面试复盘。
6. 作品集需要规划、PRD、UI/UX Demo 或验收标准时进入 designing-student-portfolio-products；规划不等于学生已经完成产品。
7. 正式长文的成文、改写和文风审稿配合 writing-readable-documents；业务主入口继续负责事实与必需内容。任一主入口产出复杂长文、流程图、时间线、角色交接或可信数据图时调用 visual-document-delivery，并按目标格式验收。
8. 学生服务查漏用 multi-source-todo-control；综合个人待办与协作台账用 personal-todo-control。默认先只读，更新只在当前授权范围内。
9. 销售咨询用 job-sales-advisor；正式学生规划仍走独立规划 Skill。已确认的求职母稿需要出图并写回飞书时用 job-content-publisher；仅处理本地图片包时用 xiaohongshu-image-renderer。

## 岗位匹配的硬限制

同一学生每家公司累计默认最多 3 个岗位；当前任务明确另定上限时以该要求为准。真实岗位去重始终执行。岗位完成评分和排序后，先运行 `skills/campus-job-matching/scripts/enforce_company_cap.py`，再生成 Excel、截图包或写回飞书；回读时按公司计数，超过本轮明确上限即判定未完成；历史超额保留并报告，不删除。该限制适用于不同城市、不同方向和同公司的多个职位 ID。

## 公开边界

仓库只提供通用流程、可选脚本和脱敏示例，不包含学生简历、逐字稿、私人知识库、飞书节点、访问令牌或固定本机路径。每个使用者需要在当前任务或自己的配置中提供资料位置、外部工具权限和目标交付面。

## 团队配置与依赖

每个目录的 references/team-setup.md 说明本Skill需要的资源。完整安装器自动带上已声明的必需兄弟Skill；手动复制时补齐其依赖。campus-recommend依赖岗位主Skill；职业规划正式交付校验依赖visual-document-delivery；内容生产写回依赖xiaohongshu-image-renderer。其他文档、浏览器、设计、聊天和知识库能力按任务需要提供，不要求复制作者环境。

完整33源及未整包分发的连接器/上游见 [来源清单](SOURCE_INVENTORY.md)。首次操作见 [团队配置](TEAM_SETUP.md)，更新见 [同步约定](PUBLIC_SYNC.md)。
