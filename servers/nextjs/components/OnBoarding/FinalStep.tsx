import { ArrowRight } from 'lucide-react'
import { usePathname, useRouter } from 'next/navigation'
import React from 'react'
import { trackEvent, MixpanelEvent } from "@/utils/mixpanel";

const FinalStep = () => {
    const router = useRouter()
    const pathname = usePathname()
    const handleGoToDashboard = () => {
        trackEvent(MixpanelEvent.Navigation, { from: pathname, to: "/dashboard" });
        router.push('/dashboard')
    }
    const handleGoToUpload = () => {
        trackEvent(MixpanelEvent.Navigation, { from: pathname, to: "/upload" });
        router.push('/upload')
    }
    return (
        <div className='fixed top-0 left-0 w-full h-full flex flex-col items-center justify-center'>
            <div className='flex flex-col items-center justify-center'>

                <img src="/final_onboarding.png" alt="presenton" className='w-[118px] h-[98px]  object-contain' />
                <h1 className='text-black text-[30px] font-normal font-unbounded py-2.5'>欢迎加入！</h1>
                <p className='text-[#000000CC] text-xl font-normal font-syne'>您的 AI 工作区已准备就绪。让我们开始创建您的第一份演示文稿吧。</p>
                <button onClick={handleGoToUpload} className='bg-[#7C51F8] px-[23px] mt-14 py-[15px]  rounded-[70px] text-white text-lg font-syne font-semibold'>我的第一份演示文稿</button>
            </div>
            <button onClick={handleGoToDashboard} className='absolute bottom-20 text-[#7A5AF8] flex items-center gap-2 right-10  text-xs font-normal font-syne'>前往控制台 <ArrowRight className='w-4 h-4 text-[#7A5AF8]' /></button>
        </div>
    )
}

export default FinalStep
