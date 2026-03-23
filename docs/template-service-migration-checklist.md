# Template Service Migration Checklist

- [x] 1. Define template JSON contract (fields, version, directory rules)
- [x] 2. Add Next.js build script to export templates to `servers/fastapi/templates/`
- [x] 3. Generate and commit default template artifacts (`general/modern/standard/swift/...`)
- [x] 4. Refactor FastAPI `get_layout_by_name` to use local templates as primary source
- [x] 5. Add FastAPI template preload and in-memory cache
- [x] 6. Add remote fallback switch in FastAPI (disabled by default for production)
- [x] 7. Add/align config and `.env` examples (`TEMPLATE_SOURCE`, etc.)
- [x] 8. Add template source observability in dataAgent logs (`template_source=...`)
- [x] 9. Verify compatibility for `/third-party/generate`, `/build`, `/build/stream`
- [x] 10. Update deployment docs to remove runtime dependency on Next.js/Chromium
- [x] 11. Document rollback switch and operation steps
