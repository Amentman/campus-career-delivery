# campus-recommend｜团队配置

## 第一次使用

整个Skill目录一起安装，保留 `references/`、`scripts/`、`assets/`、`agents/` 和随包测试，不只复制 `SKILL.md`。本目录内容是工作方法；团队实际资源位置在各成员本机私有配置中。

配置查找顺序：环境变量 `JIHUI_SKILLS_CONFIG` 指定的JSON；未设置时使用 `~/.config/jihui-skills/team.json`。岗位Skill兼容既有 `~/.codex/campus-job-matching.local.json`。当前任务明确给出的来源、目标和限制优先于配置。

这是旧入口兼容别名，必须同时安装 `campus-job-matching`。完整安装器会补齐依赖；手动复制时复制这两个目录，实际工作流全部交给主Skill。

## 私有配置结构

```json
{
  "version": 1,
  "expected_user_open_id": "",
  "expected_profile": "",
  "workspace": {"student_root": "", "knowledge_root": "", "output_root": ""},
  "feishu": {"students_root_url": "", "template_url": "", "content_base_url": "", "service_base_url": "", "todo_url": ""},
  "shared_pool": {"enabled": true, "base_token": "", "job_table_id": "", "company_table_id": "", "owner_open_id": ""}
}
```

只填写当前任务需要的字段；单纯聊天、读取用户给定材料或生成本地稿，不要求配置无关系统。已有 `wiki` 和 `format_reference` 路由继续保留，不改学生目录或投递表。没有共享岗位库的部署应由使用者明确设 `shared_pool.enabled=false`；不能把配置缺失当作跳过已约定岗位库的理由。

团队负责人私下提供资源路由；成员在本机用自己的 `lark-cli` 登录，静默核对并绑定本人的 `expected_user_open_id`。共享库所有者与操作者是两个对象；有权限的成员可以访问团队负责人名下的库，不需要把资源转给成员。配置文件不携带密码、Cookie、访问令牌、聊天库或学生材料，也不会自动赋予权限。

## 安装器与诊断

完整项目库为 `Amentman/campus-career-delivery`。在仓库根目录可运行：

```bash
python3 scripts/team_setup.py install --dest "<运行器扫描的Skills目录>" --skill campus-recommend
# 检查预览后，在已授权的安装范围内加 --apply 执行
python3 scripts/team_setup.py init --team-profile "<私下提供的团队入口.json>"
python3 scripts/team_setup.py bind-user
python3 scripts/team_setup.py doctor --skill campus-recommend --live
```

手动复制单个Skill时，也可直接按上面的JSON在成员本机创建私有配置；不要求仓库根工具存在于Skill目录。需要其他Skill或外部工具时，按本Skill的相关说明补齐对应能力。`doctor` 只核对配置、工具和登录态，不证明目标有权限、岗位在招、正文已写入或显示正确。

## 每次任务

先读任务必需的当前来源、已有交付入口和本次授权。已配置的入口自行核对，不反复索取；必需来源/目标不唯一时只处理该缺口。目录、库或权限异常时保存具体失败范围，不把它当作“对象不存在”，也不擅自在根目录建替代页面、表或视图。

任务完成后按实际交付面回读内容、数量、附件、父级和可读性。配置成功、CLI成功和本地测试通过不替代业务验收；没有测试成员账号时不声称已验证该成员访问。
