from enum import Enum


class LLMProvider(Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    GOOGLE = "google"
    ANTHROPIC = "anthropic"
    DOUBAO = "doubao"
    CUSTOM = "custom"
    CODEX = "codex"
