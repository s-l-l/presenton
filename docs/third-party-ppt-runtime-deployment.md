# Third-Party PPT Runtime Deployment

## Runtime chain (recommended)

- `data-agent-management` (3001) -> `presenton fastapi` (8000)
- Runtime no longer requires `nextjs` (3000) or Chromium when using local templates.

## Required runtime components

- FastAPI service (`servers/fastapi`)
- Template artifacts in `servers/fastapi/templates/*.json`

## Template source configuration

- `TEMPLATE_SOURCE=local` (recommended for production)
- `TEMPLATE_CACHE_PRELOAD=true` (recommended)
- `TEMPLATE_REMOTE_FALLBACK=false` (recommended for stable low-latency runtime)
- Optional:
  - `TEMPLATE_LOCAL_DIR=/custom/path/to/templates`
  - `NEXTJS_API_BASE_URL=http://127.0.0.1:3000` (only used for remote mode/fallback)

## Export/update templates (build-time operation)

From `servers/nextjs`:

```bash
npm run export:templates
```

This generates JSON artifacts into `servers/fastapi/templates`.

## Rollback switches

If local template artifacts are invalid/missing and you need temporary rollback:

1. Set `TEMPLATE_SOURCE=remote`
2. Set `TEMPLATE_REMOTE_FALLBACK=true`
3. Ensure Next.js `3000` and Puppeteer environment are available
4. Restart FastAPI

## Observability hints

- FastAPI logs preload event:
  - `template.local.preload_done loaded=<n> dir=<path>`
- dataAgent outbound logs include:
  - `template_source=<value>`

