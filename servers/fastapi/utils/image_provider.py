from enums.image_provider import ImageProvider
import json
import os
from pathlib import Path
from utils.get_env import (
    get_doubao_api_key_env,
    get_doubao_image_model_env,
    get_disable_image_generation_env,
    get_image_provider_env,
    get_llm_provider_env,
    get_user_config_path_env,
)
from utils.parsers import parse_bool_or_none


def is_image_generation_disabled() -> bool:
    return parse_bool_or_none(get_disable_image_generation_env()) or False


def is_pixels_selected() -> bool:
    return ImageProvider.PEXELS == get_selected_image_provider()


def is_pixabay_selected() -> bool:
    return ImageProvider.PIXABAY == get_selected_image_provider()


def is_gemini_flash_selected() -> bool:
    return ImageProvider.GEMINI_FLASH == get_selected_image_provider()


def is_nanobanana_pro_selected() -> bool:
    return ImageProvider.NANOBANANA_PRO == get_selected_image_provider()


def is_dalle3_selected() -> bool:
    return ImageProvider.DALLE3 == get_selected_image_provider()


def is_gpt_image_1_5_selected() -> bool:
    return ImageProvider.GPT_IMAGE_1_5 == get_selected_image_provider()


def is_comfyui_selected() -> bool:
    return ImageProvider.COMFYUI == get_selected_image_provider()


def is_doubao_image_selected() -> bool:
    return ImageProvider.DOUBAO == get_selected_image_provider()


def get_selected_image_provider() -> ImageProvider | None:
    """
    Get the selected image provider from environment variables.
    Returns:
        ImageProvider: The selected image provider.
    """
    image_provider_env = get_image_provider_env()
    print(
        "get_selected_image_provider: "
        f"IMAGE_PROVIDER={image_provider_env}, "
        f"LLM={get_llm_provider_env()}, "
        f"DOUBAO_API_KEY_SET={bool(get_doubao_api_key_env())}, "
        f"DOUBAO_IMAGE_MODEL={get_doubao_image_model_env()}"
    )
    if image_provider_env:
        try:
            provider = ImageProvider(image_provider_env.strip().lower())
            print(f"get_selected_image_provider: selected from env -> {provider.value}")
            return provider
        except Exception:
            print(
                "get_selected_image_provider: invalid IMAGE_PROVIDER="
                f"{image_provider_env}"
            )
            return None

    # Fallback to persisted user config when env sync middleware is skipped or delayed.
    user_config_path = get_user_config_path_env()
    if not user_config_path:
        # Local fallback path when USER_CONFIG_PATH env is not provided.
        repo_user_config = Path.cwd().parent.parent / "app_data" / "user-config.json"
        if repo_user_config.exists():
            user_config_path = str(repo_user_config)
    print(
        "get_selected_image_provider: "
        f"USER_CONFIG_PATH={user_config_path}, "
        f"exists={bool(user_config_path and os.path.exists(user_config_path))}"
    )
    if user_config_path and os.path.exists(user_config_path):
        try:
            with open(user_config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f) or {}
            raw_provider = user_config.get("IMAGE_PROVIDER")
            print(
                "get_selected_image_provider: "
                f"IMAGE_PROVIDER from user config={raw_provider}"
            )
            if isinstance(raw_provider, str) and raw_provider.strip():
                provider = ImageProvider(raw_provider.strip().lower())
                print(
                    f"get_selected_image_provider: selected from user config -> {provider.value}"
                )
                return provider
        except Exception as e:
            print(f"get_selected_image_provider: failed reading user config: {e}")

    # Fallback: if LLM is Doubao and Doubao image config exists, prefer Doubao image provider.
    llm_provider_env = (get_llm_provider_env() or "").strip().lower()
    if llm_provider_env == "doubao" and get_doubao_api_key_env():
        print("get_selected_image_provider: selected from doubao fallback -> doubao")
        return ImageProvider.DOUBAO
    print("get_selected_image_provider: final -> None")
    return None
