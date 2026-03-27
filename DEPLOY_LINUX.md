# Presenton Linux 手动部署文档

## 一、服务器环境要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Ubuntu 20.04+ / Debian 11+ / CentOS 8+ |
| Python | 3.11（必须，不支持 3.12+） |
| Node.js | 20.x |
| 内存 | 建议 4GB+ |
| 磁盘 | 建议 10GB+ |

## 二、系统依赖安装（Ubuntu/Debian）

```bash
# 更新系统
sudo apt-get update && sudo apt-get upgrade -y

# 安装基础工具
sudo apt-get install -y curl wget git build-essential fontconfig zstd

# 安装 Nginx
sudo apt-get install -y nginx

# 安装 LibreOffice（PPT 导出需要）
sudo apt-get install -y libreoffice

# 安装 Chromium（截图/PDF 导出需要）
sudo apt-get install -y chromium-browser
# 如果是 Debian：sudo apt-get install -y chromium
```

### 2.1 安装 Python 3.11

```bash
sudo apt-get install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip

# 验证
python3.11 --version
```

### 2.2 安装 Node.js 20

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# 验证
node --version   # v20.x.x
npm --version
```

## 三、部署目录规划

```
/opt/presenton/              # 项目代码
/opt/presenton/app_data/     # 持久化数据（数据库、图片、导出文件、字体等）
/tmp/presenton/              # 临时文件
```

```bash
sudo mkdir -p /opt/presenton
sudo mkdir -p /opt/presenton/app_data
sudo mkdir -p /tmp/presenton

# 设置权限（假设用 presenton 用户运行）
sudo useradd -r -s /bin/false presenton
sudo chown -R presenton:presenton /opt/presenton
sudo chown -R presenton:presenton /tmp/presenton
```

## 四、上传代码

将项目代码上传到 `/opt/presenton/`，确保目录结构如下：

```
/opt/presenton/
├── servers/
│   ├── fastapi/
│   └── nextjs/
├── start.js
├── nginx.conf
└── ...
```

## 五、安装 FastAPI 后端依赖

```bash
cd /opt/presenton/servers/fastapi

# 方式一：使用 pip 直接安装（推荐生产环境）
pip3.11 install alembic aiohttp aiomysql aiosqlite asyncpg \
    "fastapi[standard]" pathvalidate pdfplumber chromadb sqlmodel \
    anthropic google-genai openai fastmcp dirtyjson nltk \
    python-pptx redis "volcengine-python-sdk[ark]" python-dotenv

# 安装 docling（使用 CPU 版 PyTorch）
pip3.11 install docling --extra-index-url https://download.pytorch.org/whl/cpu

# 方式二：使用 uv（如果已安装 uv）
pip3.11 install uv
uv sync
```

## 六、安装并构建 Next.js 前端

```bash
cd /opt/presenton/servers/nextjs

# 安装依赖
npm install

# 构建生产版本
npm run build
```

构建成功后会生成 `.next-build/` 目录。

## 七、环境变量配置

在 `/opt/presenton/` 下创建 `.env` 文件：

```bash
cat > /opt/presenton/.env << 'EOF'
# ========== 路径配置 ==========
APP_DATA_DIRECTORY=/opt/presenton/app_data
TEMP_DIRECTORY=/tmp/presenton
USER_CONFIG_PATH=/opt/presenton/app_data/userConfig.json
PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser
# Debian 上可能是 /usr/bin/chromium

# ========== Next.js 配置 ==========
NEXTJS_API_BASE_URL=http://127.0.0.1:3000

# ========== 模板配置 ==========
TEMPLATE_SOURCE=local
TEMPLATE_REMOTE_FALLBACK=false
TEMPLATE_CACHE_PRELOAD=true

# ========== 数据库配置 ==========
# 默认 SQLite，无需配置。如需 PostgreSQL/MySQL，取消注释：
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/presenton
# DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/presenton
MIGRATE_DATABASE_ON_STARTUP=true

