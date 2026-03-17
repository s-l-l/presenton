import path from "path";

export const getIconFromFile = (file: string): string => {
  const file_ext = file.split(".").pop()?.toLowerCase() ?? "";
  if (file_ext == "pdf") {
    return "/pdf.svg";
  } else if (file_ext == "docx") {
    return "/report.png";
  } else if (file_ext == "pptx") {
    return "/ppt.svg";
  }
  return "/report.png";
};

export function isDarkColor(hex: any) {
  // Remove the hash symbol if it's there
  hex = hex.replace("#", "");

  // Convert 3-digit hex to 6-digit
  if (hex.length === 3) {
    hex = hex
      .split("")
      .map((char: any) => char + char)
      .join("");
  }

  // Parse r, g, b values
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);

  // Calculate relative luminance (per WCAG)
  const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;

  // Return true if luminance is below a threshold (dark color)
  return luminance < 128;
}

export function removeUUID(fileName: string) {
  const uuidLength = 36 + 5; // Length of the UUID
  const fileExtensionIndex = fileName.lastIndexOf("."); // Find the last index of file extension

  // Remove the last 36 characters before the file extension
  if (fileExtensionIndex !== -1) {
    return (
      fileName.slice(0, fileName.length - uuidLength) +
      fileName.slice(fileExtensionIndex)
    );
  }

  return fileName; // In case there's no extension
}








export function sanitizeFilename(input: string | null | undefined, replacement = '') {
  // Start with a safe base string to avoid calling string methods on null/undefined
  let sanitized = (input ?? '').toString();
  // Remove any null bytes first
  sanitized = sanitized.replace(/\0/g, '');
  
  // Remove or replace path traversal sequences
  sanitized = sanitized.replace(/\.\./g, replacement);
  
  // Regular filename sanitization (but preserve forward slashes for paths)
  // Modified to allow backslashes and colons for Windows paths
  const illegalRe = /[\?<>\|\*"]/g; 
  const controlRe = /[\x00-\x1f\x80-\x9f]/g;
  const reservedRe = /^\.+$/;
  const windowsReservedRe = /^(con|prn|aux|nul|com\d|lpt\d)$/i;
  const windowsTrailingRe = /[\. ]+$/;

  sanitized = sanitized
    .replace(illegalRe, replacement)
    .replace(controlRe, replacement);

  // Split path into segments to handle reserved names and trailing characters per segment
  // Handle both forward and backward slashes
  const pathSegments = sanitized.split(/[/\\]/);
  const cleanedSegments = pathSegments.map(segment => {
    // Skip checking drive letters (e.g. "C:")
    if (segment.match(/^[a-zA-Z]:$/)) {
      return segment;
    }

    let cleanSegment = segment
      .replace(reservedRe, replacement)
      .replace(windowsReservedRe, replacement)
      .replace(windowsTrailingRe, replacement);
    
    // Remove any remaining path traversal attempts in individual segments
    cleanSegment = cleanSegment.replace(/\.\./g, replacement);
    
    return cleanSegment;
  });

  // Reconstruct path using original separators if possible, or forward slashes
  // Since we split by both, we might lose the original separator info.
  // A safer bet for cross-platform Node.js is to use path.join/normalize later,
  // but here we just want to return the sanitized string.
  // For Windows paths, we need to be careful not to double-sanitize backslashes.
  
  return cleanedSegments.join('/'); 
}


export function getStaticFileUrl(filepath: string): string {
  const pathParts = filepath.split('/');
  const relevantPath = pathParts.slice(2).join('/');
  return path.join("/static", relevantPath);
}