"""Build the small, self-contained team setup reference shipped in every skill."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESOURCE_NOTES = {
    'writing-readable-documents': '纯写作、聊天改写与本地审阅不要求飞书或团队库配置，也不需要Python、Node或外部API。读者、来源、参考与目标沿用当前请求；只有实际交付飞书时才读取目标和成员身份。学习私人参考只提炼组织与讲解方法，不公开原文、链接或素材。完整安装时保留 `third-party/` 中四份上游MIT许可证。复杂文档可配合同包 `visual-document-delivery` 与外部上游 `impeccable`；按当前运行器补齐所需能力，不依赖作者插件缓存或私人环境。Word、PDF与图解工具按交付格式配置；业务Skill继续负责必需内容、事实核验与权限检查。',
    'campus-job-matching': '需要团队学生目录 `feishu.students_root_url`（或兼容的 `wiki` 路由）、原投递表、`shared_pool` 的库与两张表ID。先查共享岗位库，再按缺口外搜；缺配置不能当作已查库或库内无岗。资源所有者用 `shared_pool.owner_open_id`，当前成员用 `expected_user_open_id`，两者可以不同。',
    'campus-recommend': '这是旧入口兼容别名，必须同时安装 `campus-job-matching`。完整安装器会补齐依赖；手动复制时复制这两个目录，实际工作流全部交给主Skill。',
    'job-content-publisher': '需要本次内容记录，或团队内容总表 `feishu.content_base_url`；读取真实字段、记录与子表关系。图片依赖 `xiaohongshu-image-renderer`，正式文档排版按实际可用能力选择。公开发布到平台仍按本次明确授权执行。',
    'job-sales-advisor': '业务知识库从 `workspace.knowledge_root` 或本次明确提供的入口读取。使用团队产品、价格、客户原话与案例；没有作者私人素材时不假装已经读取，也不把旧客户结论套给当前客户。',
    'multi-source-todo-control': '服务主表从 `feishu.service_base_url`、既有学生页或本轮指定入口读取。聊天来自成员获授权的连接器或导出；不可访问的渠道明确列覆盖缺口，不把旧快照说成已刷新。',
    'personal-todo-control': '服务主表与待办入口分别用 `feishu.service_base_url`、`feishu.todo_url` 或本轮明确目标。聊天、日历、合同等只使用成员获授权的来源。运行时间和通知偏好由当前用户明确约定，不继承作者的定时任务。',
    'xiaohongshu-image-renderer': '需要已确认的母稿、Node.js、Playwright 和可用Chrome/Chromium。按本目录依赖说明安装；浏览器通过显式参数或本机发现获得，不依赖作者的Codex插件缓存。输出路径使用本轮指定目录或 `workspace.output_root`。',
    'tencent-meeting-cloud-export': '使用成员自己的腾讯会议网页版登录态及获授权的下载范围。浏览器必须具备所需能力；当前旧脚本会激活标签页，未获前台操作授权时不得运行它。媒体与状态留在成员本机，不分发账号、录制链接或密码。',
    'jihui-interview': '优先复用 `workspace.knowledge_root` 或用户指定的现有知识库。只有当前用户授权建库时才创建所需目录；已有目录保留结构和历史，不覆盖别人的资料。',
    'pengyouquan-copywriting': '取材入口为 `workspace.knowledge_root` 或本轮提供的真实素材。风格文件是教学参考，不是当前使用者的个人经历、产品承诺、客户案例或可直接复用的数据。',
    'recording-processing': '本轮逐字稿是必需来源；知识库入口为 `workspace.knowledge_root`，导出用 `workspace.output_root` 或当前明确目录。整理、入库与对外发送分别按已给范围执行。属于真实面试复盘时转专用Skill。',
    'auditing-candidate-resumes': '简历、JD与招聘方评价标准由本轮提供。聊天内审查不要求飞书配置；只有用户要正式存档时才读取明确的目标文档与权限，不默认发布候选人的个人资料。',
    'building-resume-interview-stories': '以当前简历、JD或项目证据为输入。正式学生交付优先既有学生入口；聊天内的有界表达任务不因为缺飞书配置而停工。',
    'student-job-content': '需要当前选题、真实来源与已授权素材。采用团队自己的案例和产品资料；写作授权不等于发布到小红书、朋友圈或写入内容表。',
}


def reference(name):
    note = RESOURCE_NOTES.get(name, '正式学生材料优先本轮已给的唯一入口；未给时，从 `feishu.students_root_url` 或兼容 `wiki` 路由定位该学生。`workspace.student_root` 用于本机材料搜索，`workspace.output_root` 用于备份。先读现有页、父级和权限，避免建立重复页面。')
    content = f'''# {name}｜团队配置

## 第一次使用

整个Skill目录一起安装，保留 `references/`、`scripts/`、`assets/`、`agents/` 和随包测试，不只复制 `SKILL.md`。本目录内容是工作方法；团队实际资源位置在各成员本机私有配置中。

配置查找顺序：环境变量 `JIHUI_SKILLS_CONFIG` 指定的JSON；未设置时使用 `~/.config/jihui-skills/team.json`。岗位Skill兼容既有 `~/.codex/campus-job-matching.local.json`。当前任务明确给出的来源、目标和限制优先于配置。

{note}

## 私有配置结构

```json
{{
  "version": 1,
  "expected_user_open_id": "",
  "expected_profile": "",
  "workspace": {{"student_root": "", "knowledge_root": "", "output_root": ""}},
  "feishu": {{"students_root_url": "", "template_url": "", "content_base_url": "", "service_base_url": "", "todo_url": ""}},
  "shared_pool": {{"enabled": true, "base_token": "", "job_table_id": "", "company_table_id": "", "owner_open_id": ""}}
}}
```

只填写当前任务需要的字段；单纯聊天、读取用户给定材料或生成本地稿，不要求配置无关系统。已有 `wiki` 和 `format_reference` 路由继续保留，不改学生目录或投递表。没有共享岗位库的部署应由使用者明确设 `shared_pool.enabled=false`；不能把配置缺失当作跳过已约定岗位库的理由。

团队负责人私下提供资源路由；成员在本机用自己的 `lark-cli` 登录，静默核对并绑定本人的 `expected_user_open_id`。共享库所有者与操作者是两个对象；有权限的成员可以访问团队负责人名下的库，不需要把资源转给成员。配置文件不携带密码、Cookie、访问令牌、聊天库或学生材料，也不会自动赋予权限。

## 安装器与诊断

完整项目库为 `Amentman/campus-career-delivery`。在仓库根目录可运行：

```bash
python3 scripts/team_setup.py install --dest "<运行器扫描的Skills目录>" --skill {name}
# 检查预览后，在已授权的安装范围内加 --apply 执行
python3 scripts/team_setup.py init --team-profile "<私下提供的团队入口.json>"
python3 scripts/team_setup.py bind-user
python3 scripts/team_setup.py doctor --skill {name} --live
```

手动复制单个Skill时，也可直接按上面的JSON在成员本机创建私有配置；不要求仓库根工具存在于Skill目录。需要其他Skill或外部工具时，按本Skill的相关说明补齐对应能力。`doctor` 只核对配置、工具和登录态，不证明目标有权限、岗位在招、正文已写入或显示正确。

## 每次任务

先读任务必需的当前来源、已有交付入口和本次授权。已配置的入口自行核对，不反复索取；必需来源/目标不唯一时只处理该缺口。目录、库或权限异常时保存具体失败范围，不把它当作“对象不存在”，也不擅自在根目录建替代页面、表或视图。

任务完成后按实际交付面回读内容、数量、附件、父级和可读性。配置成功、CLI成功和本地测试通过不替代业务验收；没有测试成员账号时不声称已验证该成员访问。
'''

    if name == 'student-interview-review-delivery':
        content = content.replace('## 每次任务\n\n', '## 每次任务\n\n逐字稿入口需要 Python3；飞书需本人 `lark-cli`，腾讯在线读取需可执行 JavaScript 的已登录后台浏览器。Node.js 只用于本包腾讯读取器的离线测试，不是获取腾讯登录的工具。没有后台能力时使用已授权原生导出或本地原稿，不安装依赖、不抢占前台。完整 Skill 必须包含 `scripts/transcript.py`、`scripts/read_tencent.js` 和输入指南。\n\n')

    if name == 'student-role-interview-prep':
        content = content.replace('"expected_profile": "",', '"expected_profile": "",\n  "role_prep_delivery": {"authorization_confirmed": false, "link_share_entity": "preserve"},')
        content = content.replace('## 安装器与诊断', '## 专岗交付分享偏好\n\n`role_prep_delivery` 默认缺省或 `preserve`，不改变分享范围。当前使用者明确要求本人后续学生专岗交付页均为“获得链接的所有人可查看”后，在其私有配置中设 `authorization_confirmed=true`、`link_share_entity=anyone_readable`；按写入边界逐页执行和回读。配置只保存本人已确认偏好，不授予API权限，不适用于老师内部页、学生主页或其他服务记录，也不能复制作者的确认值给其他成员。当前任务限定更窄时采用当前限定。\n\n## 安装器与诊断')
    return content



def build():
    for directory in sorted((ROOT / 'skills').iterdir()):
        if not (directory / 'SKILL.md').is_file():
            continue
        target = directory / 'references/team-setup.md'
        target.parent.mkdir(exist_ok=True)
        target.write_text(reference(directory.name), encoding='utf-8')


if __name__ == '__main__':
    build()
