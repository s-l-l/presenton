import net from 'net'
import treeKill from 'tree-kill'
import fs from 'fs'
import { localhost, tempDir, userConfigPath } from './constants'

export function setUserConfig(userConfig: UserConfig) {
  let existingConfig: UserConfig = {}

  if (fs.existsSync(userConfigPath)) {
    const configData = fs.readFileSync(userConfigPath, 'utf-8')
    existingConfig = JSON.parse(configData)
  }
  const mergedConfig: UserConfig = {
    CAN_CHANGE_KEYS: userConfig.CAN_CHANGE_KEYS || existingConfig.CAN_CHANGE_KEYS,
    LLM: userConfig.LLM || existingConfig.LLM,
    OPENAI_API_KEY: userConfig.OPENAI_API_KEY || existingConfig.OPENAI_API_KEY,
    OPENAI_MODEL: userConfig.OPENAI_MODEL || existingConfig.OPENAI_MODEL,
    GOOGLE_API_KEY: userConfig.GOOGLE_API_KEY || existingConfig.GOOGLE_API_KEY,
    GOOGLE_MODEL: userConfig.GOOGLE_MODEL || existingConfig.GOOGLE_MODEL,
    ANTHROPIC_API_KEY: userConfig.ANTHROPIC_API_KEY || existingConfig.ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL: userConfig.ANTHROPIC_MODEL || existingConfig.ANTHROPIC_MODEL,
    DOUBAO_API_KEY: userConfig.DOUBAO_API_KEY || existingConfig.DOUBAO_API_KEY,
    DOUBAO_MODEL: userConfig.DOUBAO_MODEL || existingConfig.DOUBAO_MODEL,
    OLLAMA_URL: userConfig.OLLAMA_URL || existingConfig.OLLAMA_URL,
    OLLAMA_MODEL: userConfig.OLLAMA_MODEL || existingConfig.OLLAMA_MODEL,
    CUSTOM_LLM_URL: userConfig.CUSTOM_LLM_URL || existingConfig.CUSTOM_LLM_URL,
    CUSTOM_LLM_API_KEY: userConfig.CUSTOM_LLM_API_KEY || existingConfig.CUSTOM_LLM_API_KEY,
    CUSTOM_MODEL: userConfig.CUSTOM_MODEL || existingConfig.CUSTOM_MODEL,
    PEXELS_API_KEY: userConfig.PEXELS_API_KEY || existingConfig.PEXELS_API_KEY,
    PIXABAY_API_KEY: userConfig.PIXABAY_API_KEY || existingConfig.PIXABAY_API_KEY,
    IMAGE_PROVIDER: userConfig.IMAGE_PROVIDER || existingConfig.IMAGE_PROVIDER,
    DOUBAO_IMAGE_MODEL: userConfig.DOUBAO_IMAGE_MODEL || existingConfig.DOUBAO_IMAGE_MODEL,
    DISABLE_IMAGE_GENERATION: userConfig.DISABLE_IMAGE_GENERATION || existingConfig.DISABLE_IMAGE_GENERATION,
    EXTENDED_REASONING: userConfig.EXTENDED_REASONING || existingConfig.EXTENDED_REASONING,
    TOOL_CALLS: userConfig.TOOL_CALLS || existingConfig.TOOL_CALLS,
    DISABLE_THINKING: userConfig.DISABLE_THINKING || existingConfig.DISABLE_THINKING,
    WEB_GROUNDING: userConfig.WEB_GROUNDING || existingConfig.WEB_GROUNDING,
    DATABASE_URL: userConfig.DATABASE_URL || existingConfig.DATABASE_URL,
    DISABLE_ANONYMOUS_TRACKING: userConfig.DISABLE_ANONYMOUS_TRACKING || existingConfig.DISABLE_ANONYMOUS_TRACKING,
    COMFYUI_URL: userConfig.COMFYUI_URL || existingConfig.COMFYUI_URL,
    COMFYUI_WORKFLOW: userConfig.COMFYUI_WORKFLOW || existingConfig.COMFYUI_WORKFLOW,
    DALL_E_3_QUALITY: userConfig.DALL_E_3_QUALITY || existingConfig.DALL_E_3_QUALITY,
    GPT_IMAGE_1_5_QUALITY: userConfig.GPT_IMAGE_1_5_QUALITY || existingConfig.GPT_IMAGE_1_5_QUALITY,
    CODEX_MODEL: userConfig.CODEX_MODEL || existingConfig.CODEX_MODEL,
    CODEX_ACCESS_TOKEN: existingConfig.CODEX_ACCESS_TOKEN,
    CODEX_REFRESH_TOKEN: existingConfig.CODEX_REFRESH_TOKEN,
    CODEX_TOKEN_EXPIRES: existingConfig.CODEX_TOKEN_EXPIRES,
    CODEX_ACCOUNT_ID: existingConfig.CODEX_ACCOUNT_ID,
  }
  fs.writeFileSync(userConfigPath, JSON.stringify(mergedConfig))
}

export function getUserConfig(): UserConfig {
  if (!fs.existsSync(userConfigPath)) {
    return {}
  }
  const configData = fs.readFileSync(userConfigPath, 'utf-8')
  return JSON.parse(configData)
}

export function setupEnv(fastApiPort: number, nextjsPort: number) {
  process.env.NEXT_PUBLIC_FAST_API = `${localhost}:${fastApiPort}`;
  process.env.TEMP_DIRECTORY = tempDir;
  process.env.NEXT_PUBLIC_USER_CONFIG_PATH = userConfigPath;
  process.env.NEXT_PUBLIC_URL = `${localhost}:${nextjsPort}`;
  
  // Set environment variables for NextJS API routes
  process.env.USER_CONFIG_PATH = userConfigPath;
  // Read CAN_CHANGE_KEYS from existing env or default to true
  if (process.env.CAN_CHANGE_KEYS === undefined) {
    process.env.CAN_CHANGE_KEYS = "true";
  }
}


export function killProcess(pid: number, signal: NodeJS.Signals = "SIGTERM") {
  return new Promise((resolve, reject) => {
    treeKill(pid, signal, (err: any) => {
      if (err) {
        console.error(`Error killing process ${pid}:`, err)
        reject(err)
      } else {
        console.log(`Process ${pid} killed (${signal})`)
        resolve(true)
      }
    })
  })
}

export async function findUnusedPorts(startPort: number = 40000, count: number = 2): Promise<number[]> {
  const ports: number[] = [];
  console.log(`Finding ${count} unused ports starting from ${startPort}`);

  const isPortAvailable = (port: number): Promise<boolean> => {
    return new Promise((resolve) => {
      const server = net.createServer();
      server.once('error', () => {
        resolve(false);
      });
      server.once('listening', () => {
        server.close();
        resolve(true);
      });
      server.listen(port);
    });
  };

  let currentPort = startPort;
  while (ports.length < count) {
    if (await isPortAvailable(currentPort)) {
      ports.push(currentPort);
    }
    currentPort++;
  }

  return ports;
}


export function sanitizeFilename(filename: string): string {
  return filename.replace(/[\\/:*?"<>|]/g, '_');
}