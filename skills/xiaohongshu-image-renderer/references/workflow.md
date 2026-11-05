# 小红书图文制作：完整流程

输入：已锁定 source.json；完整标题与正文；匹配的 sourceHash。

交付：按顺序的 NN.png；manifest 与验证结果；正文一致性和填充率。

![完整流程图](../assets/workflow.svg)

[按原尺寸打开完整流程图](../assets/workflow.svg)

## 按什么顺序做

### 读取锁定视觉合同

完整读visual-contract，默认沿用备忘录模板，未授权不改样式。

### 预检运行依赖

Node20+、Playwright、独立无头Chrome与中文字体；不复用登录浏览器。

### 准备并核对锁定输入

新输入按标题与去空白正文计算哈希；已锁定文件不得改写。

### 调用内置渲染和校验

只运行随包生产命令，任一步失败立即停，不返回半包或手工修复。

### 检查全文与逐页版面

全句与表行不拆，封面含正文，长文填充率达硬门槛。

### 交付验证包

仅声明产物文件；返回路径、文件顺序、哈希、exactText及每页填充率。

## 验收

- source.json与copy.json锁定后不改
- 只用内置渲染器及校验器
- 任一失败立即停，不返回部分包
- exactText、sourceHash及全文顺序一致
- 零溢出、完整句/表行与逐页fillRatio门槛
- 只返回合同声明文件集

只生成本地文件；不写飞书、不打开发布面、不公开发布。

## 对应规则

- [SKILL.md](../SKILL.md)
- [references/team-setup.md](team-setup.md)
- [references/visual-contract.md](visual-contract.md)

<details>
<summary>可编辑的流程源码</summary>

```mermaid
flowchart TB
  input(["已确认完整标题与正文<br/>或已有锁定图片包"])
  contract["完整读取视觉合同<br/>固定1080×1440备忘录样式"]
  runtime["预检Node20+与npm ci环境<br/>Chrome与实际中文字体"]
  ready{"必需运行能力可用？"}
  locked{"输入已经锁定？"}
  prepare["保留原标题与全文<br/>按固定公式计算sourceHash"]
  verify{"标题正文非空、哈希匹配<br/>已有身份字段保留？"}
  render["仅运行内置渲染命令<br/>独立无头配置，不用登录态"]
  rendered{"渲染命令成功？"}
  validate["运行内置包校验<br/>核全文、页序与溢出"]
  valid{"校验ok且全文一致？"}
  visual["逐页核全句、表头/表行<br/>封面正文与填充率硬门槛"]
  visualok{"实际逐页版面通过？"}
  artifacts["核manifest与声明文件集<br/>不加README或替代文件名"]
  done(["仅交本地完整验证包<br/>文件序、哈希、全文与各页填充率"])
  stop(["停止并报告原始失败<br/>不交半包、不手修或改源稿"])
  input --> contract
  contract --> runtime
  runtime --> ready
  ready -->|"不可用：说明依赖缺口"| stop
  ready -->|"可用"| locked
  locked -->|"是：保持source/copy不动"| verify
  locked -->|"否：只准备已确认输入"| prepare
  prepare --> verify
  verify -->|"不匹配：不得改锁定稿"| stop
  verify -->|"匹配"| render
  render --> rendered
  rendered -->|"失败：立即停止"| stop
  rendered -->|"成功"| validate
  validate --> valid
  valid -->|"失败或ok=false"| stop
  valid -->|"通过"| visual
  visual --> visualok
  visualok -->|"不通过：不手工修复"| stop
  visualok -->|"通过"| artifacts
  artifacts --> done
```

</details>
