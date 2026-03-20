from typing import Optional
from pydantic import BaseModel


class ImagePrompt(BaseModel):
    prompt: str
    theme_prompt: Optional[str] = None

    def get_image_prompt(self, with_theme: bool = False) -> str:
        if not with_theme:
            return self.prompt
        if self.theme_prompt and self.theme_prompt.strip():
            return f"{self.prompt}, {self.theme_prompt}"
        return self.prompt
