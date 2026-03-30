import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { LanguageType, PresentationConfig, ToneType, VerbosityType } from "../type";
import { useState } from "react";
import { GalleryVertical, SlidersHorizontal } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import ToolTip from "@/components/ToolTip";

// Types
interface ConfigurationSelectsProps {
    config: PresentationConfig;
    onConfigChange: (key: keyof PresentationConfig, value: any) => void;
}

type SlideOption = "5" | "8" | "9" | "10" | "11" | "12" | "13" | "14" | "15" | "16" | "17" | "18" | "19" | "20";

// Constants
const SLIDE_OPTIONS: SlideOption[] = ["5", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20"];

const TONE_LABELS: Record<ToneType, string> = {
    [ToneType.Default]: "默认",
    [ToneType.Casual]: "随和",
    [ToneType.Professional]: "专业",
    [ToneType.Funny]: "幽默",
    [ToneType.Educational]: "教育",
    [ToneType.Sales_Pitch]: "销售",
};

const VERBOSITY_LABELS: Record<VerbosityType, string> = {
    [VerbosityType.Concise]: "简洁",
    [VerbosityType.Standard]: "标准",
    [VerbosityType.Text_Heavy]: "详尽",
};

/**
 * Renders a select component for slide count
 */
const SlideCountSelect: React.FC<{
    value: string | null;
    onValueChange: (value: string) => void;
}> = ({ value, onValueChange }) => {
    const [customInput, setCustomInput] = useState(
        value && !SLIDE_OPTIONS.includes(value as SlideOption) ? value : ""
    );

    const sanitizeToPositiveInteger = (raw: string): string => {
        const digitsOnly = raw.replace(/\D+/g, "");
        if (!digitsOnly) return "";
        // Remove leading zeros
        const noLeadingZeros = digitsOnly.replace(/^0+/, "");
        return noLeadingZeros;
    };

    const applyCustomValue = () => {
        const sanitized = sanitizeToPositiveInteger(customInput);
        if (sanitized && Number(sanitized) > 0) {
            onValueChange(sanitized);
        }
    };

    return (
        <Select value={value || ""} onValueChange={onValueChange} name="slides">
            <SelectTrigger
                className="w-[140px]  font-instrument_sans font-medium bg-white text-slate-700 hover:bg-slate-50 focus-visible:ring-[#5146E5]/30 flex items-center gap-2 h-10 rounded-xl px-3 ring-1 ring-inset ring-slate-200 shadow-sm"
                data-testid="slides-select"
            >
                <div className="flex items-center gap-2.5"><GalleryVertical className="w-4 h-4" /> <SelectValue placeholder="选择幻灯片数" /></div>
            </SelectTrigger>
            <SelectContent className="font-instrument_sans">
                {/* Sticky custom input at the top */}
                <div
                    className="sticky top-0 z-10 bg-white  p-2 border-b"
                    onMouseDown={(e) => e.stopPropagation()}
                    onPointerDown={(e) => e.stopPropagation()}
                    onClick={(e) => e.stopPropagation()}
                >
                    <div className="flex items-center gap-2">
                        <Input
                            inputMode="numeric"
                            pattern="[0-9]*"
                            value={customInput}
                            onMouseDown={(e) => e.stopPropagation()}
                            onPointerDown={(e) => e.stopPropagation()}
                            onClick={(e) => e.stopPropagation()}
                            onChange={(e) => {
                                const next = sanitizeToPositiveInteger(e.target.value);
                                setCustomInput(next);
                            }}
                            onKeyDown={(e) => {
                                if (e.key === "Enter") {
                                    e.preventDefault();
                                    applyCustomValue();
                                }
                            }}
                            onBlur={applyCustomValue}
                            placeholder="--"
                            className="h-8 w-16 px-2 text-sm"
                        />
                        <span className="text-sm font-medium">页</span>
                    </div>
                </div>

                {/* Hidden item to allow SelectValue to render custom selection */}
                {value && !SLIDE_OPTIONS.includes(value as SlideOption) && (
                    <SelectItem value={value} className="hidden">
                        {value} 页
                    </SelectItem>
                )}

                {SLIDE_OPTIONS.map((option) => (
                    <SelectItem
                        key={option}
                        value={option}
                        className="font-instrument_sans text-sm font-medium"
                        role="option"
                    >
                        {option} 页
                    </SelectItem>
                ))}
            </SelectContent>
        </Select>
    );
};

export function ConfigurationSelects({
    config,
    onConfigChange,
}: ConfigurationSelectsProps) {
    const [openAdvanced, setOpenAdvanced] = useState(false);

    const [advancedDraft, setAdvancedDraft] = useState({
        tone: config.tone,
        verbosity: config.verbosity,
        instructions: config.instructions,
        includeTableOfContents: config.includeTableOfContents,
        includeTitleSlide: config.includeTitleSlide,
        webSearch: config.webSearch,
    });

    const handleOpenAdvancedChange = (open: boolean) => {
        if (open) {
            setAdvancedDraft({
                tone: config.tone,
                verbosity: config.verbosity,
                instructions: config.instructions,
                includeTableOfContents: config.includeTableOfContents,
                includeTitleSlide: config.includeTitleSlide,
                webSearch: config.webSearch,
            });
        }
        setOpenAdvanced(open);
    };

    const handleSaveAdvanced = () => {
        onConfigChange("tone", advancedDraft.tone);
        onConfigChange("verbosity", advancedDraft.verbosity);
        onConfigChange("instructions", advancedDraft.instructions);
        onConfigChange("includeTableOfContents", advancedDraft.includeTableOfContents);
        onConfigChange("includeTitleSlide", advancedDraft.includeTitleSlide);
        onConfigChange("webSearch", advancedDraft.webSearch);
        setOpenAdvanced(false);
    };

    return (
        <div className="flex flex-wrap order-1 gap-4 items-center">
            <SlideCountSelect
                value={config.slides}
                onValueChange={(value) => onConfigChange("slides", value)}
            />
            <ToolTip content="高级设置">

                <button
                    aria-label="高级设置"
                    title="高级设置"
                    type="button"
                    onClick={() => handleOpenAdvancedChange(true)}
                    className="ml-auto flex items-center gap-2 text-sm bg-white text-slate-700 hover:bg-slate-50 focus-visible:ring-[#5146E5]/30 h-10 rounded-xl px-3 ring-1 ring-inset ring-slate-200 shadow-sm font-instrument_sans font-medium"
                    data-testid="advanced-settings-button"
                >
                    <SlidersHorizontal className="h-4 w-4" aria-hidden="true" />
                </button>
            </ToolTip>

            <Dialog open={openAdvanced} onOpenChange={handleOpenAdvancedChange}>
                <DialogContent className="max-w-2xl font-instrument_sans">
                    <DialogHeader>
                        <DialogTitle>高级设置</DialogTitle>
                    </DialogHeader>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                        {/* Tone */}
                        <div className="w-full flex flex-col gap-2">
                            <label className="text-sm font-semibold text-gray-700">语气</label>
                            <p className="text-xs text-gray-500">控制写作风格（例如：随和、专业、幽默）。</p>
                            <Select
                                value={advancedDraft.tone}
                                onValueChange={(value) => setAdvancedDraft((prev) => ({ ...prev, tone: value as ToneType }))}
                            >
                                <SelectTrigger className="w-full font-instrument_sans capitalize font-medium bg-white border-slate-300 hover:bg-slate-50 focus-visible:ring-slate-300">
                                    <SelectValue placeholder="选择语气" />
                                </SelectTrigger>
                                <SelectContent className="font-instrument_sans">
                                    {Object.values(ToneType).map((tone) => (
                                        <SelectItem key={tone} value={tone} className="text-sm font-medium capitalize">
                                            {TONE_LABELS[tone]}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        {/* Verbosity */}
                        <div className="w-full flex flex-col gap-2">
                            <label className="text-sm font-semibold text-gray-700">详细程度</label>
                            <p className="text-xs text-gray-500">控制幻灯片描述的详细程度：简洁、标准或文本密集。</p>
                            <Select
                                value={advancedDraft.verbosity}
                                onValueChange={(value) => setAdvancedDraft((prev) => ({ ...prev, verbosity: value as VerbosityType }))}
                            >
                                <SelectTrigger className="w-full font-instrument_sans capitalize font-medium bg-white border-slate-300 hover:bg-slate-50 focus-visible:ring-slate-300">
                                    <SelectValue placeholder="选择详细程度" />
                                </SelectTrigger>
                                <SelectContent className="font-instrument_sans">
                                    {Object.values(VerbosityType).map((verbosity) => (
                                        <SelectItem key={verbosity} value={verbosity} className="text-sm font-medium capitalize">
                                            {VERBOSITY_LABELS[verbosity]}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>



                        {/* Toggles */}
                        <div className="w-full flex flex-col gap-2 p-3 rounded-md bg-slate-50 border-slate-200">
                            <div className="flex items-center justify-between">
                                <label className="text-sm font-semibold text-gray-700">包含目录页</label>
                                <Switch
                                    checked={advancedDraft.includeTableOfContents}
                                    onCheckedChange={(checked) => setAdvancedDraft((prev) => ({ ...prev, includeTableOfContents: checked }))}
                                />
                            </div>
                            <p className="text-xs text-gray-600">添加一个总结各章节的索引幻灯片（需要至少 3 页）。</p>
                        </div>
                        <div className="w-full flex flex-col gap-2 p-3 rounded-md bg-slate-50 border-slate-200">
                            <div className="flex items-center justify-between">
                                <label className="text-sm font-semibold text-gray-700">标题幻灯片</label>
                                <Switch
                                    checked={advancedDraft.includeTitleSlide}
                                    onCheckedChange={(checked) => setAdvancedDraft((prev) => ({ ...prev, includeTitleSlide: checked }))}
                                />
                            </div>
                            <p className="text-xs text-gray-600">包含一个作为第一页的标题幻灯片。</p>
                        </div>
                        <div className="w-full flex flex-col gap-2 p-3 rounded-md bg-slate-50 border-slate-200">
                            <div className="flex items-center justify-between">
                                <label className="text-sm font-semibold text-gray-700">网络搜索</label>
                                <Switch
                                    checked={advancedDraft.webSearch}
                                    onCheckedChange={(checked) => setAdvancedDraft((prev) => ({ ...prev, webSearch: checked }))}
                                />
                            </div>
                            <p className="text-xs text-gray-600">允许模型查询网络以获取更新的事实。</p>
                        </div>

                        {/* Instructions */}
                        <div className="w-full sm:col-span-2 flex flex-col gap-2">
                            <label className="text-sm font-semibold text-gray-700">附加指令</label>
                            <p className="text-xs text-gray-500">为 AI 提供可选的指导。这些指令将覆盖除格式限制外的默认设置。</p>
                            <Textarea
                                value={advancedDraft.instructions}
                                rows={4}
                                onChange={(e) => setAdvancedDraft((prev) => ({ ...prev, instructions: e.target.value }))}
                                placeholder="例如：重点关注企业买家，强调投资回报率和安全合规性。保持幻灯片以数据驱动，避免使用行话，并在最后一页包含一个简短的行动号召（Call-to-action）。"
                                className="py-2 px-3 border-2 font-medium text-sm min-h-[100px] max-h-[200px] border-blue-200 focus-visible:ring-offset-0 focus-visible:ring-blue-300"
                            />
                        </div>
                    </div>

                    <DialogFooter>
                        <Button variant="outline" onClick={() => handleOpenAdvancedChange(false)}>取消</Button>
                        <Button onClick={handleSaveAdvanced} className="bg-[#5141e5] text-white hover:bg-[#5141e5]/90">保存</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
