# 逐字稿读取、完整性与漏题对照

先取得本轮原件，再进行分析。所有文件保存到本次私有任务目录，不能放进 Skill、公开仓库或长期项目事实库。以下命令的 `SKILL_DIR` 是当前安装目录，`RUN_DIR` 是本轮任务目录；先根据环境赋值，不依赖工作目录。

## 飞书妙记

1. 静默核对当前本人登录与成员配置中的身份；读取当前 `lark-minutes`、`lark-shared` 和 minutes 详情引用。`lark-cli minutes +detail --help` 必须包含 `--transcript`、`--as user` 与 `--output-dir`。不因显示名称不同重复确认本人。
2. 区分 `/minutes/`、普通文档和智能纪要。妙记执行：

```bash
python3 "$SKILL_DIR/scripts/transcript.py" prepare --source feishu \
  --input '<本轮妙记URL>' --out-dir "$RUN_DIR/source"
```

脚本调用 `lark-cli minutes +detail --minute-tokens <token> --transcript --as user --output-dir <目录>`，核对返回目标，随后实际读取 `artifacts.transcript_file`。不以成功状态、标题或 AI 总结代替原文。

3. 普通文档按当前 `lark-doc` 读取完整正文；已知智能纪要按 `lark-note`。若妙记关联纪要，先取真实 `note_id` 再取逐字稿文档 token，禁止混用 token。导出的正文走本地入口，保留其来源。权限不足只处理实际错误；不切 bot、不自动申请权限、不重复创建对象。
4. 通读实际原稿，核对开头、结束位置与双方发言。CLI 成功只说明读到了平台返回的文件，不能证明原录音没有漏录。

## 腾讯会议

优先使用本轮明确选择的完整导出；已有归档只定位同一场，不启动全账号下载。云录制详情的逐字稿与独立转写可能内容不同，分别保留来源，不自动拼接成一场。只有链接时：

1. 使用已登录且不激活用户窗口的后台浏览器，打开指定录制／转写详情，核对本轮标题、日期、记录 ID、时长（若有）和当前账号。分享页与账号下录制页分流；只能读取当前账号有权读取的内容。不要运行批量导出器的 `switch_tab()` 或 `new_tab()` 来抢占前台。
2. 读取该页实际产生的 `/minutes/detail` 请求，核对其中 `id`、`meeting_id`、`recording_id` 对应选中的记录。可在该后台页面读取 `performance.getEntriesByType('resource')`，或由可用浏览器工具观察网络请求。**不猜接口签名，不照抄历史 `recording_id + 1` 关系。**签名和完整请求 URL 只在当次浏览器内使用，不打印或保存凭据。
3. 将 `scripts/read_tencent.js` 的完整源码作为函数在该后台页执行，并调用：

```javascript
await readTencentTranscript({detailUrl: observedDetailUrl, recordId: selectedRecordId})
```

函数使用页面当前登录态，只读同源请求，不导航、不改原稿、不导出 Cookie；分页到 `more=false`，按 `pid` 去重，保留说话人、时间与原文。游标不推进、字段变化、同段不同版本、空内容、权限或网络失败均抛错，不能把部分内容报完整。外层须等待 Promise 完成。若工具没有后台执行能力、分享页不暴露该接口或接口已变化，保留具体缺口，使用该页已授权的原生导出；不能绕过权限或声称已经接通。
4. 将函数返回 JSON 原样写入本轮私有 `tencent_capture.json`（用工具文件写入，避免拼进 shell）。再执行：

```bash
python3 "$SKILL_DIR/scripts/transcript.py" prepare --source tencent \
  --input "$RUN_DIR/tencent_capture.json" --out-dir "$RUN_DIR/source"
```

这是可嵌入后台浏览器的读取器，不是带账号登录的独立腾讯 CLI。本包不提供登录态、自动切号、签名生成或录音上传。

## 已有文字与录音

TXT 支持 `[00:00:01] 说话人：正文`、`说话人 00:00:01` 后接多行正文、`[说话人][00:00:01] 正文` 或无时间戳的 `说话人：正文`。格式无法识别会保留原文并报待核对；不得静默丢弃段落。Word/PDF/SRT 等先用当前可用的读取能力导出保留说话人和位置的 UTF-8 TXT，原件不改动。

```bash
python3 "$SKILL_DIR/scripts/transcript.py" prepare --source local \
  --input "$RUN_DIR/original.txt" --out-dir "$RUN_DIR/source" --complete
```

