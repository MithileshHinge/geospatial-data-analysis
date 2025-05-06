from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8")

    s3_bucket: str = Field(..., validation_alias="S3_BUCKET")
    s3_endpoint: str | None = Field(None, validation_alias="S3_ENDPOINT")
    region: str = Field("us-east-1", validation_alias="AWS_REGION")
    dl_concurrency: int = Field(5, validation_alias="DL_CONCURRENCY")
    scrape_search_concurrency: int = Field(
        10, validation_alias="SCRAPE_SEARCH_CONCURRENCY"
    )

    @field_validator("s3_endpoint")
    @classmethod
    def validate_s3_endpoint(cls, v: str | None) -> str | None:
        if v == "":
            return None
        return v


settings = Settings()
