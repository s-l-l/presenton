import { net } from "electron";
import { app, BrowserWindow } from "electron";
import { isDev } from "./constants";

/**
 * Version check URL — GitHub raw version.json (no API required).
 * Override with UPDATE_SERVER_URL for local testing.
 */
const VERSION_JSON_URL =
  process.env.UPDATE_SERVER_URL ||
  "https://raw.githubusercontent.com/presenton/presenton/refs/heads/main/electron/version.json";

const CURRENT_VERSION = app.getVersion();

/** Maximum number of fetch attempts (polls). */
const MAX_ATTEMPTS = 3;

/** Wait 2 minutes after load before first poll (10s in dev for testing). */
const INITIAL_DELAY_MS = isDev ? 10 * 1_000 : 2 * 60 * 1_000;

/** 1 minute between poll attempts (5s in dev for testing). */
const POLL_INTERVAL_MS = isDev ? 5 * 1_000 : 1 * 60 * 1_000;

/** Short delay before injecting banner to allow React/Next.js to mount. */
const INJECT_DELAY_MS = isDev ? 500 : 1_000;

function log(msg: string): void {
  const line = `[UpdateChecker] ${msg}\n`;
  process.stderr.write(line);
  console.log(`[UpdateChecker] ${msg}`);
}

interface VersionResponse {
  version: string;
  downloads: {
    linux: string;
    mac: string;
    windows: string;
  };
}

function getDownloadUrlForPlatform(downloads: VersionResponse["downloads"]): string {
  const platform = process.platform;
  if (platform === "darwin") return downloads.mac;
  if (platform === "win32") return downloads.windows;
  return downloads.linux;
}

/**
 * Simple semver comparison that strips pre-release labels for numeric comparison.
 * Returns true if `remote` is strictly newer than `current`.
 */
function isNewerVersion(current: string, remote: string): boolean {
  const toNumbers = (v: string) =>
    v
      .replace(/[^0-9.]/g, "")
      .split(".")
      .map(Number);

  const curr = toNumbers(current);
  const rem = toNumbers(remote);
  const len = Math.max(curr.length, rem.length);

  for (let i = 0; i < len; i++) {
    const c = curr[i] ?? 0;
    const r = rem[i] ?? 0;
    if (r > c) return true;
    if (r < c) return false;
  }
  return false;
}

async function fetchVersionInfo(): Promise<VersionResponse | null> {
  try {
    log(`Fetching ${VERSION_JSON_URL}...`);
    const response = await net.fetch(VERSION_JSON_URL, {
      method: "GET",
      headers: { "User-Agent": `Presenton/${CURRENT_VERSION}` },
    });
    if (!response.ok) {
      log(`Fetch failed: HTTP ${response.status}`);
      return null;
    }
    const data = (await response.json()) as VersionResponse;
    log(`Fetched version: ${data.version}`);
    return data;
  } catch (err) {
    log(`Fetch error: ${err}`);
    return null;
  }
}

/** Pending update to re-inject on navigation (production: React/Next.js may replace DOM). */
let pendingUpdate: { version: string; downloadUrl: string } | null = null;

/**
 * Schedules banner injection after INJECT_DELAY_MS so React/Next.js can mount first.
 * In production (.deb), the DOM may not be ready when did-finish-load fires.
 */
function scheduleBannerInjection(
  win: BrowserWindow,
  version: string,
  downloadUrl: string
): void {
  pendingUpdate = { version, downloadUrl };
  setTimeout(() => {
    if (win.isDestroyed() || !pendingUpdate) return;
    log(`Injecting banner now`);
    injectUpdateBanner(win, pendingUpdate.version, pendingUpdate.downloadUrl);
  }, INJECT_DELAY_MS);
}

/**
 * Injects a Cursor-style update banner at the bottom of the renderer window.
 * Safe to call multiple times; a second call while the banner is visible is a no-op.
 */