`--complete` 仅在确认导出覆盖本轮全部来源后使用；不确定时省略。已知录制时长可加 `--duration-ms <毫秒>` 检查尾部时间差。尾部差距可能是静音，必须回查解释，不能直接判为漏录。只有录音时按已授权且实际可用的转写能力处理；未授权不上传到其他平台。

## 原稿归一化与输入检查

输出 `transcript.json` 和不会覆盖人工编辑的 `question_inventory.draft.json`。前者保留输入 SHA-256、全部发言段 `T0001…`、说话人、时间戳／行号及输入异常。重读后原稿变化会让旧问题索引失效。

完整通读，核对首尾、分页终态、双方发言、说话人和转写错字；有时长则对照末段，无法判断的明确保留。`input_review.confirmed` 是 Agent 完成原文检查后的记录，不要求用户再批准一遍。仅人物归属、关键语句或漏录无法自行查清时询问相应片段。每个 `issues` 都在 `input_review.resolutions` 中逐项解释；确实缺失写入 `limitations`，范围标 `partial`。没有时间戳可用稳定段号，不能补造。摘要不是原稿，原稿为空不能通过。

## 全量问题索引

复制草稿为 `question_inventory.json`，逐段填完。主问题、同一句中的多个问题及连续追问分别编号；不要用问号数量代替判断。学生反问也记问题，但标 `excluded` 并写明“学生反问”；寒暄、事务沟通、面试官讲解和无问题段写具体原因。面试官问句被排除时须在该段写 `non_question_evidence`，说明具体依据，不能只填“无问题”。

```json
{
  "transcript_sha256": "复制本轮transcript.json的sha256",
  "scope": "full",
  "roles": {"面试官": "interviewer", "学生": "candidate"},
  "input_review": {"confirmed": true, "limitations": [], "resolutions": {}},
  "audits": [
    {"turn_id": "T0001", "question_ids": ["Q01", "Q02"]},
    {"turn_id": "T0002", "question_ids": [], "reason": "学生回答上述两问"}
  ],
  "exchanges": {"Q01": [["T0001", "T0002"]]},
  "questions": [
    {"id": "Q01", "turn_id": "T0001", "quote": "请介绍项目。", "review_id": "Q01"},
    {"id": "Q02", "turn_id": "T0001", "quote": "你负责什么？", "review_id": "Q01"}
  ]
}
```

`quote` 必须逐字来自对应段落。`exchanges` 按复盘题卡列出有序的原始问答段落范围（首尾都包含），多处非连续讨论用多个范围，不把中间追问或候选人续答删掉。实际未作答的题保留原问题，并在该题索引写明 `no_answer_reason`，不能编造回答。正文保留 `**原始问答：**`，每个发言使用 `> [T0001] 时间｜说话人` 独立一行，下一行起用 `> 原文` 引用完整发言。脚本支持手机号、邮箱、证件号，以及带“微信／微信号／微信ID／WeChat ID”标签的账号脱敏；只替换账号本身，保留标签与周围原话。除此以外只调整排版空白；转写错字在引文外注释。题卡中写 `**来源问题：** Q01、Q02`，合并讲解也保留两问的原意与分别纠正。用户只指定部分题组时，索引仍核对全部已读段；未纳入题组的问题写 `disposition: out_of_scope` 与具体理由，`scope: partial`。不为通过格式检查重写未授权题目。

正式校验在 `validate_review.py` 中同时检查原稿、索引和题卡；局部题组可以单独运行 `transcript.py check --transcript … --inventory … --review …`，不强制补齐整册章节。输出统计须区分原稿总问题、追问、范围内已复盘、合理排除、范围外与未解决数。

机器还会比较正文的原始问答顺序和每段完整源文本，只有摘要、删句或改写会失败。原始范围仍须人工核对，不能人为缩小范围隐藏续答。机器只能抓已声明范围的结构与文本遗漏，不能保证 Agent 已识别所有隐性问题。验收时再次逐段对照原文，尤其检查一句多问、无问号的请求、连续追问、学生反问和转写断句。不能把 `coverage_checked` 当作语义质量通过。

## 方法来源

参考 [landing-0/interview-debrief](https://github.com/landing-0/interview-debrief)（MIT）的“先读取逐字稿文件、输入质量检查、全量问题索引、按本轮角色解释关注点、下一轮动作与跨轮对照”组织方式。本包代码独立实现；没有复制其全部模板，也没有腾讯专用接口来自该项目的含义。

上游 4.0 要求完整列出问题与连续追问，4.2 要求逐题分析原文证据，但没有规定每题完整粘贴候选人原答。本包的“受控正文完整原始问答及逐段文本比对”是本地交付增强，不能说成上游已有要求。
