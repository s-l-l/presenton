"use client";
import { Button } from "@/components/ui/button";
import {
  Play,
  Loader2,
  Redo2,
  Undo2,
  RotateCcw,
  ArrowRightFromLine,

  ArrowUpRight,

} from "lucide-react";
import React, { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { PresentationGenerationApi } from "../../services/api/presentation-generation";
import { useDispatch, useSelector } from "react-redux";


import { RootState } from "@/store/store";
import { toast } from "sonner";


import { PptxPresentationModel } from "@/types/pptx_models";
import { trackEvent, MixpanelEvent } from "@/utils/mixpanel";
import { usePresentationUndoRedo } from "../hooks/PresentationUndoRedo";
import ToolTip from "@/components/ToolTip";
import { clearPresentationData } from "@/store/slices/presentationGeneration";
import { clearHistory } from "@/store/slices/undoRedoSlice";
import { Separator } from "@/components/ui/separator";
import ThemeSelector from "./ThemeSelector";
import { DEFAULT_THEMES } from "../../(dashboard)/theme/components/ThemePanel/constants";
import ThemeApi from "../../services/api/theme";
import { Theme } from "../../services/api/types";
import MarkdownRenderer from "@/components/MarkDownRender";

const PresentationHeader = ({
  presentation_id,
  isPresentationSaving,
  currentSlide,
}: {
  presentation_id: string;
  isPresentationSaving: boolean;
  currentSlide?: number;
}) => {
  const [open, setOpen] = useState(false);
  const router = useRouter();
  const [isExporting, setIsExporting] = useState(false);
  const [themes, setThemes] = useState<Theme[]>([]);

  const pathname = usePathname();
  const dispatch = useDispatch();


  const { presentationData, isStreaming } = useSelector(
    (state: RootState) => state.presentationGeneration
  );

  useEffect(() => {
    const load = async () => {
      try {
        const [customThemes] = await Promise.all([
          ThemeApi.getThemes(),
        ]);
        setThemes([...customThemes, ...DEFAULT_THEMES]);
      } catch (e: any) {
        toast.error(e?.message || "加载主题失败");
      }
    };
    if (themes.length === 0) {
      load();
    }
  }, []);

  const { onUndo, onRedo, canUndo, canRedo } = usePresentationUndoRedo();

  const get_presentation_pptx_model = async (id: string): Promise<PptxPresentationModel> => {
    const response = await fetch(`/api/presentation_to_pptx_model?id=${id}`);
    const pptx_model = await response.json();
    return pptx_model;
  };

  const exportViaIpc = async (format: "pptx" | "pdf"): Promise<boolean> => {
    if (typeof window === 'undefined') return false;
    if (!(window as any).electron?.exportPresentation) return false;
    trackEvent(
      format === "pptx"
        ? MixpanelEvent.Header_ExportAsPPTX_API_Call
        : MixpanelEvent.Header_ExportAsPDF_API_Call
    );
    const result = await (window as any).electron.exportPresentation(
      presentation_id,
      presentationData?.title || '演示文稿',
      format
    );
    if (!result?.success) {
      throw new Error(result?.message || '导出失败');
    }
    return true;
  };

  const downloadLink = (url: string, filename: string) => {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleExportPptx = async () => {
    if (isStreaming) return;

    try {
      setIsExporting(true);
      // Save the presentation data before exporting
      trackEvent(MixpanelEvent.Header_UpdatePresentationContent_API_Call);
      await PresentationGenerationApi.updatePresentationContent(presentationData);

      if (await exportViaIpc("pptx")) {
        toast.success("PPTX 导出成功！");
        return;
      }

      trackEvent(MixpanelEvent.Header_GetPptxModel_API_Call);
      const pptx_model = await get_presentation_pptx_model(presentation_id);
      if (!pptx_model) {
        throw new Error("获取演示文稿 PPTX 模型失败");
      }
      trackEvent(MixpanelEvent.Header_ExportAsPPTX_API_Call);
      const blob = await PresentationGenerationApi.exportAsPPTX(pptx_model);
      if (blob) {
        const url = window.URL.createObjectURL(blob);
        downloadLink(url, `${presentationData?.title || '演示文稿'}.pptx`);
        window.URL.revokeObjectURL(url);
      } else {
        throw new Error("导出未返回有效数据");
      }
    } catch (error) {
      console.error("Export failed:", error);
      toast.error("导出遇到问题！", {
        description:
          "导出您的演示文稿时遇到问题。请重试。",
      });
    } finally {
      setIsExporting(false);
    }
  };

  const handleExportPdf = async () => {
    if (isStreaming) return;

    try {
      setIsExporting(true);
      // Save the presentation data before exporting
      trackEvent(MixpanelEvent.Header_UpdatePresentationContent_API_Call);
      await PresentationGenerationApi.updatePresentationContent(presentationData);

      trackEvent(MixpanelEvent.Header_ExportAsPDF_API_Call);
      if (await exportViaIpc("pdf")) {
        toast.success("PDF 导出成功！");
        return;
      }
      const response = await fetch('/api/export-as-pdf', {
        method: 'POST',
        body: JSON.stringify({
          id: presentation_id,
          title: presentationData?.title,
        })
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        downloadLink(url, `${presentationData?.title || '演示文稿'}.pdf`);
        window.URL.revokeObjectURL(url);
      } else {
        throw new Error("导出 PDF 失败");
      }

    } catch (err) {
      console.error(err);
      toast.error("导出遇到问题！", {
        description:
          "导出您的演示文稿时遇到问题。请重试。",
      });
    } finally {
      setIsExporting(false);
    }
  };
  const handleReGenerate = () => {
    dispatch(clearPresentationData());
    dispatch(clearHistory())
    trackEvent(MixpanelEvent.Header_ReGenerate_Button_Clicked, { pathname });
    router.push(`/presentation?id=${presentation_id}&stream=true`);
  };

  const ExportOptions = ({ mobile }: { mobile: boolean }) => (
    <div className={` rounded-[18px] max-md:mt-4 ${mobile ? "" : "bg-white"}  p-5`}>
      <p className="text-sm font-medium text-[#19001F]">导出为</p>
      <div className="my-[18px] h-[1px] bg-[#E8E8E8]" />
      <div className="space-y-3">

        <Button
          onClick={() => {
            trackEvent(MixpanelEvent.Header_Export_PDF_Button_Clicked, { pathname });
            handleExportPdf();
            setOpen(false);
          }}
          variant="ghost"
          className={`  rounded-none px-0 w-full text-xs flex justify-start text-black hover:bg-transparent ${mobile ? "bg-white py-6 border-none rounded-lg" : ""}`} >

          PDF
          <ArrowUpRight className="w-3.5 h-3.5" />
        </Button>
        <Button
          onClick={() => {
            trackEvent(MixpanelEvent.Header_Export_PPTX_Button_Clicked, { pathname });
            handleExportPptx();
            setOpen(false);
          }}
          variant="ghost"
          className={`w-full flex px-0 justify-start text-xs text-black hover:bg-transparent  ${mobile ? "bg-white py-6" : ""}`}
        >

          PPTX
          <ArrowUpRight className="w-3.5 h-3.5" />
        </Button>
      </div>


    </div>
  );




  return (
    <>
      <div className="py-7 sticky top-0 bg-white z-50 mb-[17px]  font-syne flex justify-between items-center">
        <h2 className="text-lg text-[#101323] font-unbounded "><MarkdownRenderer content={presentationData?.title || "演示文稿"} className="mb-0  w-[600px] truncate text-sm text-[#101323] " /></h2>
        <div className="flex items-center gap-2.5">

          {isPresentationSaving && <div className="flex items-center gap-2">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          </div>}
          <ThemeSelector presentation_id={presentation_id} current_theme={presentationData?.theme || {}} themes={themes} />

          <div className="flex items-center gap-2 bg-[#F6F6F9] px-3.5 h-[38px] border border-[#EDECEC] rounded-[80px]">

            <ToolTip content="重新生成">
              <button onClick={handleReGenerate} className="group">
                <RotateCcw className="w-3.5 h-3.5 text-[#101323] group-hover:text-[#5141e5] duration-300" />
              </button>
            </ToolTip>
            <Separator orientation="vertical" className="h-4" />
            <ToolTip content="撤销">
              <button disabled={!canUndo} className=" disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer group" onClick={() => {
                onUndo();
              }}>

                <Undo2 className="w-3.5 h-3.5 text-[#101323] group-hover:text-[#5141e5] duration-300" />

              </button>
            </ToolTip>
            <Separator orientation="vertical" className="h-4" />
            <ToolTip content="重做">

              <button disabled={!canRedo} className=" disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer group" onClick={() => {

                onRedo();
              }}>
                <Redo2 className="w-3.5 h-3.5 text-[#101323] group-hover:text-[#5141e5] duration-300" />

              </button>
            </ToolTip>
            <Separator orientation="vertical" className="h-4 w-[2px]" />
            <ToolTip content="演示">
              <button
                onClick={() => {
                  const to = `?id=${presentation_id}&mode=present&slide=${currentSlide || 0}`;
                  trackEvent(MixpanelEvent.Navigation, { from: pathname, to });
                  router.push(to);
                }}
                disabled={!presentationData?.slides || presentationData?.slides.length === 0} className="cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed group">
                <Play className="w-3.5 h-3.5 text-[#101323] group-hover:text-[#5141e5] duration-300" />
              </button>
            </ToolTip>
          </div>

          <Popover open={open} onOpenChange={setOpen} >
            <PopoverTrigger asChild>
              <button className="flex  items-center gap-[7px] px-[18px] py-[11px] rounded-[53px] text-sm font-semibold text-[#101323]"
                style={{
                  background: "linear-gradient(270deg, #D5CAFC 2.4%, #E3D2EB 27.88%, #F4DCD3 69.23%, #FDE4C2 100%)",
                }}
                disabled={isExporting}
              >
                {isExporting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "导出"} <ArrowRightFromLine className="w-3.5 h-3.5" />
              </button>
            </PopoverTrigger>
            <PopoverContent align="end" className="w-[200px] rounded-[18px] space-y-2 p-0  ">
              <ExportOptions mobile={false} />
            </PopoverContent>
          </Popover>
        </div>
      </div>
    </>
  );
};

export default PresentationHeader;
