# Nginx 部署配置说明（ai.cqxqkj.com.cn）

本文档给出当前项目可用的 Nginx 生产配置，目标是：
- 主前端 `data_agent` 走根路径 `/`
- PPT 子系统（Next.js）挂在 `/ppt`
- FastAPI 走 `/api/v1`
- DataAgent 后端走 `/api`
- `app_data` 静态目录可直接访问

## 1. 完整配置示例

> 证书路径、根目录、端口请按你的机器实际路径确认。

```nginx
server {
    listen 80;
    server_name ai.cqxqkj.com.cn;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ai.cqxqkj.com.cn;

    ssl_certificate     /www/server/panel/vhost/cert/ai.cqxqkj.com.cn/fullchain.pem;
    ssl_certificate_key /www/server/panel/vhost/cert/ai.cqxqkj.com.cn/privkey.pem;

    # 主前端（data_agent）
    root /www/wwwroot/data_agent/web;
    index index.html;

    # Presenton Next.js（挂到 /ppt）
    location /ppt/ {
        proxy_pass http://127.0.0.1:3000/ppt/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # /ppt 自动跳到新入口
    location = /ppt {
        return 301 /ppt/deck-studio;
    }

    # Presenton FastAPI
    location /api/v1/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_read_timeout 1800s;
        proxy_connect_timeout 1800s;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # DataAgent 后端
    location /api/ {
        proxy_pass http://127.0.0.1:8065;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 本地静态目录
    location /app_data/ {
        alias /www/wwwroot/presenton/app_data/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # SPA fallback（data_agent）
    location / {
        try_files $uri $uri/ /index.html;
    }

    access_log /www/wwwlogs/ai_access.log;
    error_log  /www/wwwlogs/ai_error.log;
}
```

## 2. 必须满足的约束

1. `server_name ai.cqxqkj.com.cn` 只能有一套有效站点配置（80/443 各一段）。
2. 不要再让其他 `*.conf` 里重复定义同域名，否则会命中错误站点。
3. Next.js 生产入口为：
   - `https://ai.cqxqkj.com.cn/ppt/deck-studio`

## 3. 上线与校验命令

```bash
nginx -t
nginx -s reload
nginx -T | grep -n "server_name ai.cqxqkj.com.cn"
```

期望结果：
- `nginx -t` 成功
- 同域名只出现当前这套配置

## 4. 常见问题排查

### 4.1 跳到别的项目登录页
- 原因：同域名重复 `server` 块，命中了别的站点。
- 处理：删掉重复站点定义，只保留唯一配置。

### 4.2 `/api/v1/*` 返回 404
- 原因：FastAPI 没启动或 Nginx `/api/v1/` 没转发到 `8000`。
- 处理：确认 FastAPI 进程和端口，再检查 `location /api/v1/`。

### 4.3 图片 CORS 或外链过期
- 现已通过后端代理和本地化兜底处理。
- 仍异常时先重启 FastAPI，再重新生成图片。

## 5. 建议的服务端口对照

- `3000`：Presenton Next.js
- `8000`：Presenton FastAPI
- `8065`：DataAgent 后端

---

如果后续你要拆分域名（例如把 PPT 独立成 `ppt.xxx.com`），建议再出一版“多域名配置”，避免路径耦合。
