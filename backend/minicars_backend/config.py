from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "minicars-control-station-backend"


settings = Settings()


