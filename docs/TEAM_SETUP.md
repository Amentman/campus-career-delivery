# 团队第一次接入

先由负责人确认团队学生目录、投递表模板、共享岗位库和内容/服务入口，再把必要路由作为私有JSON交给成员。成员导入后绑定自己的登录身份。公开仓库不保存实际节点、学生材料或凭据。

## 哪些内容需要一起交接

| 项目 | 配置位置 | 怎么使用 |
| --- | --- | --- |
| 学生既有飞书目录 | feishu.students_root_url，或旧 wiki 路由 | 在此定位学生正式姓名唯一页，优先复用原页面和原表 |
| 投递表结构参考 | feishu.template_url、format_reference | 只在确认学生没有投递表且建表属于当前授权时使用，只复制结构 |
| 共享岗位库 | shared_pool 的 base_token、job_table_id、company_table_id、owner_open_id | 先全量查库再按学生画像复核，不把入库记录当作当前可投 |
| 内容总表 | feishu.content_base_url | 按本次内容记录、真实字段与子表关系处理 |
| 服务主表、待办 | feishu.service_base_url、feishu.todo_url | 已有服务事实与人工状态优先，不建替代台账 |
| 本机学生资料、业务知识库、备份 | workspace.student_root、knowledge_root、output_root | 每位成员自己的路径，不继承负责人的机器目录 |
| 当前成员身份 | expected_user_open_id、expected_profile | 由 bind-user 读取成员自己的 lark-cli 登录态设置 |

可只配置本轮需要的资源。任务已经明确提供唯一目标时优先用该目标，不为缺少其他字段打断任务。

## 负责人准备一次

复制 config/team.example.json，在私有位置填写真实路由。共享池 owner 填资源实际所有者；expected_user_open_id 和 expected_profile 留空，不把自己身份当作团队共用登录。不要加入 access_token、Cookie、密码、API Key、聊天库、学生简历或真实客户素材。

向成员私下交接此JSON及他们需要的访问权限。这里的“交接”不意味着Agent可以自行发送消息、加协作者或扩大权限；这些动作按用户明确指定范围执行。

## 成员安装与登录

按仓库README运行 install、init、bind-user，再对正在使用的Skill运行 doctor。安装器只写成员指定的Skills目录；初始化只写本机私有配置；bind-user只读取登录态并绑定成员本人。都不会创建飞书表、修改权限或提交申请。

岗位脚本兼容旧 ~/.codex/campus-job-matching.local.json；显式指定 JIHUI_SKILLS_CONFIG 时以该文件为准，路径错误不得偷偷回退到另一个人的配置。共享池 owner 可以与成员 open_id 不同，仍须核对成员本人的实际访问能力。

## 遇到问题怎么处理

| 现象 | 下一步 |
| --- | --- |
| 未配置学生目录或本次目标不唯一 | 读取已给来源后，只补这一个目标；不在知识库根目录先建一份 |
| 共享库配置缺失 | 提供共享池路由；确实没有共享库的部署，由使用者明确设 shared_pool.enabled=false |
| 库有权限错误 | 核对当前成员、真实对象和已有权限；列出受阻，不换负责人凭据、不建替代库 |
| 同名Skill有本地改动 | 安装器停止并列冲突；保留改动，明确合并后再更新 |
| 只装旧 campus-recommend | 使用安装器自动带上 campus-job-matching；手动复制时同时复制主Skill |
| 文档、浏览器或图片工具缺失 | 补齐任务所需能力；先完成不依赖它的工作，不声称最终显示已验收 |

## 交付检查

目标应仍是原学生目录下的唯一页面或原表；新增岗位保留原默认视图和人工状态。实际回读正文、表格、图片、附件和父级。首次接入时选一个获授权的测试对象做端到端验证，再扩大范围；没有成员账号实测时，只能说明本机/安装测试结果。
