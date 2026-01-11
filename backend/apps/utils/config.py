import secrets
from pathlib import Path
from typing import Annotated, Any, Literal

import yaml
from pydantic import (
    AnyUrl,
    BeforeValidator,
    PostgresDsn,
    computed_field,
    Field,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


def load_yaml_config() -> dict[str, Any]:
    """Load configuration from etc/config.yaml file.
    
    Returns:
        Dictionary with configuration data, or empty dict if file not found.
    """
    config_path = Path(__file__).parent.parent.parent / "etc" / "config.yaml"
    if config_path.exists():
        print(f"Loading configuration from {config_path}")
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )
    PROJECT_NAME: str = Field(default="Terra AIOps Platform")
    API_V1_STR: str = Field(default="/api/v1")
    
    HTTP_HOST: str = Field(default="0.0.0.0")
    HTTP_PORT: int = Field(default=7082)

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = Field(default=[])

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS]

    POSTGRES_SERVER: str = Field(default="172.17.1.227")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_USER: str = Field(default="root")
    POSTGRES_PASSWORD: str = Field(default="Dms123@pg")
    POSTGRES_DB: str = Field(default="terra-aiops")
    TERRA_DB_URL: str = Field(default="")

    LOG_LEVEL: str = Field(default="INFO")  # DEBUG, INFO, WARNING, ERROR
    LOG_DIR: str = Field(default="logs")
    LOG_FORMAT: str = Field(default="%(asctime)s - %(name)s - %(levelname)s:%(lineno)d - %(message)s")
    SQL_DEBUG: bool = Field(default=False)

    NEO4J_URL: str = Field(default="bolt://172.17.1.227:7687")
    NEO4J_USER: str = Field(default="neo4j")
    NEO4J_PASSWORD: str = Field(default="dms123!!")

    PG_POOL_SIZE: int = Field(default=20)
    PG_MAX_OVERFLOW: int = Field(default=30)
    PG_POOL_RECYCLE: int = Field(default=3600)
    PG_POOL_PRE_PING: bool = Field(default=True)

    # Cache Configuration
    CACHE_TYPE: str = Field(default="memory")  # memory or redis
    CACHE_MAX_SIZE: int = Field(default=1000)  # For memory cache
    CACHE_REDIS_HOST: str = Field(default="localhost")
    CACHE_REDIS_PORT: int = Field(default=6379)
    CACHE_REDIS_DB: int = Field(default=0)
    CACHE_REDIS_PASSWORD: str = Field(default="")
    CACHE_REDIS_SOCKET_TIMEOUT: int = Field(default=5)
    CACHE_REDIS_SOCKET_CONNECT_TIMEOUT: int = Field(default=5)
    CACHE_REDIS_SERIALIZER: str = Field(default="json")  # json or pickle

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Settings with YAML config file and environment variables.
        
        Priority (highest to lowest):
        1. Explicitly passed arguments
        2. Environment variables
        3. YAML configuration file
        4. Default values
        """
        yaml_config = load_yaml_config()
        merged_config = self._merge_configs(yaml_config, kwargs)
        super().__init__(**merged_config)

    @staticmethod
    def _merge_configs(yaml_config: dict[str, Any], explicit_kwargs: dict[str, Any]) -> dict[str, Any]:
        """Merge YAML config with explicit kwargs, respecting environment variables.
        
        Priority: explicit_kwargs > yaml_config
        Environment variables are already handled by pydantic-settings.
        """
        merged = {}
        
        # Map yaml config keys to Settings field names
        yaml_mapping = {
            "project_name": "PROJECT_NAME",
            "api_v1_str": "API_V1_STR",
            "http_host": "HTTP_HOST",
            "http_port": "HTTP_PORT",
            "backend_cors_origins": "BACKEND_CORS_ORIGINS",
            "postgres": None,  # Handled separately
            "neo4j": None,  # Handled separately
            "logging": None,  # Handled separately
            "cache": None,  # Handled separately
        }
        
        # Process simple mappings from YAML
        for yaml_key, field_name in yaml_mapping.items():
            if field_name and yaml_key in yaml_config and yaml_key not in explicit_kwargs:
                merged[field_name] = yaml_config[yaml_key]
        
        # Process postgres config
        if "postgres" in yaml_config and "postgres" not in explicit_kwargs:
            pg_config = yaml_config["postgres"]
            if "url" in pg_config and not explicit_kwargs.get("TERRA_DB_URL"):
                merged["TERRA_DB_URL"] = pg_config["url"]
            if "server" in pg_config:
                merged["POSTGRES_SERVER"] = pg_config["server"]
            if "port" in pg_config:
                merged["POSTGRES_PORT"] = pg_config["port"]
            if "user" in pg_config:
                merged["POSTGRES_USER"] = pg_config["user"]
            if "password" in pg_config:
                merged["POSTGRES_PASSWORD"] = pg_config["password"]
            if "db" in pg_config:
                merged["POSTGRES_DB"] = pg_config["db"]
            if "pool_size" in pg_config:
                merged["PG_POOL_SIZE"] = pg_config["pool_size"]
            if "max_overflow" in pg_config:
                merged["PG_MAX_OVERFLOW"] = pg_config["max_overflow"]
            if "pool_recycle" in pg_config:
                merged["PG_POOL_RECYCLE"] = pg_config["pool_recycle"]
            if "pool_pre_ping" in pg_config:
                merged["PG_POOL_PRE_PING"] = pg_config["pool_pre_ping"]
        
        # Process neo4j config
        if "neo4j" in yaml_config and "neo4j" not in explicit_kwargs:
            neo4j_config = yaml_config["neo4j"]
            if "url" in neo4j_config:
                merged["NEO4J_URL"] = neo4j_config["url"]
            if "user" in neo4j_config:
                merged["NEO4J_USER"] = neo4j_config["user"]
            if "password" in neo4j_config:
                merged["NEO4J_PASSWORD"] = neo4j_config["password"]
        
        # Process logging config
        if "logging" in yaml_config and "logging" not in explicit_kwargs:
            log_config = yaml_config["logging"]
            if "level" in log_config:
                merged["LOG_LEVEL"] = log_config["level"]
            if "dir" in log_config:
                merged["LOG_DIR"] = log_config["dir"]
            if "format" in log_config:
                merged["LOG_FORMAT"] = log_config["format"]
            if "sql_debug" in log_config:
                merged["SQL_DEBUG"] = log_config["sql_debug"]
        
        # Process cache config
        if "cache" in yaml_config and "cache" not in explicit_kwargs:
            cache_config = yaml_config["cache"]
            if "type" in cache_config:
                merged["CACHE_TYPE"] = cache_config["type"]
            if "max_size" in cache_config:
                merged["CACHE_MAX_SIZE"] = cache_config["max_size"]
            if "host" in cache_config:
                merged["CACHE_REDIS_HOST"] = cache_config["host"]
            if "port" in cache_config:
                merged["CACHE_REDIS_PORT"] = cache_config["port"]
            if "db" in cache_config:
                merged["CACHE_REDIS_DB"] = cache_config["db"]
            if "password" in cache_config:
                merged["CACHE_REDIS_PASSWORD"] = cache_config["password"] or ""
            if "socket_timeout" in cache_config:
                merged["CACHE_REDIS_SOCKET_TIMEOUT"] = cache_config["socket_timeout"]
            if "socket_connect_timeout" in cache_config:
                merged["CACHE_REDIS_SOCKET_CONNECT_TIMEOUT"] = cache_config["socket_connect_timeout"]
            if "serializer" in cache_config:
                merged["CACHE_REDIS_SERIALIZER"] = cache_config["serializer"]
        
        # Add explicit kwargs (these take precedence)
        merged.update(explicit_kwargs)
        
        return merged

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn | str:
        if self.TERRA_DB_URL:
            return self.TERRA_DB_URL
        return MultiHostUrl.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )
    
    def get_cache_config(self) -> dict[str, Any]:
        """Get cache configuration as a dictionary."""
        return {
            "type": self.CACHE_TYPE,
            "max_size": self.CACHE_MAX_SIZE,
            "host": self.CACHE_REDIS_HOST,
            "port": self.CACHE_REDIS_PORT,
            "db": self.CACHE_REDIS_DB,
            "password": self.CACHE_REDIS_PASSWORD,
            "socket_timeout": self.CACHE_REDIS_SOCKET_TIMEOUT,
            "socket_connect_timeout": self.CACHE_REDIS_SOCKET_CONNECT_TIMEOUT,
            "serializer": self.CACHE_REDIS_SERIALIZER,
        }

    def get_graph_db_config(self) -> dict[str, Any]:
        """Get Neo4j graph database configuration as a dictionary."""
        return {
            "uri": self.NEO4J_URL,
            "username": self.NEO4J_USER,
            "password": self.NEO4J_PASSWORD,
        }


settings = Settings()  # type: ignore
