import os


def get_can_change_keys_env():
    return os.getenv("CAN_CHANGE_KEYS")


def get_database_url_env():
    return os.getenv("DATABASE_URL")


def get_app_data_directory_env():
    return os.getenv("APP_DATA_DIRECTORY")


def get_temp_directory_env():
    return os.getenv("TEMP_DIRECTORY")


def get_user_config_path_env():
    return os.getenv("USER_CONFIG_PATH")


def get_container_db_path_env():
    return os.getenv("CONTAINER_DB_PATH")


def get_llm_provider_env():
    return os.getenv("LLM")


def get_anthropic_api_key_env():
    return os.getenv("ANTHROPIC_API_KEY")


def get_anthropic_model_env():
    return os.getenv("ANTHROPIC_MODEL")


def get_doubao_api_key_env():
    return os.getenv("DOUBAO_API_KEY")


def get_doubao_model_env():
    return os.getenv("DOUBAO_MODEL")


def get_ollama_url_env():
    return os.getenv("OLLAMA_URL")


def get_custom_llm_url_env():
    return os.getenv("CUSTOM_LLM_URL")


def get_openai_api_key_env():
    return os.getenv("OPENAI_API_KEY")


def get_openai_model_env():
    return os.getenv("OPENAI_MODEL")


def get_google_api_key_env():
    return os.getenv("GOOGLE_API_KEY")


def get_google_model_env():
    return os.getenv("GOOGLE_MODEL")


def get_custom_llm_api_key_env():
    return os.getenv("CUSTOM_LLM_API_KEY")


def get_ollama_model_env():
    return os.getenv("OLLAMA_MODEL")


def get_custom_model_env():
    return os.getenv("CUSTOM_MODEL")


def get_pexels_api_key_env():
    return os.getenv("PEXELS_API_KEY")


def get_disable_image_generation_env():
    return os.getenv("DISABLE_IMAGE_GENERATION")


def get_image_provider_env():
    return os.getenv("IMAGE_PROVIDER")


def get_doubao_image_model_env():
    return os.getenv("DOUBAO_IMAGE_MODEL")


def get_pixabay_api_key_env():
    return os.getenv("PIXABAY_API_KEY")


def get_tool_calls_env():
    return os.getenv("TOOL_CALLS")


def get_disable_thinking_env():
    return os.getenv("DISABLE_THINKING")


def get_extended_reasoning_env():
    return os.getenv("EXTENDED_REASONING")


def get_web_grounding_env():
    return os.getenv("WEB_GROUNDING")


def get_comfyui_url_env():
    return os.getenv("COMFYUI_URL")


def get_comfyui_workflow_env():
    return os.getenv("COMFYUI_WORKFLOW")


def get_nextjs_api_base_url_env():
    return os.getenv("NEXTJS_API_BASE_URL")


def get_template_source_env():
    return os.getenv("TEMPLATE_SOURCE")


def get_template_remote_fallback_env():
    return os.getenv("TEMPLATE_REMOTE_FALLBACK")


def get_template_preload_env():
    return os.getenv("TEMPLATE_CACHE_PRELOAD")


def get_template_local_dir_env():
    return os.getenv("TEMPLATE_LOCAL_DIR")


# Dalle 3 Quality
def get_dall_e_3_quality_env():
    return os.getenv("DALL_E_3_QUALITY")


# Gpt Image 1.5 Quality
def get_gpt_image_1_5_quality_env():
    return os.getenv("GPT_IMAGE_1_5_QUALITY")


# Codex OAuth
def get_codex_access_token_env():
    return os.getenv("CODEX_ACCESS_TOKEN")


def get_codex_refresh_token_env():
    return os.getenv("CODEX_REFRESH_TOKEN")


def get_codex_token_expires_env():
    return os.getenv("CODEX_TOKEN_EXPIRES")


def get_codex_account_id_env():
    return os.getenv("CODEX_ACCOUNT_ID")


def get_codex_model_env():
    return os.getenv("CODEX_MODEL")


def get_migrate_database_on_startup_env():
    return os.getenv("MIGRATE_DATABASE_ON_STARTUP")


def get_slide_to_html_model_env():
    return os.getenv("SLIDE_TO_HTML_MODEL")
