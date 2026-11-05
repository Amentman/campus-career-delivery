# 校招交付

寂辉团队共用的求职服务 Skills：选岗、职业规划、简历、作品集、面试、学生跟进、销售与内容生产。公开仓库保存工作方法、引用、脚本和测试；团队目录、岗位库、资料入口及成员身份放在私有配置中。

先按下面三步安装和配置，再从 [完整目录](docs/SKILL_CATALOG.md) 选择任务。每个 Skill 目录自带团队接入说明；需要其他 Skill 的入口，安装器会补齐已声明的必需依赖。

## 先看业务 Skill 怎么运转

[完整流程图目录](docs/SKILL_WORKFLOWS.md)覆盖本项目全部业务 Skill。每项包含输入、操作对象、判断分支、失败去向、交付与验收。

选岗先看[总览与完整流程](skills/campus-job-matching/references/workflow.md)：先查共享岗位库，按缺口外搜；合格岗位在学生原表末尾去重追加，新发现岗位的公共事实再去重回收同一库。

## 团队成员第一次使用

### 1. 安装完整目录

```bash
git clone https://github.com/Amentman/campus-career-delivery.git
cd campus-career-delivery
python3 scripts/team_setup.py install --dest ~/.codex/skills
# 上条只预览；确认目标是自己的 Skills 目录后执行
python3 scripts/team_setup.py install --dest ~/.codex/skills --apply
```

其他 Agent 使用它实际扫描的 Skills 目录替换 `--dest`。只装选岗可加 `--skill campus-job-matching`；只装旧别名时安装器会同时安装主技能。不只复制 `SKILL.md`，还要带上该目录的引用、脚本、模板和测试。

已有同名目录时，安装器比较文件内容和上次安装记录。未托管的不同版本或成员自己改过的文件会列为冲突，整次安装不写入；不会为升级覆盖个人改动。升级使用 `git pull --ff-only` 后运行相同命令并加 `--update --apply`。

### 2. 导入团队入口，绑定自己的账号

负责人私下提供团队入口 JSON。成员不需要拿负责人的登录凭据：

```bash
python3 scripts/team_setup.py init --team-profile "<团队入口.json>"   --student-root "<本机学生资料目录>"   --knowledge-root "<本机业务知识库目录>"   --output-root "<本机交付备份目录>"
# 使用成员自己已经登录的 lark-cli；以下只读登录态、写本机配置
python3 scripts/team_setup.py bind-user
```

成员配置默认存到 `~/.config/jihui-skills/team.json`，也可通过环境变量 `JIHUI_SKILLS_CONFIG` 指定。导入时会清空原配置中的成员身份与本机路径；共享资源所有者单独保留。已有成员配置不会被初始化命令覆盖。

没有团队入口文件时，负责人按 [配置说明](docs/TEAM_SETUP.md) 填写 [空白示例](config/team.example.json)。各项入口由真实读取确认，不凭页面标题猜 token。成员仍需具有对应资源的访问权限；本工具不添加协作者、不改权限、不向飞书写业务内容。

### 3. 检查后开始任务

```bash
python3 scripts/team_setup.py doctor --skill campus-job-matching --live
```

检查会报告缺失字段、工具可用性和成员登录是否一致。它不证明岗位当前在招、目标页面有写权限或业务交付已经完成；每次任务仍要读取当前来源和真实目标。

选岗流程：**定位该生原投递表 → 先查团队共享岗位库 → 按当前简历逐岗复核 → 不足再外搜 → 在原表去重追加并回读**。沿用原默认视图，不另建日期页、批次表或批次视图。没有原投递表时，确认确实不存在，再在已配置学生目录下按原格式建空表。

共享岗位库缺配置、无权限或读取失败时，应报告具体缺口；不能写“已查库”或把它当作库内没有岗位。公司上限以本次明确要求优先；没有另定范围时，同一学生每家公司累计默认最多 3 个岗位，历史记录计入，真实岗位去重始终执行。

## 目录

当前随包提供 **21 个业务 Skill**，详见 [用途、依赖与交付面](docs/SKILL_CATALOG.md)。本机另外一项微信能力作为可选私有连接器交接；10 个第三方通用 Skill 保留其上游来源，不重新冠名分发。32 项完整盘点见 [来源清单](docs/SOURCE_INVENTORY.md)。

聊天整理、录音、朋友圈与候选人审查等有界任务，不因缺少无关飞书配置而停止。正式、可归档的学生材料默认写入唯一飞书页面；用户明确限定聊天、本地、PDF或只读时按该范围执行。

## 页面与交付规则

学生唯一飞书主页是既有根入口。通用双端标题为 `姓名｜面试指导者版（内部）`、`姓名｜学生面试准备版`；专岗在学生主页下建独立的 `专岗准备｜公司｜岗位`；真实面试复盘为 `面试复盘｜公司｜日期`，默认放在学生面试准备版下的唯一子页。已有同场页或本次指定位置优先，不移动既有页面。

专岗讲解图片嵌入正文对应章节，保留既有有效画板；正文图片、附件与学生端阅读效果要实际检查。新作品集规划不能写成学生已上线的经历。学生亲自完成的导师带教实践属于真实实践，只核对具体职责、指标、时间与归因的冲突。

## 工具与能力

- 飞书任务需要成员本人已登录的 `lark-cli`。共享库所有者和操作者分开核对，不要求把团队库转给每个成员。
- Word/PDF需要对应文档工具；简历检查器的Python依赖见 [环境说明](docs/ENVIRONMENT.md)。没有渲染能力时不得宣称版式已验收。
- 小红书图片需要 Node.js、Playwright 和 Chrome/Chromium。进入图片 Skill 后按其 `package.json` 安装依赖；浏览器可用 `--chrome-path` 或 `XHS_CHROME_PATH` 指定。
- 浏览器、设计工具、聊天连接器和知识库由成员按任务配置。未具备的能力应说明缺口，不猜作者的插件缓存，也不读取作者私有资料。

## 后续更新与验证

这个仓库是团队统一公开入口，版本为 `0.5.0`。历史仓库名 `codex-student-interview-skills` 的插件 ID 保留以兼容既有安装；项目地址统一使用本仓库。

作者环境的自动同步只处理白名单规则、Skill 与运行资源：比较上次已发布源快照，保留公开版的团队适配；检查配置、引用、测试和敏感信息后提交推送。发现冲突、缺源或新的私密内容时保留双方并报告，不强制覆盖、不把跳过对象说成已经同步。机制见 [同步约定](docs/PUBLIC_SYNC.md)。

发布前在图片Skill目录执行一次 `npm ci --ignore-scripts` 安装已锁定依赖，再回到仓库根目录运行：

```bash
python3 scripts/build_team_docs.py
python3 scripts/build_manifest.py
uv run --with pyyaml --with python-docx --with pdfplumber --with lxml   --with pypdf --with reportlab python scripts/verify_release.py
```

[环境与依赖](docs/ENVIRONMENT.md) · [团队配置](docs/TEAM_SETUP.md) · [来源与公开边界](docs/PROVENANCE.md)
