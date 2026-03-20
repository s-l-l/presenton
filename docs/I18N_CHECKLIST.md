# Presenton 汉化 Checklist

本项目前端主要位于 `servers/nextjs/` 目录下。为了保证汉化质量，我们将按照模块逐步推进，并在本文件中记录进度。

## 核心模块进度

- [x] **1. 欢迎页与全局组件 (Home & Globals)**
  - [x] `app/page.tsx` (根页面 / 重定向)
  - [x] `components/Home.tsx` (主页)
  - [x] `components/Header.tsx`
  - [x] `components/OnBoarding/*` (引导流程)

- [x] **2. 控制台 (Dashboard)**
  - [x] `app/(presentation-generator)/(dashboard)/Components/DashboardSidebar.tsx` (侧边栏)
  - [x] `app/(presentation-generator)/(dashboard)/Components/DashboardNav.tsx` (顶部导航)
  - [x] `app/(presentation-generator)/(dashboard)/dashboard/components/DashboardPage.tsx`
  - [x] `app/(presentation-generator)/(dashboard)/dashboard/components/EmptyState.tsx`
  - [x] `app/(presentation-generator)/(dashboard)/dashboard/components/PresentationCard.tsx`

- [x] **3. 创建配置页 (Upload/Create)**
  - [x] `app/(presentation-generator)/upload/components/UploadPage.tsx`
  - [x] `app/(presentation-generator)/upload/components/PromptInput.tsx`
  - [x] `app/(presentation-generator)/upload/components/AdvanceSettings.tsx`
  - [x] `app/(presentation-generator)/upload/components/SupportingDoc.tsx`

- [x] **4. 大纲编辑页 (Outline)**
  - [x] `app/(presentation-generator)/outline/components/OutlinePage.tsx`
  - [x] `app/(presentation-generator)/outline/components/OutlineContent.tsx`
  - [x] `app/(presentation-generator)/outline/components/TemplateSelection.tsx`
  - [x] `app/(presentation-generator)/outline/components/GenerateButton.tsx`

- [x] **5. 演示文稿预览/编辑 (Presentation)**
  - [x] `app/(presentation-generator)/presentation/components/PresentationPage.tsx`
  - [x] `app/(presentation-generator)/presentation/components/SidePanel.tsx`
  - [x] `app/(presentation-generator)/presentation/components/PresentationHeader.tsx`
  - [x] `app/(presentation-generator)/presentation/components/SlideContent.tsx`

- [x] **6. 设置与主题 (Settings & Theme)**
  - [x] `app/(presentation-generator)/(dashboard)/settings/SettingPage.tsx`
  - [x] `app/(presentation-generator)/(dashboard)/settings/SettingSideBar.tsx`
  - [x] `app/(presentation-generator)/(dashboard)/theme/components/ThemePanel/*`
  - [x] `components/LLMSelection.tsx` / `OpenAIConfig.tsx` 等提供商配置

## 汉化规范
1. 保持专业术语的准确性（如 "Prompt" -> "提示词"，"Layout" -> "布局"，"Outline" -> "大纲"）。
2. 不破坏原有的 UI 结构和变量占位符。
3. 提示信息 (Toast/Sonner) 同步汉化。
