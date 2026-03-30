# Linux 最小部署文件清单（手工上传版）

本文档用于你手工上传代码到 Linux 后，保证服务可以正常跑起来。

## 1. 目录结构约定

建议线上目录：

```text
/www/wwwroot/presenton
  ├─ app_data/
  ├─ servers/
  │   ├─ nextjs/
  │   └─ fastapi/
  └─ ...
```

## 2. 必须上传的文件与目录

只要要跑通你当前架构，至少上传这些：

1. `servers/nextjs/**`  
2. `servers/fastapi/**`  
3. `app_data/**`（至少保留目录结构，内容可为空）  
4. 根目录环境文件（按你项目实际）：
   - `.env`（如果你的后端/脚本依赖）
   - 或分别准备 `servers/nextjs/.env.production`、`servers/fastapi/.env`
5. 若你使用 SQLite 或本地文件存储，请一并上传对应数据文件（例如在 `app_data` 下）

## 3. 不需要上传的内容（可重建）

1. `servers/nextjs/node_modules`
2. `servers/nextjs/.next`、`.next-build`
3. Python 虚拟环境目录（如 `.venv`）
4. 本地临时目录（如 `temp_data`）
5. Git 相关目录（`.git`）和本地 IDE 配置

## 4. Next.js 必备运行条件

目录：`/www/wwwroot/presenton/servers/nextjs`

必须有：
1. `package.json`
2. `package-lock.json`（建议）
3. `next.config.mjs`
4. `app/**`
5. `components/**`
6. `public/**`

部署命令：

```bash
cd /www/wwwroot/presenton/servers/nextjs
npm ci
npm run build
npm run start
```

## 5. FastAPI 必备运行条件

目录：`/www/wwwroot/presenton/servers/fastapi`

必须有：
1. `api/**`
2. `services/**`
3. `models/**`
4. `utils/**`
5. `static/**`
6. `templates/**`
7. 依赖清单（`requirements.txt` 或你当前使用的安装方式）

部署命令（示例）：

```bash
cd /www/wwwroot/presenton/servers/fastapi
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python api/main.py --port 8000 --reload false
```

## 6. 必需环境变量（最低）

按当前代码，至少确认：

1. Next.js：
   - `CAN_CHANGE_KEYS`
   - `USER_CONFIG_PATH`
2. FastAPI：
   - `APP_DATA_DIRECTORY`（建议显式设置，避免路径漂移）
   - 你使用的模型 API Key（OpenAI/Anthropic/Doubao 等）

示例：

```bash
# Next.js
CAN_CHANGE_KEYS=true
USER_CONFIG_PATH=/www/wwwroot/presenton/app_data/user_config.json

# FastAPI
APP_DATA_DIRECTORY=/www/wwwroot/presenton/app_data
```

## 7. 启动顺序（建议）

1. 启动 FastAPI（`:8000`）
2. 启动 Next.js（`:3000`）
3. 最后 reload Nginx

## 8. 上线前自检

```bash
# FastAPI
curl -I http://127.0.0.1:8000/api/v1/ppt/presentation/all
curl -I http://127.0.0.1:8000/static/images/placeholder.jpg

# Next.js
curl -I http://127.0.0.1:3000/deck-studio
curl -I http://127.0.0.1:3000/api/v1/ppt/presentation/all
curl -I http://127.0.0.1:3000/deck-dashboard
```

## 9. 你当前路径命名约定（已改）

1. 上传页入口：`/deck-studio`
2. 控制台入口：`/deck-dashboard`
3. 兼容旧路径：
   - `/upload -> /deck-studio`
   - `/dashboard -> /deck-dashboard`

---

如果你希望，我可以再给你一份“只包含必须上传文件名（逐项 checklist）”版本，适合直接对照打包上传。
