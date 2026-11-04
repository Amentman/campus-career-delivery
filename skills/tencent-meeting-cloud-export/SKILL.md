---
name: tencent-meeting-cloud-export
description: Use when the user asks to batch download Tencent Meeting cloud recordings and transcripts from the currently logged-in account to a local folder, including after switching accounts. Covers browser-based inventory, resumable downloads, transcript versions, and verification; does not process meeting content or upload it to cloud storage.
---

# 腾讯会议云录制导出

首次供团队成员使用时，先读 [团队配置与依赖](references/team-setup.md)，只配置当前任务所需能力。

用已登录的腾讯会议**网页版**清点“我的录制”，把当前账号有权限下载的视频和逐字稿保存到桌面单独目录。批量下载授权包含本次下载、状态记录与验收，不包含公开、发送或网盘上传。默认使用已验证不会激活窗口的后台浏览器能力，不切换用户的前台窗口或抢鼠标键盘；不要进入“历史会议”、发起会议或改动录制。

## 开始前

本目录包含通用化导出脚本，不包含成员账号、录制链接、cookies、状态目录或录制文件。每位成员使用自己已授权的网页版登录；不要复制制作者或同事的登录态。下载脚本需要 Python 3、`ffprobe`（验视频时长），浏览器阶段另需 `browser-use` 与它注入的 Python helpers。上游浏览器工具由成员环境自行提供，安装本 Skill 不会安装或登录这些能力。先确认工具和当前授权，不静默安装依赖。

1. 读取 `browser-use` Skill，检查已有登录和后台连接。当前导出脚本会调用 `switch_tab()`，已安装 harness 的该方法会激活标签页；现有脚本不是已验证的后台下载路线。只有用户明确授权前台操作时才能按下方脚本运行。否则选择已可用、适合下载且不激活窗口的能力；没有该能力时停在浏览器依赖处并说明原因，不静默运行脚本、开收费云会话或切换窗口。若目标账号未登录，说明登录要求；客户端账号切换不代表网页版也已切换。
2. 先读出网页版账号标识和“我的录制”数量，再执行下载。若与用户指定账号或本地旧归档不符，停在清点阶段。无权限、来源空内容可记录并跳过，不尝试绕过权限。
3. 在上述能力和授权条件满足时，使用本 Skill 的 [导出脚本](scripts/export.py)。脚本只接受当前浏览器已有的腾讯会议登录态，不保存登录令牌；状态文件留在 `~/.codex/tencent-meeting-export-state`，桌面归档只放媒体、逐字稿、清单和说明。沿用已有下载授权，不为清点后每个正常下载步骤重复确认。

## 执行

满足上述能力和授权条件后，先运行清点阶段。脚本路径从本次加载的 Skill 根目录解析，成员不必安装到制作者的用户目录。先把下面变量替换为实际路径；后续命令沿用它，不依赖项目 cwd。

```bash
TMEET_SKILL_DIR='<本Skill实际目录>'
export TMEET_SKILL_DIR
TMEET_EXPORT_PHASE=inventory browser-use <<'PY'
import os
p = os.path.join(os.environ['TMEET_SKILL_DIR'], 'scripts', 'export.py')
scope = dict(globals(), __name__='tmeet_skill')
exec(compile(open(p).read(), p, 'exec'), scope)
scope['main']()
PY
```

输出中的 `state_dir` 和 `dest` 要核对账号与目录。后续阶段均设置 `TMEET_EXPORT_STATE_DIR` 为该 `state_dir`，依次运行 `transcripts`、`videos`。运行方式与上面相同，只需改 `TMEET_EXPORT_PHASE`。中断后原命令可续跑，已完成文件按大小和视频时长验证，不重复下载。网页账号中途改变时脚本会停止。

最后运行：

```bash
TMEET_EXPORT_PHASE=finalize TMEET_EXPORT_STATE_DIR='<清点输出的 state_dir>' python3 "$TMEET_SKILL_DIR/scripts/export.py"
```

`finalize` 必须逐项对齐来源记录、下载状态、文件大小与 MP4 可读时长，并检查没有残留 `.part` 或分段文件。只在退出码为 0、异常清单为空时称为全部完成。交付桌面目录和 `归档清单.csv` 的本地链接，说明已下载数量、来源空内容/无权限数量及未解决项。

## 安装验收与离线续接检查

以下命令不连接浏览器、不读取默认私人状态、不写配置或归档；`--check-state` 只读取显式选择的状态与其指向的归档，必须是当前任务允许检查的目录：

```bash
python3 "$TMEET_SKILL_DIR/scripts/export.py" --help
python3 -m unittest discover -s "$TMEET_SKILL_DIR/tests" -v
python3 "$TMEET_SKILL_DIR/scripts/export.py" --check-state '<本次明确选择的 state_dir>'
```

续接检查核对 `run.json`、`inventory.json`、数量、唯一记录、已有完成文件的路径与大小；只输出计数和异常，不输出账号 UID、标题或录制地址。退出 0 只表示本地状态可以进入后续账号核对，不证明网页仍登录、下载权限有效、视频可播放或导出完成。继续下载时仍须核对网页版账号、当前后台能力与本次授权；当前下载脚本可能激活 Chrome，未经前台授权不能因为离线检查通过就启动它。

成员可以按任务设置 `TMEET_EXPORT_STATE_ROOT`、`TMEET_EXPORT_DEST` 或 `TMEET_EXPORT_DESKTOP`；`TMEET_EXPORT_EXPECT_UID` 可约束本次账号，但真实值只留成员私有环境。状态和产物不得提交公开仓库。

## 关键边界

- 每次新账号用账号 UID 和日期隔离目录；不要写入此前正在上传网盘的归档。相同账号同日重跑可续传，目的目录已有内容但没有匹配状态记录时脚本会拒绝覆盖。
- 视频可能有主画面、共享屏幕、说话人等多路文件，全部保存。独立“转写”条目与视频详情的逐字稿可能文字不同，分别导出并在清单标明来源。
- 腾讯会议网页接口或文件类型变化时，先核对实际页面与请求，再调整脚本。未知类型、下载格式或权限错误不得当作成功。
- 网盘上传不在此 Skill 的默认范围内；只有用户另行授权时才上传。
