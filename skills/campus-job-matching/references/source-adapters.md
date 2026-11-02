# 来源适配与增量规则

## 借鉴边界

借鉴 [career-agent架构](https://github.com/mengxi111/career-agent/blob/main/docs/architecture.md) 和 [届别证据分流](https://github.com/mengxi111/career-agent/blob/main/job_cohorts.py)：平台采集分开、字段统一、未知届别分流、匹配增量复用、单源失败隔离。这里独立实现本地质检；不安装其整套系统、不接DeepSeek、不传学生画像、不启用GitHub Actions、公开发布或飞书机器人。

参考 [Ricsign失效页面测试](https://github.com/ricsign/Ricsign-New-Grads-Jobs-2027/blob/main/tests/test_verify.py) 区分200但停招和访问失败；不能直接照搬其HTTP规则，国内JS/反抓取页面的404也需实际确认。

## 采集适配

优先当前可用的公开API/CLI，必须渲染时用匿名后台浏览器；无可用后台能力则blocked，不抢前台，不绕过验证码/登录墙。

| 来源 | 提取重点 | 常见误判 |
|---|---|---|
| 北森/Zhiye | 企业/租户、ID、职责/要求、类别/用工、地点、截止原值、状态 | Status=1不能单独证可投；校招不等于任意毕业月份可投；0001为空截止 |
| Moka | 企业/租户、ID、open、hireMode/commitment、项目归属/毕业窗口、地点 | 校招项目可能混实习；不能把门户活动套到所有岗 |
| 飞书招聘 | 企业租户、job_post ID、职能、recruit_type/项目、城市/学历、在线状态 | 在线不证明学历/专业符合；列表不能代替详情与申请路径 |
| 企业独立站 | 官方ID/稳定URL、职责要求、工作地、校招政策、申请流程 | URL形状/title/版权年/首页活动不是逐岗资格证据 |
| 企业指定平台 | 官方指定关系、企业主体、ID、详情与申请 | 平台页不自动是官网；更新标签不等于首次发布 |
| BOSS/其他招聘平台 | source_platform、企业/岗位/招聘者ID、完整JD、当前沟通或表单入口 | 活跃不等于在招；沟通控件可见不等于已联系/发简历；不点击可能发送的按钮来测试 |
| 搜索/就业网/聚合 | 来源链接、时间、发现线索 | 转载不单独证明当前在招、官方窗口或学生可投 |

这是字段语义，不是永久API规格；按当前真实返回映射。保留原始响应与时间，不猜ID/URL，不把company_hint当成核验后的企业主体。

标准化保留企业、可靠别名key、tenant、官方/平台岗位ID或稳定URL、title、完整JD、实际城市、用工、项目关联、学历/专业、本模式条件原文、deadline原文/标准值、published_at、updated_at、fetched_at。平台企业ID/岗位ID不能编造或只按公司名相似合并。随后独立产生分模式checks及availability/application观察，不能由active标志直接生成ready。社招与平台路径读 [模式与平台](search-modes.md)，结构见 [数据契约](quality-contract.md)。

## 缓存与覆盖

- 初筛匹配缓存键含JD、学生画像、规则版本，任一变化重做；每轮最终名单仍须独立终审，原件/提取正文变化也必须重审。原始简历与学生信息留本地，不发第三方。
- first_seen、last_seen、last_verified、企业发布/更新分别存；缓存命中不刷新checked_at。交付前重查岗位与实际表单/沟通入口，临近截止再查。
- 单源失败保留错误和未覆盖数量，不能整家公司判下架；有限串行退避，只重试未完成请求，不加并发打频控。
- “更多”继续同一画像、历史职位键、累计公司数与覆盖进度，不能重新计数凑量。
- 可用JSON/CSV+证据目录，不强制数据库、MCP或爬虫框架。平台适配由Agent使用现有能力完成；离线质检器不是自动全站爬虫。
- 新平台先查正常详情、明确下架、访问受阻、错误申请跳转；核对主体、详情主区域、分页与上下文后再扩大采集。
