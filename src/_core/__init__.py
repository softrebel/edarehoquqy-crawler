from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from .logging import *  # noqa: F403
from .schemas import *  # noqa: F403


class Configs(BaseSettings):
    OUTPUT_PATH: str | None = None

    model_config = SettingsConfigDict(env_file=".env")


project_configs = Configs()


if project_configs.OUTPUT_PATH and not os.path.exists(project_configs.OUTPUT_PATH):
    os.makedirs(project_configs.OUTPUT_PATH)
