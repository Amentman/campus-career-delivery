# 模式条件与平台入口

## 一份主Skill，三种画像

按用户本轮意图确定profile.search_mode：campus / internship / experienced。同一人可以分别选不同模式，但每批规则与合格数量必须分开；保留同一个学生身份、累计公司上限及跨批历史。模式不能由“学历高/毕业久/无工作经历”擅自推断。学历专业或行业经验是否为硬门槛，以当前JD及本人限制为准。

### 校招 campus

维持原毕业年月和官方窗口检查，不擅自归届。默认全职；实习单独用internship模式。非典型毕业时间、国内/海外政策和项目适用范围须有来源。

### 实习 internship

profile包含student_status=enrolled/graduated，以及internship_availability的start_date（YYYY-MM-DD）、days_per_week（>0且≤7）、months（>0）。关键未知不能填0凑完整。比较在校生要求、最晚到岗、每周出勤、持续时长；课程/考试安排按真实限制说明。

job.internship_requirement为 `{days_per_week, months, student_only, latest_start_date?}`；days/months为岗位最低要求，0只表示全文核实后确无最低要求，student_only必须是真实布尔值，未知不能写false。毕业年月不是所有实习的默认门槛；JD确有限制时保留graduation_window继续检查。

### 社招 experienced

先完整梳理工作时间线、用工性质、职责/产出与行业：正式工作按区间去重计月，并行不能叠加；实习、个人项目、导师带教实践分别保留，不能自动当作正式工作年限。导师指导的本人实践正常作为能力证据。简历没写某技能是未知，不能断言不会；未知必备能力不推荐。

profile.experience含verified_work_months（已证实正式工作总月数）、relevant_work_months（其中与本次目标有关的月数）；均为非负有限数字，0须确实核对无该经历，后者不能大于前者。可另记internship_months，脚本不把它用于社招正式年限。

job.experience_requirement为 `{min_months, basis: formal_work/relevant_work, priority: mandatory/preferred/none/unknown}`。必须有“3年相关经验”就按相关月数查；不限经验用none+0，要求未知用unknown。优先项不足可保留差距，不冒充必须；明确必备年限不足则剔除。没有毕业窗口的社招不要求填毕业年份；当前JD确有限制仍检查。

JD明确允许实习/项目经验替代时，引用该条件，在requirements中核对可替代实践的真实时间与能力；不能额外添加JD没有的正式工作门槛。该岗没有独立正式年限硬限制时，结构化正式年限用none+0，实际实践要求仍须完整终审。未明确允许就不能擅自折算或把导师带教实践当作正式任职年限。

职级看职责、决策范围、独立负责程度和带人要求，不能仅凭“经理/高级”标题自动匹配，也不把所有公司职级等同。可记录target_seniority与到岗约束；要求离职、出差、轮班、证书、具体行业或管理经验时，纳入JD要求矩阵及终审，不能只核对总工作年限。

薪资保留原区间、币种、月薪/年薪、薪数、固定/浮动组成。profile.salary_constraint可设 `{min, period: month/year, currency: CNY等, hard: true/false}`；未指定底线不替本人编数字。job.salary_range为 `{min, max, period, currency}`，只对已确认同口径比较：整个区间低于硬底线→剔除；硬底线已设但薪资未知/口径不同→待核验；区间部分覆盖→可继续沟通，明确“部分区间符合，实际offer未确定”。面议且无硬底线不单凭薪资未知剔除，保留未知；不能将奖金/期权当保底现金或擅自换汇、换算薪数。

## 检查键与终审

共用checks：subject、role、degree、major、city、employment。

| 模式 | 追加checks键 | final_review.hard_conditions |
|---|---|---|
| campus | graduation | degree/major/city/employment + graduation |
| internship | student_status、schedule | degree/major/city/employment + student_status/schedule |
| experienced | experience、seniority、salary | degree/major/city/employment + experience/seniority/salary |

