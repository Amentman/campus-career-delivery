# 环境基线

本仓库在以下本机环境完成打包与自动测试（历史环境记录；本轮团队版为2026-11-04，Asia/Shanghai）：

| 组件 | 验收版本 |
| --- | --- |
| Codex CLI | `0.155.0-alpha.9.2` |
| Python | `3.14.7` |
| Node.js | `22.23.2` |
| lark-cli | `1.0.72` |
| 操作系统 | macOS |

版本不是硬编码下限，但工具参数、飞书返回结构、插件清单和渲染结果可能随版本变化。迁移到其他环境时先运行仓库测试，再用脱敏样例完成一次不写入/测试空间演练。

## 必需能力

- Codex 能发现 `skills/` 中的 Skill，并支持 `.codex-plugin/plugin.json` 或根目录可移植 `plugin.json`。
- 岗位、面试和待办校验器主要使用 Python 标准库。简历 Word/PDF 检查及其测试需要 `python-docx`、`pdfplumber`、`lxml`、`pypdf` 和 `reportlab`；Skill Creator 格式验证需要 PyYAML。本仓库验收命令使用 `uv run --with pyyaml python <validator> ...` 临时提供依赖，不要求污染系统 Python。
- 飞书交付需要已登录的 `lark-cli`、目标文档权限和当前版本的 Wiki/Docs/Drive 使用指南。
- 真实面试复盘的逐字稿归一化与覆盖校验只需 Python3 标准库；腾讯分页读取器在已授权的后台浏览器执行，离线测试使用 Node.js 内置测试器，不安装 npm 包。腾讯读取需本人的网页登录和目标权限，不随包提供。
- Word、PDF和页面渲染能力由安装环境提供，本仓库不复制 OpenAI 自带系统 Skill。

## 路径与命令约定

- Skill 文档中的 `scripts/...` 都相对该 Skill 自己的目录解析；从仓库根目录执行时应使用 `python3 skills/<skill-name>/scripts/<script>.py ...`，不要依赖当前工作目录碰巧位于 Skill 内。
- `student-mock-interview-delivery/scripts/locate_student.py` 使用本次 --root 或成员配置 workspace.student_root；支持多个 --root。没有有效配置时明确提示，不猜制作者的学生目录。
- `prompts/` 是审计快照而不是直接覆盖模板，本轮已将私人路径、账号标识与生产节点移除。其他使用者应以根目录 `AGENTS.md` 为入口，并对用户级规则做人工合并。

## 提示词容量

`prompts/` 为当前脱敏副本，项目入口与全局规则合并后应检查实际运行器的上下文容量。安装时按需要合并，不自动覆盖已有规则。

## 内容生产与外部依赖

21 个 Skill 均可按需安装。小红书渲染器需要 Node.js、Playwright 及 Chrome；使用 `npm install playwright` 安装依赖，默认命令使用 macOS Chrome 路径；其他平台需自行适配并验证。其余 Word/PDF 渲染、设计 Skill、聊天连接器、知识库与 lark-cli 由使用者自行提供。本仓库不分发私人微信解析器、聊天数据库或密钥。

## 团队版配置工具

根目录 scripts/team_setup.py、sync_public.py、build_team_docs.py、build_manifest.py 仅依赖 Python 标准库，合并同步另需 Git。安装器不调用飞书；bind-user和doctor --live只读现有本人登录态。正式目标仍须按任务回读并验证访问能力。

图片技能在自己的目录执行 npm ci 安装已锁定依赖；不从作者插件缓存猜依赖。源码与安装包排除 node_modules、字节码、私有JSON和生成日志。完整测试命令见README；正式文档Python检查依赖通过uv临时环境提供，不修改系统Python。
