# 首次运行与成员配置

离线 `validate_jobs.py`、公司限额检查及合成测试仅用 Python 标准库，不读取飞书配置。公开岗位采集需要当前环境的网页读取／后台浏览器能力；脚本不是自动联网爬虫。

实时共享池与飞书写入需要本人已登录的 `lark-cli`。先用 `lark-cli auth status --verify --json` 核对当前成员身份；不要把 token 粘到命令、公开配置或聊天中。账号显示名不同本身不说明身份错误，按已绑定的 open_id 与 profile 核对。

## 配置位置

`shared_pool.py` 按以下顺序只选择一个文件：

1. 非空 `JIHUI_SKILLS_CONFIG` 指向的 JSON 文件；
2. `~/.config/jihui-skills/team.json`（存在时）；
3. 旧 `~/.codex/campus-job-matching.local.json`（仅在新路径不存在时兼容）。

指定文件缺失、不可读或格式错误时立即说明配置缺口，不偷偷回退到另一个账号。没有配置不会创建文件或查询飞书。安装包附带的团队样例应复制到成员私有配置区，再填写真实读取所得的身份与入口；不要提交填写后的文件。

下面只是字段形状；大写占位符必须换成当前成员与团队实际核对的值：

```json
{
  "version": 1,
  "expected_user_open_id": "CURRENT_MEMBER_OPEN_ID",
  "expected_profile": "CURRENT_MEMBER_PROFILE",
  "workspace": {
    "student_root": "MEMBER_STUDENT_ROOT",
    "knowledge_root": "MEMBER_KNOWLEDGE_ROOT",
    "output_root": "MEMBER_OUTPUT_ROOT"
  },
  "feishu": {
    "students_root_url": "MEMBER_STUDENT_ROOT_URL",
    "template_url": "CONFIRMED_TEMPLATE_URL"
  },
  "shared_pool": {
    "url": "CONFIRMED_SHARED_POOL_URL",
    "base_token": "SHARED_BASE_TOKEN",
    "job_table_id": "SHARED_JOB_TABLE_ID",
    "company_table_id": "SHARED_COMPANY_TABLE_ID",
    "wiki_node_token": "SHARED_WIKI_NODE",
    "owner_open_id": "CONFIRMED_SHARED_POOL_OWNER"
  }
}
```

团队统一配置可以另外包含 `feishu.content_base_url/service_base_url/todo_url`，以及兼容的 `wiki`、`format_reference`。不要把这些入口自动当作本次学生的目标；实际写入前仍读取唯一学生父链、原表、字段、权限与修订号。

## 成员登录与共享池所有者分别核对

`expected_user_open_id`、`expected_profile` 绑定当前成员本人；`shared_pool.owner_open_id` 绑定实际共享池所有者，可以属于另一位已确认的团队成员。先核对本人登录和池节点的 owner／Base，再完整读取岗位表和公司表，读取成功才证明当前成员具有访问能力。所有后续飞书命令使用 `--as user`，不切为机器人或共享账号。

无 `version` 的旧配置只为兼容已有运行：未填写池 owner 时沿用旧的“本人拥有个人池”口径。团队共享池应迁移到 `version: 1` 并显式填 owner，不能为绕过所有者核验删字段。

共享池还需符合现有字段约定：公司表含“公司名称”；岗位表使用本 Skill 的公共岗位字段。先读取实际字段和选项；不一致时先做映射或修正配置，不自动改团队业务表结构。Owner 正确不证明表字段、记录访问或写权限已经通过。

## 缺少配置或权限时

缺文件、`shared_pool` 字段缺失、登录／profile 不符、owner 不符和读表失败分别保留异常。实时脚本返回非零状态及 `pool_checked: false`，不输出伪造的空池快照。先补配置；只有当前任务已明确允许不使用共享池，才能继续公开外搜，并报告本轮未覆盖池内记录。不要把该异常写成“池内无符合岗位”。

可在任意工作目录检查帮助：

```bash
python3 "<本Skill目录>/scripts/shared_pool.py" --help
python3 "<本Skill目录>/scripts/validate_jobs.py" --help
python3 -m unittest discover -s "<本Skill目录>/tests" -v
```

`snapshot` 读取实际飞书；`append` 默认 dry-run 仍会读取本人身份与实时池，`--execute` 才新增记录。`search/plan` 是离线快照操作。只做安装验收时运行帮助与合成测试，不运行真实读写命令。