每项保留pass/fail/unknown、真实来源quote/source_url及理由。社招检查的是条件是否冲突，不等于薪资已谈妥或职级已经确认；JD没有该门槛且本人未设硬限制时，完整核对JD并说明“不构成当前限制，具体值未公布”，不编造“不限/面议”原句。学历/专业有明确要求必须按原件核对，来源不全不能把未提自动当不限。

所有模式都重读最新原简历×完整JD做独立终审；结构检查、来源hash和数值比较不代替语义判断。工作年限、出勤或薪资要求的标准化值必须与原文一致，不能为通过修改字段。

## BOSS与其他招聘平台

社招按用户流程优先BOSS；猎聘、智联、前程及企业官网按岗位覆盖补充，不强制所有岗位都走同一平台。实习/校招也可出现平台岗位，**求职模式与入口类型是两条独立轴**。

- 记录source_platform（如boss/liepin）、岗位ID、平台企业ID/招聘主体、招聘者标识、完整JD、城市及当前入口。link_type=recruiter_platform表示招聘平台具体岗位，不冒充企业官网或已获企业指定的平台。
- 在当前岗位主区域核对招聘主体与招聘者关系。招聘者活跃/在线只是排序信号，不能证明当前在招；公司名、JD标题相同也不能证明是同一岗位。多个招聘者/平台重复挂同一已证实岗位合并入口，不按不同链接凑数；仅相似职责不武断合并。
- 公开页面足够时直接读；必须登录但本轮未授权的操作不自行登录。已有明确授权的账号可按范围做只读检查，不能切换求职身份或编辑在线简历。飞书本人身份确认不等于招聘平台账号归属或沟通授权。
- 申请路径分application.route=form/chat。官网表单沿用实际打开/点击且不提交的规则；BOSS使用chat，不能套用官网申请表。优先观察同岗且启用的沟通控件及招聘者，不为证明入口而点击可能发送消息的按钮；状态为chat_available，entry_method=visible_control、control_enabled=true、recruiter_id非空。仍需context、实际text/checked_at/evidence_file，并真实看图。
- 岗位详情和上下文完整、入口指向保留该岗位的登录页时可记录login_required；这仅证明待登录入口，报告不能称已登录可发送。通用登录页、空壳、未识别岗位或招聘者不通过；受限/验证码/渲染失败为blocked，不绕过、不批量判停招。
- ready只代表本轮条件与指定范围入口核验通过。表内注明“待沟通/登录后继续”等实际边界，不承诺招聘方回复或最终投递资格。quality_gate.delivery_verified固定false，不能据ready自动填已沟通、已发简历或已提交。

## 沟通与投递状态

选岗只写“已选岗”（按现有表约定），其他状态必须来自本次明确授权动作或已读历史证据：

| 业务状态 | 最低证据 |
|---|---|
| 已发起沟通 | 同岗位/招聘者对话中真实发出消息的记录 |
| 已发送简历 | 实际发送的文件/在线简历事件及接收方记录；同意请求/按钮可见不够 |
| 招聘方回复 | 招聘方真实回信；区分系统提示、自动欢迎和实质反馈 |
| 官网已提交 | 当前申请成功页/编号或实际提交记录 |

沟通、发送、回复分别保留时间、岗位/招聘者、证据和实际结果，不互相推导。平台也许会在沟通时展示在线履历，这不证明附件已发送；以当前事件为准。不新建“已投递”伪记录，不覆盖原有人工状态。若用户另有明确代投/沟通授权，执行该范围并验收，不对同一授权重复提问；这次Skill扩展本身不发送任何消息/简历。

平台行为以当前实际界面为准，参考 [BOSS功能说明](https://www.zhipin.com/web/common/protocol/feature-intro.html)、[BOSS使用帮助](https://www.zhipin.com/web/common/protocol/use-help.html)。不实现未经核对的私有接口、群发脚本或绕过登录/验证码的抓取器。
