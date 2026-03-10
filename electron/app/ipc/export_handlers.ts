import { ipcMain } from "electron";
import { appDataDir, baseDir, downloadsDir, tempDir } from "../utils/constants";
import fs from "fs";
import path from "path";

import { showFileDownloadedDialog } from "../utils/dialog";
import { v4 as uuidv4 } from 'uuid';
import { spawn } from "child_process";

export function setupExportHandlers() {
  ipcMain.handle("file-downloaded", async (_, filePath: string): Promise<IPCStatus> => {
    const fileName = path.basename(filePath);
    const destinationPath = path.join(downloadsDir, fileName);

    await fs.promises.rename(filePath, destinationPath);
    const success = await showFileDownloadedDialog(destinationPath);
    return { success };
  });

  ipcMain.handle("export-presentation", async (_, id: string, title: string, exportAs: "pptx" | "pdf" | "png") => {
    try {
      const pptUrl = `${process.env.NEXT_PUBLIC_URL}/pdf-maker?id=${id}`;

      let exportTask = {
        type: "export",
        url: pptUrl,
        format: exportAs,
        title: title,
      }

      const randomUuid = uuidv4();
      const exportTempDir = path.join(tempDir, randomUuid);
      await fs.promises.mkdir(exportTempDir, { recursive: true });

      const exportTaskPath = path.join(exportTempDir, "export_task.json");
      await fs.promises.writeFile(exportTaskPath, JSON.stringify(exportTask));

      const exportScriptPath = path.join(baseDir, "resources", "export", "index.js");
      const pythonModulePath = path.join(baseDir, "resources", "export", "py", "convert");
      const exportTaskProcess = spawn("node", [exportScriptPath, exportTaskPath], {
        stdio: ["ignore", "pipe", "pipe"],
        env: {
          ...process.env,
          TEMP_DIRECTORY: tempDir,
          APP_DATA_DIRECTORY: appDataDir,
          BUILT_PYTHON_MODULE_PATH: pythonModulePath,
        },
      });

      exportTaskProcess.stdout.on("data", (data: Buffer) => {
        console.log(`[Export] ${data.toString()}`);
      });
      exportTaskProcess.stderr.on("data", (data: Buffer) => {
        console.error(`[Export] ${data.toString()}`);
      });

      await new Promise<void>((resolve, reject) => {
        exportTaskProcess.on("error", reject);
        exportTaskProcess.on("exit", (code) => {
          if (code === 0) {
            resolve();
          } else {
            reject(new Error(`Export process exited with code ${code}`));
          }
        });
      });

      const responsePath = exportTaskPath.replace(".json", ".response.json");
      const responseRaw = await fs.promises.readFile(responsePath, "utf8");
      const responseData = JSON.parse(responseRaw);
      const exportFilePath = resolveExportedFilePath(responseData);

      if (!exportFilePath) {
        return { success: false, message: "Export finished but output file was not found." };
      }

      const destinationPath = path.join(downloadsDir, path.basename(exportFilePath));
      await moveFile(exportFilePath, destinationPath);
      const success = await showFileDownloadedDialog(destinationPath);
      return { success, message: success ? "Export completed." : "Export completed but dialog failed." };
    } catch (error: any) {
      console.error("[Export] Error exporting presentation:", error);
      return { success: false, message: error?.message ?? "Export failed." };
    }
  })

}

function resolveExportedFilePath(responseData: any): string | null {
  if (responseData?.path && typeof responseData.path === "string") {
    return path.isAbsolute(responseData.path)
      ? responseData.path
      : path.join(appDataDir, responseData.path);
  }

  if (responseData?.url && typeof responseData.url === "string") {
    try {
      const parsed = new URL(responseData.url);
      if (parsed.protocol === "file:") {
        const filePath = decodeURIComponent(parsed.pathname);
        if (process.platform === "win32" && filePath.startsWith("/")) {
          return filePath.slice(1);
        }
        return filePath;
      }
    } catch {
      return null;
    }
  }

  return null;
}

async function moveFile(sourcePath: string, destinationPath: string) {
  try {
    await fs.promises.rename(sourcePath, destinationPath);
  } catch (error: any) {
    if (error?.code !== "EXDEV") {
      throw error;
    }
    await fs.promises.copyFile(sourcePath, destinationPath);
    await fs.promises.unlink(sourcePath);
  }
}