# Template JSON Contract

This contract is the runtime input for FastAPI layout loading used by third-party PPT generation.

## File location

- Directory: `servers/fastapi/templates/`
- File name: `<group>.json` (for example `general.json`)

## JSON schema (runtime)

```json
{
  "version": "v1",
  "name": "general",
  "ordered": false,
  "slides": [
    {
      "id": "general:IntroSlideLayout",
      "name": "Intro Slide",
      "description": "Optional text",
      "json_schema": {}
    }
  ]
}
```

## Field rules

- `version`: required string. Current value: `v1`.
- `name`: required string; must match file name stem.
- `ordered`: optional boolean; defaults to `false`.
- `slides`: required array of slide layouts.
- `slides[].id`: required unique string in one group.
- `slides[].name`: optional string.
- `slides[].description`: optional string.
- `slides[].json_schema`: required JSON object.

## Compatibility

- FastAPI runtime model remains `PresentationLayoutModel` (`name`, `ordered`, `slides`).
- `version` is metadata for validation/traceability and is ignored by `PresentationLayoutModel` parsing.

