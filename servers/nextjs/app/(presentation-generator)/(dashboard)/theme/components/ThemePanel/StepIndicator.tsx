import React from 'react'

interface StepIndicatorProps {
  currentStep: number
}

const steps = [
  { step: 1, label: '品牌' },
  { step: 2, label: '调色板' },
  { step: 3, label: '字体' },
  { step: 4, label: '徽标' },
]

export const StepIndicator: React.FC<StepIndicatorProps> = ({ currentStep }) => (
  <div className="flex flex-col items-center gap-7 px-4 min-w-[104px] pt-8 border-r border-[#EDEEEF]">
    {steps.map(({ step, label }) => {
      const isActive = currentStep === step
      return (
        <div key={step} className="flex flex-col items-center gap-1.5 px-3  ">
          <span
            className={`px-2 py-0.5 rounded-full text-[9px] font-medium ${isActive
              ? 'bg-[#7A5AF8] text-white'
              : 'bg-white text-[#404348] border border-[#EDEEEF]'
              }`}
          >
            第 {step} 步
          </span>
          <span className="text-[11px] font-normal text-black">{label}</span>
        </div>
      )
    })}
  </div>
)
