# 统一质检数据契约

`scripts/validate_jobs.py` 仅用Python标准库，离线消费采集证据并导出判定/合格子集。它不访问网页、不鉴定事实真假、不AI评分、不写飞书；通过不免除逐岗事实与看图检查。

## 输入

画像共同字段：student_id、search_mode（campus/internship/experienced）、target_roles数组、cities接受城市数组、employment_types数组（full_time/internship），可含excluded_companies/excluded_industries。degree/major及其他限制按真实原件保留；campus、internship要求学历专业已知，campus另需graduation_date（YYYY-MM或YYYY-MM-DD）。internship需student_status及internship_availability；experienced需experience，无毕业限制时不要求毕业年月。模式具体字段/数值口径见 [模式与平台](search-modes.md)。新任务显式模式；旧输入缺模式仅兼容为campus，非法模式不产生ready。

另必需resume_file（当前确认原简历）、resume_text_file（完整UTF-8提取正文），均为本地绝对路径且非空。原件本身为纯文本时可同一路径。关键项缺失/Open或来源不可读不产生ready；仍可继续搜集线索。

历史数组：每条至少company与tenant+job_id，或company+稳定url；可含证实的company_key和record_id。把CLI fields/data/record_id_list先标准化，不传原始envelope。首次新表传 `[]`；追加/更多传全量历史，不只取当前视图。 全量原始行与人工状态完整留在快照；语义去重后的existing输入按每组保留1条生成，审阅记录须覆盖所有原始record_id与代表条目的对应关系，不漏读、不清空未知历史。缺完整JD或主体关系证据的历史不能擅自合并；先补证，受影响主体的新增保留待核验，其他主体可继续。

候选为推荐顺序的对象数组：

| 字段 | 含义 |
|---|---|
| student_id | 与画像一致 |
| company / company_key | 原企业名；别名key只在对应有证据时填写 |
| tenant / job_id / title | 官方租户、ID、标题；无官方ID不编造，使用稳定URL作上下文 |
| url / link_type | 可定位当前岗位的http(s)链接；detail / official_list / employer_platform / recruiter_platform |
| source_platform | 招聘平台标识如boss；recruiter_platform必须填写，主体关系仍须核验 |
| jd_text / cities / employment_type | 完整官方JD、实际城市数组、规范化用工 |
| match_evidence / gaps | 学生事实支持的匹配理由、实际差距或待复习项 |
| deadline | 官方YYYY-MM-DD、带时区ISO时间或null；另保留截止原文及来源，未知不猜 |
| checks | 共用六项加本模式检查，见下文 |
| availability / application | 两次实际观察，见下文 |
| final_review | 写入前最新简历×完整JD独立终审，必需结构见 [独立终审](final-review.md) |
| record_id | 存量复核保留，便于定位 |

checks共同键：subject、role、degree、major、city、employment。campus加graduation；internship加student_status/schedule；experienced加experience/seniority/salary。每项为 `{status, quote, source_url, reason?}`，status为pass/fail/unknown。pass必须有当前企业/平台原文和http(s)来源，不收只有布尔值的标记。适用的毕业证据明确覆盖本人实际年月；项目范围或海外口径未知则unknown。专业“优先”与“必须”分开，未提不能自动判不限。额外结构化字段experience_requirement、internship_requirement、salary_constraint/salary_range见模式契约，数值冲突可独立拦截假pass。

能提取官方数值毕业窗口时增加 `graduation_window: {start: "YYYY-MM或YYYY-MM-DD", end: "同格式"}`，程序会独立检查与学生年月是否兼容。窗口从月份中途开始/结束而学生只知月份时保留pending，不猜具体日。独立站确无租户/ID时可省略，稳定URL提供唯一键与上下文；已知tenant/ID则必须保留，不能为躲避去重清空。

## 观察结构

availability和application均含：

- status：前者active/closed/unknown/blocked/error；后者按route：form用form/login_required/consent_required，chat用chat_available/login_required；均可closed/unknown/blocked/error。contacted/resume_sent/replied/submitted不是入口状态，不通过。
- context：官方job_id；确无ID时为该条稳定url原值。不是其他岗位、相关推荐或通用登录页。
- text：当前岗位主区域/申请上下文实际读到的内容，不拿全站正文替代。
- checked_at：实际访问的带时区ISO时间；不复制示例日期、不用发布日期代填。
- evidence_file：本地可读取非空证据文件的绝对路径。API原文可作来源证据；JS页与表单/沟通入口还需真实截图并看图。脚本只查文件存在，不能证明内容正确。

availability另含scope=job_detail/job_listing；可保留http_status/source_url/final_url。单次401/403/405/429是受阻而非岗位下架。application补充实际点击、按钮、最终URL、原/新标签页与上下文来源；仅url_changed=true不通过。不为形成证据登录、发验证码、勾协议、上传或提交。

application.route为form/chat；旧官网输入缺route兼容form，BOSS必须显式chat。表单必须有 `clicked: true` 的实际按钮点击记录；直接打开有依据的申请URL时改为 `entry_method: "direct_url", opened: true, final_url: "实际地址"`。沟通控件可用的chat采用 `status: chat_available, entry_method: visible_control, control_enabled: true, recruiter_id: "当前招聘者标识"`，不需要也不得为核验而发消息。所有chat入口（包括login_required）都要识别当前岗位招聘者，登录回跳不能代替该证据。所有方式都仍需当前岗位context、状态、观察文本、时间与证据文件；控件可见不证明已发送/对方会回复。