function injectUpdateBanner(
  win: BrowserWindow,
  latest: string,
  downloadUrl: string,
  releaseNotes?: string
): void {
  const notesHtml = releaseNotes
    ? `<span style="color:#a6adc8;margin-right:8px;">${releaseNotes}</span>`
    : "";

  const script = /* js */ `
    (function () {
      if (document.getElementById('__presenton_update_banner__')) return;

      const banner = document.createElement('div');
      banner.id = '__presenton_update_banner__';
      banner.style.cssText = [
        'position:fixed',
        'bottom:0',
        'left:0',
        'right:0',
        'background:#1e1e2e',
        'color:#cdd6f4',
        'display:flex',
        'align-items:center',
        'justify-content:space-between',
        'padding:10px 18px',
        'font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif',
        'font-size:13px',
        'z-index:2147483647',
        'border-top:1px solid #313244',
        'box-shadow:0 -4px 16px rgba(0,0,0,0.35)',
        'gap:12px',
      ].join(';');

      banner.innerHTML = \`
        <span style="display:flex;align-items:center;gap:8px;flex:1;min-width:0;">
          <span style="font-size:16px;">✨</span>
          <span>
            Presenton&nbsp;<strong>${latest}</strong>&nbsp;is available
            &mdash;&nbsp;you have&nbsp;<strong>${CURRENT_VERSION}</strong>
          </span>
          ${notesHtml}
        </span>
        <div style="display:flex;gap:8px;align-items:center;flex-shrink:0;">
          <a
            href="${downloadUrl}"
            target="_blank"
            style="color:#89b4fa;text-decoration:none;border:1px solid #89b4fa;padding:4px 14px;border-radius:5px;font-size:12px;white-space:nowrap;"
          >Download update</a>
          <button
            onclick="document.getElementById('__presenton_update_banner__').remove()"
            title="Dismiss"
            style="background:none;border:none;color:#6c7086;cursor:pointer;font-size:20px;line-height:1;padding:0 2px;"
          >&times;</button>
        </div>
      \`;

      document.body.appendChild(banner);
    })();
  `;

  win.webContents.executeJavaScript(script).catch((err) => {
    log(`Banner injection failed: ${err}`);
  });
}

/**
 * Polls for version info up to MAX_ATTEMPTS times with 1 min between attempts.
 * Stops as soon as a successful response is received or all attempts are exhausted.
 */
async function checkForUpdatesWithRetry(win: BrowserWindow): Promise<void> {
  log(`Starting check (current: ${CURRENT_VERSION})`);
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    if (win.isDestroyed()) {
      log("Window destroyed, aborting");
      return;
    }

    log(`Attempt ${attempt}/${MAX_ATTEMPTS}`);
    const data = await fetchVersionInfo();

    if (data) {
      const newer = isNewerVersion(CURRENT_VERSION, data.version);
      log(`Remote ${data.version} vs current ${CURRENT_VERSION} -> newer? ${newer}`);
      if (newer) {
        const downloadUrl = getDownloadUrlForPlatform(data.downloads);
        log(`Injecting banner for ${data.version} (after ${INJECT_DELAY_MS}ms delay)`);
        scheduleBannerInjection(win, data.version, downloadUrl);
      } else {
        log("No update needed, skipping banner");
      }
      return;
    }

    // Wait 1 minute before the next poll (skip delay after the last attempt)
    if (attempt < MAX_ATTEMPTS) {
      log(`Next poll in ${POLL_INTERVAL_MS / 1_000}s...`);
      await new Promise<void>((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
    }
  }
  log("All attempts failed, no update info");
}

/**
 * Starts the update checker.
 * Waits 2 minutes after load, then polls 3 times with 1 min interval.
 * Re-injects banner on every navigation (handles Next.js client routing).
 */
export function startUpdateChecker(win: BrowserWindow): void {
  log("Registered, waiting for did-finish-load");
  let hasRunCheck = false;

  const onLoad = () => {
    if (pendingUpdate) {
      log("did-finish-load (navigation), re-injecting banner");
      scheduleBannerInjection(win, pendingUpdate.version, pendingUpdate.downloadUrl);
    } else if (!hasRunCheck) {
      hasRunCheck = true;
      log(`did-finish-load fired, first poll in ${INITIAL_DELAY_MS / 1_000}s`);
      setTimeout(() => {
        if (win.isDestroyed()) return;
        checkForUpdatesWithRetry(win);
      }, INITIAL_DELAY_MS);
    }
  };

  if (!win.webContents.isLoading()) {
    log(`Page already loaded, first poll in ${INITIAL_DELAY_MS / 1_000}s`);
    hasRunCheck = true;
    setTimeout(() => {
      if (win.isDestroyed()) return;
      checkForUpdatesWithRetry(win);
    }, INITIAL_DELAY_MS);
  }
  win.webContents.on("did-finish-load", onLoad);
}

export function stopUpdateChecker(): void {
  pendingUpdate = null;
}
