import React from "react";
import type { Metadata } from "next";
import UploadPage from "../upload/components/UploadPage";
import Header from "@/app/(presentation-generator)/(dashboard)/dashboard/components/Header";

export const metadata: Metadata = {
  title: "Presenton | Open Source AI presentation generator",
  description:
    "Open-source AI presentation generator with custom layouts, multi-model support (OpenAI, Gemini, Ollama), and PDF/PPTX export. A free Gamma alternative.",
  alternates: {
    canonical: "https://presenton.ai/create",
  },
  keywords: [
    "presentation generator",
    "AI presentations",
    "data visualization",
    "automatic presentation maker",
    "professional slides",
    "data-driven presentations",
    "document to presentation",
    "presentation automation",
    "smart presentation tool",
    "business presentations",
  ],
  openGraph: {
    title: "Create Data Presentation | PresentOn",
    description:
      "Open-source AI presentation generator with custom layouts, multi-model support (OpenAI, Gemini, Ollama), and PDF/PPTX export. A free Gamma alternative.",
    type: "website",
    url: "https://presenton.ai/create",
    siteName: "PresentOn",
  },
  twitter: {
    card: "summary_large_image",
    title: "Create Data Presentation | PresentOn",
    description:
      "Open-source AI presentation generator with custom layouts, multi-model support (OpenAI, Gemini, Ollama), and PDF/PPTX export. A free Gamma alternative.",
    site: "@presenton_ai",
    creator: "@presenton_ai",
  },
};

export default function DeckStudioPage() {
  return (
    <div className="relative">
      <Header />
      <div className="flex flex-col items-center justify-center mb-8">
        <h1 className="text-[64px] font-normal font-unbounded text-[#101323] ">
          AI 演示文稿
        </h1>
        <p className="text-xl font-syne text-[#101323CC]">
          选择一个设计主题，设置偏好后，一键生成高质量演示文稿。
        </p>
      </div>
      <UploadPage />
    </div>
  );
}