## 输出与使用

报告含summary四类数量和每条index/record_id、公司、岗位、唯一键、status、reasons、final_review_summary，以及company_over_limit。add模式该项报告已超额历史公司；audit模式按整个存量集合计数，未知/受阻岗位也不悄悄从存量公司计数中消失。ready文件仅含通过对象，附selected_cities与quality_gate（时间、画像/岗位指纹、search_mode、application_route、delivery_verified=false、conditions_entry_inspection_and_resume_jd_review范围）。

只从ready映射写入，先确认指纹仍对应当前输入与新鲜证据；输入变化重跑。城市写selected_cities，不能把未接受城市混入。quality_gate是本地检查记录，不是招聘平台签发的资格凭证。

CLI的--mode add/audit控制新增或存量复核，与profile.search_mode求职模式独立。公司限额按下节执行。add按历史和本轮累计去重及计数；历史超额保留不动，只阻止向已超额的同一计数主体继续新增。audit给当前存量集合生成质检建议，不因“已在历史”把每条判重复；公司超额在company_over_limit汇总，并给对应结果附company_count_issue（count与limit），不擅自删除旧行。

audit模式的ready子集仅是存量复核结果，不是新增payload，不能再次追加到原表。修正存量按record_id和授权列局部处理。

退出0=全部ready，1=仅可使用ready子集并报告缺口，2=先修输入。实际交付省略--now，它只用于回归测试，不能拿历史时间绕过截止/时效。

官方来源真实性、公司/平台关系、JD职能、专业硬限制、毕业窗口适用范围、学生证据和截图可读性仍需Agent核验；不确定时pending/blocked，不手改pass凑量。

## 岗位语义去重优先于公司限额

对同一学生的全量历史和本轮候选统一比较。同一公司或同一实际招聘主体（含已核实的地区分支、别名和事业部）的同一岗位、实质相同职责模板，无论工作城市、招聘机构名称、编号、入口或批次不同，都只保留、计数1条；央国企及银行均适用。公司数量限制的放宽或豁免不能放宽岗位去重，也不从一个学生任务推广到其他学生。

用完整JD比较实际工作对象、核心动作、产出与责任层级。只有职责、工作内容或职级存在实质差异，并能逐项引用完整JD证明时，才可分别计数；城市、编号、标题后缀、事业部名称或措辞调整本身不构成差异。名称/职责相似但实际招聘主体不同，不能无证据合并；主体关系或JD不足时保留待核验，不计新增合格数。标题正则、文本相似度与不同ID都只能辅助发现疑似项，不能代替语义判断。

每组保留一条符合硬条件、最适合本轮城市优先级和学生经历的代表岗位；本轮北京优先时优先北京且更匹配的一条。其他接受城市可作为同条备注备选，不占新增条数。保存本地审阅记录：组内历史record_id/候选稳定键、已核实主体关系、完整JD来源与职责引文、相同/实质不同的理由、保留条目及备选城市。历史行与人工状态保留，审计时报告重复及去重后数量，不擅自删除或把历史重复当新增。

`validate_jobs.py`只按tenant+job_id或稳定URL识别重复，`company_key`只用于公司限额，`enforce_company_cap.py`也不识别职责模板。先完成语义去重，分别将历史与本批候选的每组代表条目送入existing/jobs离线检查，累计去重后的岗位数；候选命中已有历史组时不再新增。其余条目在审阅记录中列为重复/备选，待核验项不送入ready。不能改造原始ID/URL伪造同键，不能把银行分地区company_key当成不同岗位证明；脚本通过不能宣称自动完成语义去重。

## 公司限额与银行分地区计数

岗位语义去重完成后，一般企业默认累计3岗。私企大厂即使分布在不同城市、事业部或招聘批次，也归到同一经核实的公司键；不能换名称绕限额。用户本次明确另定公司数量或豁免时，仅适用于该生该任务，岗位去重仍执行。

央国企银行的不同地区独立招聘机构仅可分别计算公司限额。先用官方来源确认银行性质、岗位所属招聘机构与工作地区，再把历史和本轮候选的 `company_key` 标准化为“银行规范名::官方招聘机构::地区”。同一机构同一地区仍按默认3岗累计，全行跨地区不再累计为3岗。这个计数键不改变岗位语义去重：跨机构、地区、不同编号但职责模板实质相同的仍只算1岗；同一编号多城市也只算1岗。

例如：某国有银行深圳与广州分行分别发布“客户经理”，编号不同但完整JD的工作职责实质相同，只保留、计数1岗。若广州另有完整JD证明为独立的风险模型研发岗，可单独筛选，再使用“示例银行::广州分行::广州”计算公司限额。若是私人互联网公司，深圳已有3个不同岗位后，广州新增不同岗仍归该公司累计，默认不再新增。

`validate_jobs.py` 已按显式 `company_key` 计数；使用预裁剪脚本时，把相同计数键写入指定列，并传 `--company-key <计数键列>`。两处使用相同的 `--max-per-company N`（默认3），不要为了单家银行例外把所有公司上限统一放大。银行性质或历史招聘机构不明时先补证，不把未知历史当作0；无法补齐的计数保留待核验。

选岗备选数与企业实际可申请数分开。即使表内有多个地区岗位，也须注明全行/同机构志愿上限、是否平行志愿及已知截止；不把备选清单表述成每岗都可同时申请。
