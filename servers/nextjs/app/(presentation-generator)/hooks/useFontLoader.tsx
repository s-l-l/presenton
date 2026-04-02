
export const useFontLoader = ( fonts:string[]) => {
    const injectFonts = (fontUrls: string[]) => {
        fontUrls.forEach((fontUrl) => {
          if (!fontUrl) return;
          let newFontUrl = fontUrl;
          if (!fontUrl.includes('fonts.googleapis') && !fontUrl.startsWith('http')) {
            const baseUrl = typeof window !== 'undefined' ? window.location.origin : '';
            newFontUrl = `${baseUrl}${fontUrl}`;
          }
          const existingStyle = document.querySelector(`style[data-font-url="${newFontUrl}"]`);
          if (existingStyle) return;
          const style = document.createElement("style");
          style.setAttribute("data-font-url", newFontUrl);
          style.textContent = `@import url('${newFontUrl}');`;
          document.head.appendChild(style);
        });
      };
      injectFonts(fonts);
};