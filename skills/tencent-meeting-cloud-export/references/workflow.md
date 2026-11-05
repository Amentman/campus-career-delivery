# 腾讯会议归档：完整流程

输入：网页版已登录账号；录制导出范围；本地归档目录。

交付：本地视频与逐字稿；归档清单 CSV；异常和未解决项。

![完整流程图](../assets/workflow.svg)

[按原尺寸打开完整流程图](../assets/workflow.svg)

## 按什么顺序做

### 检查运行能力与授权

网页版当前登录为准；后台能力未验证且无前台授权时停止，不静默安装。

### 续接状态与账号核对

显式状态可离线检查，但通过不代表网页版登录、下载权限或完成。

### 清点并隔离归档

inventory核账号和录制数；新账号隔离，同账号同日复用，冲突不覆盖。

### 依次下载不同来源

先transcripts后videos，多路视频及独立/详情逐字稿分别保留。

### 按状态恢复与逐项验收

账号变化停止；中断可续跑，大小与时长核对后不重复下载。

### finalize对账并交付

来源、状态、大小、MP4时长和残留分段均核；异常空且退出0才称全部完成。

## 验收

- 后台能力或前台授权与网页版账号当前核对
- 目录隔离和状态匹配，不覆盖旧归档
- 无权限和空来源记录跳过不绕过
- 多路视频及两种逐字稿各自保留
- 文件大小、可读MP4时长与残留文件逐项对账
- finalize退出0且异常清单空才称全部完成
- 离线续接通过不等于线上导出完成

不绕过无权限录制；不自动处理内容或上传网盘。

## 对应规则

- [SKILL.md](../SKILL.md)
- [references/team-setup.md](team-setup.md)

<details>
<summary>可编辑的流程源码</summary>

```mermaid
flowchart TB
  input(["当前网页版账号<br/>已授权录制范围与本地目录"])
  resume{"是否续接已有显式状态？"}
  offline["离线核run/inventory与数量<br/>唯一记录、文件路径和大小"]
  offlineok{"本地状态检查通过？"}
  capability{"可用后台下载能力<br/>或已有前台操作授权？"}
  login["核网页版登录与账号<br/>客户端切换不作网页版证据"]
  account{"网页版账号符合本轮目标？"}
  inventory["清点我的录制数量与权限<br/>来源空/无权限记录并跳过"]
  destination{"账号、状态与目的目录匹配？"}
  isolate[("新账号按账号日期隔离<br/>同账号同日沿用匹配状态")]
  transcripts["先导出逐字稿<br/>独立条目与视频详情分别留存"]
  videos[("再下载所有视频文件<br/>主画面、屏幕与说话人均保存")]
  download{"下载阶段当前结果？"}
  reconcile["中断先核状态与已完成文件<br/>按大小时长跳过已完成"]
  finalize["运行finalize逐项对账<br/>来源、状态、大小、时长与残留"]
  qa{"退出0、异常清单为空<br/>且无part或分段残留？"}
  done(["交本地目录与归档清单<br/>下载、空来源/无权限及缺口数量"])
  stop(["停止具体异常并保留状态<br/>不抢前台、绕权限或覆盖旧归档"])
  input --> resume
  resume -->|"是：明确允许检查该状态"| offline
  resume -->|"否：开始新清点"| capability
  offline --> offlineok
  offlineok -->|"通过：仍须在线核账号"| capability
  offlineok -->|"不通过：仅报告状态问题"| stop
  capability -->|"满足：工具依赖亦可用"| login
  capability -->|"不满足：现脚本会激活标签页"| stop
  login --> account
  account -->|"是：登录且身份符合"| inventory
  account -->|"否：未登录或账号不符"| stop
  inventory --> destination
  destination -->|"匹配或本次新隔离目标"| isolate
  destination -->|"已有内容无匹配状态或账号冲突"| stop
  isolate --> transcripts
  transcripts --> videos
  videos --> download
  download -->|"全部阶段执行完"| finalize
  download -->|"网络中断或未完成文件"| reconcile
  download -->|"网页账号改变/未知格式权限错误"| stop
  reconcile -->|"恢复前重核能力与当前账号"| capability
  finalize --> qa
  qa -->|"全部满足"| done
  qa -->|"有未解决项：不能称全部完成"| stop
```

</details>
