# 最新简历 × 完整JD独立终审

这是每轮最终名单形成后、统一离线关卡和飞书写入前的必经步骤。初筛理由和高分只是候选排序，不能替代终审，也不能证明真实性。可以按批次进行独立阅读，不必每个岗位启动新Agent。

## 怎么复核

给终审的输入仅包含：当前确认的原简历及完整提取正文、本次学生意向/硬限制、完整官方JD和岗位身份、公开资格/申请证据。先完成新判断，再对照初筛；不把初筛分数、推荐文案、别人“已通过”的结论作为判断依据。完整核对原文件和提取内容，确认没有丢页、漏表或混入另一份简历；hash不能证明提取正确或原件确为最新。

逐岗执行：

1. 先锁定模式：校招比对毕业窗口；实习比对在校身份与出勤/到岗；社招比对正式/相关工作月数、职责层级、薪资及行业要求。学历、专业、城市、用工共同检查。社招/实习不强塞通用毕业届别；JD确有限制仍检查。核对适用范围，未知不猜。键与数值契约见 [模式与平台](search-modes.md)。
2. 拆开JD的全部核心职责和要求，以业务动作、对象、产出核对简历。逐项记录原文证据：直接经验、可迁移经验、差距或未知；只有兴趣/关键词不算证据。教学知识不能写成学生经验，导师指导的本人实践正常计入。
3. 把“必须/需要/任职条件”与“优先/加分”分开。学历专业等放hard_conditions，能力/经验要求放requirements；全量覆盖JD要求，不只挑容易满足的一项。没有独立技能条件时，可把JD明确的职责能力要求作为mandatory项，保留原文和理由，不凭空添加要求。
4. 明确结论、支持它的简历/JD原句、主要差距与Open。必备条件明确不符→reject；未知或需补证后才能推荐→conditional；公开资格和核心职责有证据、无阻断未知→recommend。优先项差距本身不否决，但必须真实展示。
5. 同时保留反对理由。发现名称相近但实际职责不同、简历没有必备技能、岗位偏离意向时剔除/降为待核验，不能靠总分补偿。Agent继续自行追查可解决的问题，只把确需用户判断的冲突提出来。

## final_review 数据结构

| 字段 | 必需内容 |
|---|---|
| method / verdict | fresh_resume_jd；recommend / conditional / reject |
| reviewed_at / job_key | 实际带时区ISO时间；与脚本job_key一致（id:tenant:job_id或标准URL） |
| summary | 具体结论与原因，不用单一百分比或“匹配度高”代替 |
| source_hashes | resume_file、resume_text为两份本地文件原始字节SHA-256；jd_text为完整JD字符串UTF-8字节SHA-256；profile为完整画像JSON指纹 |
| hard_conditions | degree、major、city、employment，加本模式条件：campus为graduation；internship为student_status/schedule；experienced为experience/seniority/salary。每项含status=pass/fail/unknown和独立reason |
| duties | 核心职责数组；每项jd_quote、resume_quote、assessment=direct/transferable/gap/unknown、reason |
| requirements | 必备/优先要求数组；每项jd_quote、resume_quote、priority=mandatory/preferred、assessment=met/gap/unknown、reason |
| gaps | 实际差距字符串数组；确无差距用[]，不编造待复习项 |
| open_items | `{item: "具体未知", blocking: true/false}`数组；无Open用[]。资格、核心职责或必备能力未知不能标成非阻断 |

画像指纹与脚本一致：`sha256(json.dumps(profile, ensure_ascii=False, sort_keys=True).encode()).hexdigest()`。不能先写虚假hash/pass再找材料。正向匹配的resume_quote、所有jd_quote必须逐字来自对应完整正文，允许忽略排版空白；概括和解释放reason。引用命中只是来源检查，不代表语义成立。

脚本拦截缺终审、错岗位、过期、原件/正文/JD/意向变更、引文不存在、必须项缺口/未知、无职责证据配对与阻断Open。requirements/duties非空不证明覆盖完整，hard_conditions的pass不证明事实正确，**全部职责/条件的覆盖、引文含义和推荐是否合理仍由Agent逐条审核**。原文件、意向、JD或规则有变化必须重审，不能只重算hash沿用旧结论。

每条交付的可读结论为：`建议投递/待核验/不推荐 + 简历具体证据 + 对应JD职责/要求 + 差距与Open`。飞书只写通过子集及简明结论；待核验与剔除留在独立本地报告，不能混进合格数。流程改进和合成测试不能推出真实准确率，更不能承诺100%。
