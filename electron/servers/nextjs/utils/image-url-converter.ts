import { getFastAPIUrl } from "./api";

function toFastApiStaticUrl(fileSrc: string): string {
  try {
    const baseUrl = getFastAPIUrl();
    const url = new URL(fileSrc);
    const path = url.pathname;

    // Prefer subpath starting at /app_data or /static if present
    const appDataIdx = path.indexOf("/app_data/");
    const staticIdx = path.indexOf("/static/");

    let relPath = path;
    if (appDataIdx !== -1) {
      relPath = path.slice(appDataIdx);
    } else if (staticIdx !== -1) {
      relPath = path.slice(staticIdx);
    }

    return `${baseUrl}${relPath}`;
  } catch {
    // If URL parsing fails, leave as-is
    return fileSrc;
  }
}

export function normalizeImageSrc(src: string): string {
  // If already an absolute HTTP(S) URL, prefer FastAPI origin for /app_data and /static
  if (/^https?:\/\//.test(src)) {
    try {
      const url = new URL(src);
      if (url.pathname.startsWith("/app_data/") || url.pathname.startsWith("/static/")) {
        return `${getFastAPIUrl()}${url.pathname}`;
      }
      return src;
    } catch {
      return src;
    }
  }

  // If we have a file:// URL, map it to FastAPI static HTTP URL
  if (src.startsWith("file://")) {
    return toFastApiStaticUrl(src);
  }

  // Safe fallback for bare paths: treat as file URL, then map to FastAPI
  const trimmed = src.trim();
  const fileLike = trimmed.startsWith("/") ? `file://${trimmed}` : `file:///${trimmed}`;
  return toFastApiStaticUrl(fileLike);
}

/**
 * Normalizes image URLs so that non-protocol paths are treated as file URLs.
 * If the src is already http/https/file, it is left unchanged.
 */
export function convertImageUrlsForEnvironment() {
  if (typeof document === "undefined") return;

  const images = document.querySelectorAll("img[src]");

  images.forEach((img) => {
    const htmlImg = img as HTMLImageElement;
    if (!htmlImg.src) return;
    htmlImg.src = normalizeImageSrc(htmlImg.src);
  });
}

/**
 * Setup a MutationObserver to automatically convert any dynamically added images
 */
export function setupImageUrlConverter() {
  convertImageUrlsForEnvironment();
  
  // Watch for dynamically added images
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType === Node.ELEMENT_NODE) {
          const element = node as Element;
          
          // Any new <img> or descendants with src should be normalized
          if (element.tagName === "IMG") {
            convertImageUrlsForEnvironment();
          }
          
          const imgs = element.querySelectorAll?.("img[src]");
          if (imgs && imgs.length > 0) {
            convertImageUrlsForEnvironment();
          }
        }
      });
    });
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });
  
  return observer;
}
