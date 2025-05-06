from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DBSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="allow"
    )

    user: str = Field(..., validation_alias="DB_USER")
    password: str = Field(..., validation_alias="DB_PASS")
    host: str = Field(..., validation_alias="DB_HOST")
    port: int = Field(..., validation_alias="DB_PORT")
    dbname: str = Field(..., validation_alias="DB_NAME")

    @property
    def get_db_url(self) -> str:
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"


settings = DBSettings()