# ========== LLM 配置（按需选择一个） ==========
# --- OpenAI ---
# LLM=openai
# OPENAI_API_KEY=sk-xxx
# OPENAI_MODEL=gpt-4.1

# --- Google Gemini ---
# LLM=google
# GOOGLE_API_KEY=xxx
# GOOGLE_MODEL=gemini-2.0-flash

# --- Anthropic Claude ---
# LLM=anthropic
# ANTHROPIC_API_KEY=xxx
# ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# --- Ollama（本地模型） ---
# LLM=ollama
# OLLAMA_URL=http://127.0.0.1:11434
# OLLAMA_MODEL=llama3

# --- 自定义 OpenAI 兼容接口 ---
# LLM=custom
# CUSTOM_LLM_URL=https://your-api-endpoint/v1
# CUSTOM_LLM_API_KEY=xxx
# CUSTOM_MODEL=your-model-name

# --- 豆包 ---
# LLM=doubao
# DOUBAO_API_KEY=xxx
# DOUBAO_MODEL=doubao-seed-2-0-lite-260215

# ========== 图片生成配置（按需选择） ==========
# IMAGE_PROVIDER=pexels
# PEXELS_API_KEY=xxx
# PIXABAY_API_KEY=xxx

# ========== 其他 ==========
LOG_LEVEL=info
ACCESS_LOG=true
WEB_GROUNDING=false
DISABLE_ANONYMOUS_TRACKING=true
EOF
```

同时需要将 `.env` 复制一份到 FastAPI 目录（FastAPI 使用 `dotenv` 从当前目录加载）：

```bash
cp /opt/presenton/.env /opt/presenton/servers/fastapi/.env
```

Next.js 也需要环境变量，创建 `/opt/presenton/servers/nextjs/.env.local`：

```bash
cat > /opt/presenton/servers/nextjs/.env.local << 'EOF'
APP_DATA_DIRECTORY=/opt/presenton/app_data
TEMP_DIRECTORY=/tmp/presenton
USER_CONFIG_PATH=/opt/presenton/app_data/userConfig.json
PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser
NEXTJS_API_BASE_URL=http://127.0.0.1:3000
TEMPLATE_SOURCE=local
TEMPLATE_REMOTE_FALLBACK=false
TEMPLATE_CACHE_PRELOAD=true
EOF
```

## 八、Nginx 配置

```bash
sudo cat > /etc/nginx/sites-available/presenton << 'NGINX'
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名或 IP

    client_max_body_size 100M;

    # Next.js 前端
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 30m;
        proxy_connect_timeout 30m;
    }

    # FastAPI 后端 API
    location /api/v1/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_read_timeout 30m;
        proxy_connect_timeout 30m;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # MCP 服务
    location /mcp/ {
        proxy_pass http://127.0.0.1:8001/mcp/;
        proxy_read_timeout 30m;
        proxy_connect_timeout 30m;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /mcp {
        proxy_pass http://127.0.0.1:8001/mcp;
        proxy_read_timeout 30m;
        proxy_connect_timeout 30m;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # FastAPI Swagger 文档
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_read_timeout 30m;
        proxy_connect_timeout 30m;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
        proxy_read_timeout 30m;
        proxy_connect_timeout 30m;
    }

    # 静态文件
    location /static {
        alias /opt/presenton/servers/fastapi/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /app_data/images/ {
        alias /opt/presenton/app_data/images/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /app_data/exports/ {
        alias /opt/presenton/app_data/exports/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /app_data/uploads/ {
        alias /opt/presenton/app_data/uploads/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /app_data/fonts/ {
        alias /opt/presenton/app_data/fonts/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
NGINX

# 启用站点
sudo ln -sf /etc/nginx/sites-available/presenton /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 测试并重载
sudo nginx -t
sudo systemctl reload nginx
```

## 九、Systemd 服务配置

### 9.1 FastAPI 服务

```bash
sudo cat > /etc/systemd/system/presenton-fastapi.service << 'EOF'
[Unit]
Description=Presenton FastAPI Backend
After=network.target

[Service]
Type=simple
User=presenton
Group=presenton
WorkingDirectory=/opt/presenton/servers/fastapi
EnvironmentFile=/opt/presenton/.env
ExecStart=/usr/bin/python3.11 -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --log-level info
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

### 9.2 MCP 服务（可选）

```bash
sudo cat > /etc/systemd/system/presenton-mcp.service << 'EOF'
[Unit]
Description=Presenton MCP Server
After=presenton-fastapi.service

[Service]
Type=simple
User=presenton
Group=presenton
WorkingDirectory=/opt/presenton/servers/fastapi
EnvironmentFile=/opt/presenton/.env
ExecStart=/usr/bin/python3.11 mcp_server.py --port 8001
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

### 9.3 Next.js 服务

```bash
sudo cat > /etc/systemd/system/presenton-nextjs.service << 'EOF'
[Unit]
Description=Presenton Next.js Frontend
After=presenton-fastapi.service

[Service]
Type=simple
User=presenton
Group=presenton
WorkingDirectory=/opt/presenton/servers/nextjs
EnvironmentFile=/opt/presenton/.env
ExecStart=/usr/bin/npm run start -- -H 127.0.0.1 -p 3000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

### 9.4 启动所有服务

```bash
sudo systemctl daemon-reload

# 启用开机自启
sudo systemctl enable presenton-fastapi
sudo systemctl enable presenton-mcp
sudo systemctl enable presenton-nextjs
sudo systemctl enable nginx

# 启动服务（按顺序）
sudo systemctl start presenton-fastapi
sudo systemctl start presenton-mcp
sudo systemctl start presenton-nextjs
sudo systemctl start nginx

# 查看状态
sudo systemctl status presenton-fastapi
sudo systemctl status presenton-nextjs
```

## 十、与 DataAgent 前端集成注意事项

DataAgent 前端通过 **iframe** 嵌入 Presenton，有以下关键问题需要处理：

### 10.1 端口硬编码问题（重要）

DataAgent 前端的 `PptEditorShell.vue` 中 **硬编码了 Presenton 端口为 3000**：

```javascript
// data-agent-frontend/src/views/PptEditorShell.vue 第 43-47 行
const presentonBaseUrl = computed(() => {
  const protocol = window.location.protocol;
  const host = window.location.hostname;
  return `${protocol}//${host}:3000`;  // 硬编码 3000
});
```

**这意味着：**
- 如果 Presenton 通过 Nginx 代理在 80 端口对外，DataAgent 前端仍会尝试直连 3000 端口
- **必须确保 3000 端口对外可访问**，或者修改此处代码为 Nginx 代理端口

**已实施方案 B：通过环境变量配置 Presenton 地址**

`PptEditorShell.vue` 已修改为支持 `VITE_PRESENTON_BASE_URL` 环境变量。
默认使用 `${protocol}//${host}`（即 80 端口），不再硬编码 3000。

DataAgent 前端部署时，在 `.env` 中配置：
```bash
# 如果 Presenton 通过 Nginx 部署在 80 端口（同一台服务器）
VITE_PRESENTON_BASE_URL=http://your-server-ip

# 如果 Presenton 部署在其他服务器或自定义端口
VITE_PRESENTON_BASE_URL=http://presenton-server:8080
```

### 10.2 跨域配置

Presenton FastAPI 已配置全局 CORS `allow_origins=["*"]`，无需额外配置。

但 iframe 嵌入还需要注意：
- 如果 DataAgent 和 Presenton 部署在 **不同域名/端口** 下，`postMessage` 通信已正确使用 origin 校验，可以正常工作
- 如果后续添加了 `X-Frame-Options` 或 CSP 头，需确保允许 DataAgent 域名嵌入

### 10.3 DataAgent 后端代理

DataAgent 后端（端口 8065）会代理 PPT 相关 API 请求到 Presenton FastAPI 的 `/api/v1/ppt/third-party/*` 接口。部署时需要：

- 确认 DataAgent 后端配置中 Presenton FastAPI 的地址正确
- 如果两个服务在同一台服务器：`http://127.0.0.1:8000`
- 如果在不同服务器：`http://<presenton-server-ip>:8000`（需开放 8000 端口或走 Nginx）

### 10.4 端口总览

| 服务 | 端口 | 监听地址 | 说明 |
|------|------|----------|------|
| Nginx | 80 | 0.0.0.0 | Presenton 统一入口 |
| Next.js | 3000 | 127.0.0.1 | Presenton 前端（默认仅本地） |
| FastAPI | 8000 | 127.0.0.1 | Presenton 后端 API |
| MCP Server | 8001 | 127.0.0.1 | MCP 协议服务 |
| DataAgent 前端 | 3001 | 0.0.0.0 | DataAgent UI |
| DataAgent 后端 | 8065 | - | DataAgent API |

### 10.5 推荐部署架构（同一台服务器）

```
用户浏览器
    │
    ├──→ DataAgent 前端 (:3001)
    │       │
    │       ├── /api/* ──→ DataAgent 后端 (:8065)
    │       │                  │
    │       │                  └── /api/v1/ppt/third-party/* ──→ Presenton FastAPI (:8000)
    │       │
    │       └── iframe ──→ Presenton Next.js (:3000 或 Nginx :80)
    │
    └──→ Presenton Nginx (:80)
            ├── / ──→ Next.js (:3000)
            ├── /api/v1/ ──→ FastAPI (:8000)
            └── /static, /app_data/* ──→ 静态文件
```

## 十一、防火墙配置

```bash
# Presenton 对外端口
sudo ufw allow 80/tcp       # Nginx（必须）

# 如果 DataAgent 在同一台服务器
sudo ufw allow 3001/tcp     # DataAgent 前端
sudo ufw allow 8065/tcp     # DataAgent 后端

# 不建议对外开放
# 3000/tcp  Next.js（通过 Nginx 代理，无需直连）
# 8000/tcp  FastAPI（通过 Nginx 代理）
# 8001/tcp  MCP Server（通过 Nginx 代理）
```

## 十二、验证部署

```bash
# 1. 检查服务状态
sudo systemctl status presenton-fastapi
sudo systemctl status presenton-nextjs
sudo systemctl status nginx

# 2. 测试 FastAPI
curl http://127.0.0.1:8000/docs

# 3. 测试 Next.js
curl -I http://127.0.0.1:3000

# 4. 测试 Nginx 代理
curl -I http://127.0.0.1:80
curl http://127.0.0.1:80/api/v1/ppt/

# 5. 外部访问测试
curl http://<服务器公网IP>/
```

## 十三、日志查看

```bash
# FastAPI 日志
sudo journalctl -u presenton-fastapi -f

# Next.js 日志
sudo journalctl -u presenton-nextjs -f

# Nginx 日志
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

## 十四、常见问题

### Q: Chromium 路径找不到
不同发行版 Chromium 路径不同：
- Ubuntu: `/usr/bin/chromium-browser`
- Debian: `/usr/bin/chromium`
- 通过 snap 安装: `/snap/bin/chromium`

用 `which chromium-browser || which chromium` 确认后更新 `.env` 中的 `PUPPETEER_EXECUTABLE_PATH`。

### Q: LibreOffice 路径
一般为 `/usr/bin/soffice`，如果需要显式指定，在 `.env` 中添加：
```
LIBREOFFICE_EXECUTABLE=/usr/bin/soffice
```

### Q: 数据库迁移失败
手动执行迁移：
```bash
cd /opt/presenton/servers/fastapi
python3.11 -m alembic upgrade head
```

### Q: npm run build 内存不足
增加 Node.js 内存限制：
```bash
NODE_OPTIONS="--max-old-space-size=4096" npm run build
```
