# Tasks

## Presenton (FastAPI) 实现
- [x] Task 1: 创建 `ThirdPartyPptService` 用于编排 PPT 生成逻辑。
  - [x] SubTask 1.1: 实现 `generate_outline_with_context` 接口。
  - [x] SubTask 1.2: 实现 `build_presentation_from_outlines` 接口（同步处理）。
- [x] Task 2: 创建 `servers/fastapi/api/v1/ppt/endpoints/third_party.py` 路由。
  - [x] SubTask 2.1: 实现 `POST /generate` 接口。
  - [x] SubTask 2.2: 实现 `POST /build` 接口。
  - [x] SubTask 2.3: 实现 `GET /download/{id}` 接口。
- [x] Task 3: 在 `servers/fastapi/api/v1/ppt/router.py` 中注册 `THIRD_PARTY_ROUTER`。

## dataAgent 后端 (Spring Boot) 实现
- [x] Task 4: 在 `application.yml` 中新增 `presenton.api.url` 配置。
- [x] Task 5: 创建 `com.alibaba.cloud.ai.dataagent.service.ppt.PptService` 及其实现。
  - [x] SubTask 5.1: 使用 `WebClient` 实现对 `presenton` 的三方接口调用。
- [x] Task 6: 创建 `com.alibaba.cloud.ai.dataagent.controller.PptController` 提供代理接口。
  - [x] SubTask 6.1: 实现 `/api/ppt/generate` 接口。
  - [x] SubTask 6.2: 实现 `/api/ppt/build` 接口。
  - [x] SubTask 6.3: 实现 `/api/ppt/download/{id}` 接口。

## dataAgent 前端 (Vue 3) 实现
- [x] Task 7: 创建 `src/services/ppt.ts` API 客户端。
- [x] Task 8: 创建 `src/components/run/PptGenerateDialog.vue` 分步对话框组件。
  - [x] SubTask 8.1: 实现步骤 1：确认内容 + 选择页数。
  - [x] SubTask 8.2: 实现步骤 2：大纲展示与编辑。
  - [x] SubTask 8.3: 实现步骤 3：生成进度展示。
  - [x] SubTask 8.4: 实现步骤 4：完成下载。
- [x] Task 9: 在 `src/views/AgentRun.vue` 的报告气泡中添加 "生成 PPT" 按钮并触发对话框。

## 验证与测试
- [x] Task 10: 验证整个 PPT 生成流程是否跑通。

# Task Dependencies
- Task 5, 6 依赖 Task 1, 2, 3。
- Task 7, 8, 9 依赖 Task 4, 5, 6。
