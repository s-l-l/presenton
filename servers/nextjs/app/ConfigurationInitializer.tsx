'use client';

import { useEffect, useState } from 'react';
import { setCanChangeKeys, setLLMConfig } from '@/store/slices/userConfig';
import { hasValidLLMConfig } from '@/utils/storeHelpers';
import { usePathname, useRouter } from 'next/navigation';
import { useDispatch } from 'react-redux';
import { checkIfSelectedOllamaModelIsPulled } from '@/utils/providerUtils';
import { LLMConfig } from '@/types/llm_config';

export function ConfigurationInitializer({ children }: { children: React.ReactNode }) {
  const dispatch = useDispatch();

  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const route = usePathname();

  // Fetch user config state
  useEffect(() => {
    fetchUserConfigState();
  }, []);

  const setLoadingToFalseAfterNavigatingTo = (pathname: string) => {
    const target = pathname.endsWith('/') && pathname !== '/' ? pathname.slice(0, -1) : pathname;
    const normalize = (value: string) => (value.endsWith('/') && value !== '/' ? value.slice(0, -1) : value);
    const startedAt = Date.now();
    const interval = setInterval(() => {
      const current = normalize(window.location.pathname);
      const matched = current === target || current.endsWith(target);
      const timedOut = Date.now() - startedAt > 2500;
      if (matched || timedOut) {
        clearInterval(interval);
        setIsLoading(false);
      }
    }, 100);
  }

  const fetchJsonWithTimeout = async (url: string, options?: RequestInit, timeoutMs = 8000) => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(url, { ...options, signal: controller.signal });
      return await response.json();
    } finally {
      clearTimeout(timer);
    }
  };

  const fetchUserConfigState = async () => {
    const normalizedRoute = route?.endsWith('/') && route !== '/' ? route.slice(0, -1) : route;
    const bypassInitRoutes = [
      '/pdf-maker',
      '/ppt/pdf-maker',
    ];
    const shouldBypassInitialization = bypassInitRoutes.some((bypassRoute) =>
      normalizedRoute === bypassRoute || normalizedRoute?.startsWith(`${bypassRoute}/`)
    );

    if (shouldBypassInitialization) {
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      const canChangeKeys = (await fetchJsonWithTimeout('/api/can-change-keys')).canChange;
      dispatch(setCanChangeKeys(canChangeKeys));

      if (canChangeKeys) {
        const llmConfig = await fetchJsonWithTimeout('/api/user-config');
        if (!llmConfig.LLM) {
          llmConfig.LLM = 'openai';
        }
        if (!llmConfig.IMAGE_PROVIDER) {
          llmConfig.IMAGE_PROVIDER = 'gpt-image-1.5';
        }
        dispatch(setLLMConfig(llmConfig));
        const isValid = hasValidLLMConfig(llmConfig);
        if (isValid) {
          // Check if the selected Ollama model is pulled
          if (llmConfig.LLM === 'ollama') {
            const isPulled = await checkIfSelectedOllamaModelIsPulled(llmConfig.OLLAMA_MODEL);
            if (!isPulled) {
              router.push('/ppt');
              setLoadingToFalseAfterNavigatingTo('/ppt');
              return;
            }
          }
          if (llmConfig.LLM === 'custom') {
            const isAvailable = await checkIfSelectedCustomModelIsAvailable(llmConfig);
            if (!isAvailable) {
              router.push('/ppt');
              setLoadingToFalseAfterNavigatingTo('/ppt');
              return;
            }
          }
          if (route === '/' || route === '/ppt' || route === '/ppt/') {
            router.push('/ppt/deck-studio');
            setLoadingToFalseAfterNavigatingTo('/deck-studio');
          } else {
            setIsLoading(false);
          }
        } else if (route !== '/' && route !== '/ppt' && route !== '/ppt/') {
          router.push('/ppt');
          setLoadingToFalseAfterNavigatingTo('/ppt');
        } else {
          setIsLoading(false);
        }
      } else {
        if (route === '/' || route === '/ppt' || route === '/ppt/') {
          router.push('/ppt/deck-studio');
          setLoadingToFalseAfterNavigatingTo('/deck-studio');
        } else {
          setIsLoading(false);
        }
      }
    } catch (error) {
      console.error('Error during app initialization:', error);
      setIsLoading(false);
    }
  }


  const checkIfSelectedCustomModelIsAvailable = async (llmConfig: LLMConfig) => {
    try {
      const response = await fetch('/api/v1/ppt/openai/models/available', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: llmConfig.CUSTOM_LLM_URL,
          api_key: llmConfig.CUSTOM_LLM_API_KEY,
        }),
      });
      const data = await response.json();
      return data.includes(llmConfig.CUSTOM_MODEL);
    } catch (error) {
      console.error('Error fetching custom models:', error);
      return false;
    }
  }


  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#E9E8F8] via-[#F5F4FF] to-[#E0DFF7] flex items-center justify-center p-4">
        <div className="max-w-md w-full">
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-8 text-center">
            {/* Logo/Branding */}
            <div className="mb-6">
              <img
                src="/Logo.png"
                alt="PresentOn"
                className="h-12 mx-auto mb-4 opacity-90"
              />
              <div className="w-16 h-1 bg-gradient-to-r from-blue-500 to-purple-600 mx-auto rounded-full"></div>
            </div>

            {/* Loading Text */}
            <div className="space-y-2">
              <h3 className="text-lg font-semibold text-gray-800 font-inter">
                正在初始化应用
              </h3>
              <p className="text-sm text-gray-600 font-inter">
                正在加载配置并检查模型可用性...
              </p>
            </div>

            {/* Progress Indicator */}
            <div className="mt-6">
              <div className="flex space-x-1 justify-center">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return children;
}
