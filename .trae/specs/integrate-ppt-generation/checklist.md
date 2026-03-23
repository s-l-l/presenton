# Checklist
- [x] Presenton 新增 `/api/v1/ppt/third-party/` 路由并能正确处理请求。
- [x] `ThirdPartyPptService` 能够复用现有的 PPT 生成逻辑生成完整 PPTX 文件。
- [x] dataAgent 后端 `PptController` 成功代理请求至 `presenton`。
- [x] dataAgent 后端配置项 `presenton.api.url` 已生效。
- [x] dataAgent 前端 `PptGenerateDialog` 对话框组件功能完整。
- [x] 报告气泡中的 "生成 PPT" 按钮能正确触发对话框。
- [x] 用户可以编辑大纲，并基于编辑后的大纲生成 PPT。
- [x] 生成进度展示正常。
- [x] PPTX 文件能成功下载并能正常打开。
