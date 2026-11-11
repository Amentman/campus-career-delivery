# 团队使用说明

完整安装本目录，保留引用、示例、流程图与第三方许可证。纯写作、聊天改写或本地审稿不依赖飞书账号和团队学生库，不需要Python、Node或外部API。

读者、来源、参考与输出位置优先用当前请求和已有入口。飞书交付使用成员自己的已配置`lark-cli --as user`，核对实际身份与目标权限；本Skill不携带作者的账号、节点、私人参考原文或持续授权。

从团队主仓安装单项：

```bash
python3 scripts/team_setup.py install --dest "<运行器扫描的Skills目录>" --skill writing-readable-documents
```

检查预览与冲突后，在已授权安装范围内加`--apply`。手动复制要带整个目录。飞书、Word、PDF与图解工具按交付格式配置，不依赖作者插件缓存路径。

复杂文档配合`visual-document-delivery`和`impeccable`；前者随团队业务包提供，后者为外部上游能力。需要时按当前运行器的安装方式补齐，不复制第三方私有环境。业务Skill继续负责必需内容，本Skill不替代事实核验与权限检查。
