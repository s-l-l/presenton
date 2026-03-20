# PPT 开放 API 集成 — 方案 B 实施 Checklist

## Phase 1: Presenton 后端 — 第三方开放 API

- [x] **1.1** 创建 `api/v1/openapi/` 目录结构和路由
- [x] **1.2** 实现 API Key 鉴权中间件 (`Depends`)
- [x] **1.3** `POST /api/v1/openapi/ppt/create` — 创建演示文稿（简化参数，包装现有 `create`）
- [x] **1.4** `GET /api/v1/openapi/ppt/outline/stream/{id}` — SSE 大纲流（转发现有端点）
- [x] **1.5** `POST /api/v1/openapi/ppt/prepare` — 布局准备（转发现有端点）
- [x] **1.6** `GET /api/v1/openapi/ppt/stream/{id}` — SSE 幻灯片流（转发现有端点）
- [x] **1.7** `POST /api/v1/openapi/ppt/export/{id}` — 导出 PPTX 并返回文件
- [x] **1.8** `GET /api/v1/openapi/ppt/templates` — 获取可用模板列表
- [x] **1.9** CORS 配置允许 DataAgent 域名（已有 `*` 配置，无需修改）

## Phase 2: DataAgent 前端 — API 服务层

- [ ] **2.1** 创建 `src/services/ppt.ts` — Presenton API 服务
- [ ] **2.2** 配置 vite proxy 添加 Presenton API 代理路由
- [ ] **2.3** 创建 `src/stores/ppt.ts` — Pinia store

## Phase 3: DataAgent 前端 — PPT 生成入口

- [ ] **3.1** `AgentRun.vue` 输入框 `.option-group` 中增加 PPT 按钮
- [ ] **3.2** 创建 `src/components/ppt/PptConfigDialog.vue` — 参数配置弹窗
- [ ] **3.3** 实现报告内容提取逻辑

## Phase 4: DataAgent 前端 — 大纲编辑面板

- [ ] **4.1** 创建 `src/components/ppt/PptGeneratePanel.vue` — 全屏 PPT 生成主面板
- [ ] **4.2** 创建 `src/components/ppt/OutlineEditor.vue` — 大纲列表展示和编辑
- [ ] **4.3** 创建 `src/composables/useOutlineStreaming.ts` — SSE 大纲流 composable
- [ ] **4.4** 实现大纲拖拽排序
- [ ] **4.5** 实现大纲项编辑/删除/添加

## Phase 5: DataAgent 前端 — 幻灯片生成与预览

- [ ] **5.1** 创建 `src/components/ppt/SlidePreview.vue` — 幻灯片预览组件
- [ ] **5.2** 创建 `src/components/ppt/SlideSidePanel.vue` — 左侧缩略图列表
- [ ] **5.3** 创建 `src/composables/usePresentationStreaming.ts` — SSE 幻灯片流 composable
- [ ] **5.4** 实现幻灯片逐张实时渲染
- [ ] **5.5** 实现 LoadingState 加载动画

## Phase 6: DataAgent 前端 — 导出与下载

- [ ] **6.1** 实现导出 PPTX 功能
- [ ] **6.2** 导出按钮和进度提示

## Phase 7: 联调与测试

- [ ] **7.1** 端到端流程测试
- [ ] **7.2** SSE 流式断连/错误恢复测试
- [ ] **7.3** 跨域和鉴权测试
