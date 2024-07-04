from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    posts_db_name: str = "posts"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    other_params: str = ""


settings = Settings()
