# PPT 生成功能集成方案 (方案 C)

## Why
在 `dataAgent` 项目中，用户需要能够将分析生成的 AI 报告直接转化为 PPT。通过集成 `presenton` 的 PPT 生成引擎，可以显著提升用户的工作效率。采用方案 C（独立第三方 API + 轻量集成）旨在降低两个系统间的耦合，保证各层职责清晰，并提供良好的用户交互体验。

## What Changes
- **Presenton (FastAPI)**:
  - 新增独立路由 `/api/v1/ppt/third-party/`。
  - 实现 `generate`, `build`, `download` 三个轻量化接口。
  - 新增 `ThirdPartyPptService` 用于编排现有的 PPT 生成服务。
- **dataAgent Backend (Spring Boot)**:
  - 新增 `PptController` 作为代理层。
  - 新增 `PptService` 封装对 `presenton` API 的调用。
  - 在 `application.yml` 中新增 `presenton.api.url` 配置项。
- **dataAgent Frontend (Vue 3)**:
  - 新增 `PptGenerateDialog.vue` 对话框组件，提供分步引导（参数确认 -> 大纲编辑 -> 生成进度 -> 下载）。
  - 新增 `pptService.ts` 处理 API 请求。
  - 在 `AgentRun.vue` 的 AI 报告消息气泡中新增 "生成 PPT" 按钮。

## Impact
- **Affected specs**: 
  - `dataAgent` 的报告导出功能。
  - `presenton` 的 API 暴露能力。
- **Affected code**:
  - `presenton`: `servers/fastapi/api/v1/ppt/router.py`, `servers/fastapi/api/v1/ppt/endpoints/`
  - `dataAgent Backend`: `src/main/java/com/alibaba/cloud/ai/dataagent/controller/`, `service/`
  - `dataAgent Frontend`: `src/views/AgentRun.vue`, `src/services/`, `src/components/run/`

## ADDED Requirements
### Requirement: PPT 生成分步引导
系统应提供一个多步骤对话框，允许用户在生成 PPT 前确认报告内容、选择幻灯片页数，并支持在大纲生成后进行预览和编辑。

#### Scenario: 成功从报告生成 PPT
- **WHEN** 用户点击 AI 报告气泡中的 "生成 PPT" 按钮。
- **THEN** 弹出 `PptGenerateDialog`，展示报告摘要和页数选项。
- **WHEN** 用户确认参数并点击 "生成大纲"。
- **THEN** 调用后端接口获取大纲并展示，用户可编辑。
- **WHEN** 用户点击 "开始生成"。
- **THEN** 展示生成进度，完成后提供下载链接。

## MODIFIED Requirements
### Requirement: 后端代理与鉴权
`dataAgent` 后端应作为 `presenton` 的代理，隐藏 `presenton` 的真实地址，并统一处理请求鉴权。

## REMOVED Requirements
无。
