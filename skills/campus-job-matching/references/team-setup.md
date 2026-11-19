# campus-job-matching｜团队配置

## 第一次使用

整个Skill目录一起安装，保留 `references/`、`scripts/`、`assets/`、`agents/` 和随包测试，不只复制 `SKILL.md`。本目录内容是工作方法；团队实际资源位置在各成员本机私有配置中。

配置查找顺序：环境变量 `JIHUI_SKILLS_CONFIG` 指定的JSON；未设置时使用 `~/.config/jihui-skills/team.json`。岗位Skill兼容既有 `~/.codex/campus-job-matching.local.json`。当前任务明确给出的来源、目标和限制优先用于定位；实际写入仍须核实交付根归属。

需要团队学生目录 `feishu.students_root_url`（或兼容的 `wiki` 路由）、原投递表、`shared_pool` 的库与两张表ID。先查共享岗位库，再按缺口外搜；缺配置不能当作已查库或库内无岗。资源所有者用 `shared_pool.owner_open_id`，当前成员用 `expected_user_open_id`，两者可以不同。

实际写入飞书前，配置并核实 `feishu.delivery_root_url` 指向当前使用者确认的交付根。沿真实父级链核对既有目标或新建父级，快捷方式追到原对象，表、记录与附件追到宿主；根缺失、目录外或归属未证实则只暂停该写入，不建替代对象。聊天、只读与本地文件任务不因缺少此字段停止。

学生可见的正式成品按当前使用者已确认的分享偏好执行。私有配置 `student_delivery.authorization_confirmed=true` 且 `link_share_entity=anyone_readable` 时，仅对交付根内供学生阅读的成品设为“获得链接的所有人可查看”，不授予编辑权限；写前保存权限快照，写后独立回读 `external_access=true`、`link_share_entity=anyone_readable`，并核对正文内画板与附件的访问范围。老师内部稿、私人备注和来源材料保留原权限。当前任务更窄的限制优先；其他成员须自行确认，不继承作者授权。

## 私有配置结构

```json
{
  "version": 1,
  "expected_user_open_id": "",
  "expected_profile": "",
  "student_delivery": {"authorization_confirmed": false, "link_share_entity": "preserve"},
  "workspace": {"student_root": "", "knowledge_root": "", "output_root": ""},
  "feishu": {"delivery_root_url": "", "students_root_url": "", "template_url": "", "content_base_url": "", "service_base_url": "", "todo_url": ""},
  "shared_pool": {"enabled": true, "base_token": "", "job_table_id": "", "company_table_id": "", "owner_open_id": ""}
}
```

只填写当前任务需要的字段；单纯聊天、读取用户给定材料或生成本地稿，不要求配置无关系统。已有 `wiki` 和 `format_reference` 路由继续保留，不改学生目录或投递表。没有共享岗位库的部署应由使用者明确设 `shared_pool.enabled=false`；不能把配置缺失当作跳过已约定岗位库的理由。

团队负责人私下提供资源路由；成员在本机用自己的 `lark-cli` 登录，静默核对并绑定本人的 `expected_user_open_id`。共享库所有者与操作者是两个对象；有权限的成员可以访问团队负责人名下的库，不需要把资源转给成员。配置文件不携带密码、Cookie、访问令牌、聊天库或学生材料，也不会自动赋予权限。

## 安装器与诊断

完整项目库为 `Amentman/campus-career-delivery`。在仓库根目录可运行：

```bash
python3 scripts/team_setup.py install --dest "<运行器扫描的Skills目录>" --skill campus-job-matching
# 检查预览后，在已授权的安装范围内加 --apply 执行
python3 scripts/team_setup.py init --team-profile "<私下提供的团队入口.json>"
python3 scripts/team_setup.py bind-user
python3 scripts/team_setup.py doctor --skill campus-job-matching --live
```

手动复制单个Skill时，也可直接按上面的JSON在成员本机创建私有配置；不要求仓库根工具存在于Skill目录。需要其他Skill或外部工具时，按本Skill的相关说明补齐对应能力。`doctor` 只核对配置、工具和登录态，不证明目标有权限、岗位在招、正文已写入或显示正确。

## 每次任务

先读任务必需的当前来源、已有交付入口和本次授权。已配置的入口自行核对，不反复索取；必需来源/目标不唯一时只处理该缺口。目录、库或权限异常时保存具体失败范围，不把它当作“对象不存在”，也不擅自在根目录建替代页面、表或视图。

任务完成后按实际交付面回读内容、数量、附件、父级和可读性。配置成功、CLI成功和本地测试通过不替代业务验收；没有测试成员账号时不声称已验证该成员访问。
