from pydantic import BaseModel
from pyaml_env import parse_config


class Settings(BaseModel):
    class PyrisSettings(BaseModel):
        api_key: str
        llm: dict

    pyris: PyrisSettings


settings = Settings.parse_obj(parse_config("application.yml"))
