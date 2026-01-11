#!/usr/bin/env python3
"""Test script to verify Settings configuration loading from YAML."""

import sys
from pathlib import Path

# # Add backend to path
# sys.path.insert(0, str(Path(__file__).parent))

from apps.utils.config import settings

def test_settings():
    """Test that settings are loaded correctly."""
    print("=" * 60)
    print("Testing Settings Configuration")
    print("=" * 60)
    
    # Test basic settings
    print(f"\nBasic Settings:")
    print(f"  PROJECT_NAME: {settings.PROJECT_NAME}")
    print(f"  API_V1_STR: {settings.API_V1_STR}")
    
    # Test PostgreSQL settings
    print(f"\nPostgreSQL Settings:")
    print(f"  POSTGRES_SERVER: {settings.POSTGRES_SERVER}")
    print(f"  POSTGRES_PORT: {settings.POSTGRES_PORT}")
    print(f"  POSTGRES_USER: {settings.POSTGRES_USER}")
    print(f"  POSTGRES_DB: {settings.POSTGRES_DB}")
    print(f"  PG_POOL_SIZE: {settings.PG_POOL_SIZE}")
    print(f"  PG_MAX_OVERFLOW: {settings.PG_MAX_OVERFLOW}")
    print(f"  PG_POOL_RECYCLE: {settings.PG_POOL_RECYCLE}")
    print(f"  PG_POOL_PRE_PING: {settings.PG_POOL_PRE_PING}")
    
    # Test Neo4j settings
    print(f"\nNeo4j Settings:")
    print(f"  NEO4J_URL: {settings.NEO4J_URL}")
    print(f"  NEO4J_USER: {settings.NEO4J_USER}")
    
    # Test logging settings
    print(f"\nLogging Settings:")
    print(f"  LOG_LEVEL: {settings.LOG_LEVEL}")
    print(f"  LOG_DIR: {settings.LOG_DIR}")
    print(f"  SQL_DEBUG: {settings.SQL_DEBUG}")
    
    # Test computed field
    print(f"\nComputed Fields:")
    print(f"  SQLALCHEMY_DATABASE_URI: {settings.SQLALCHEMY_DATABASE_URI}")
    
    print(f"\nCORS Origins:")
    print(f"  all_cors_origins: {settings.all_cors_origins}")
    
    print("\n" + "=" * 60)
    print("✓ Settings loaded successfully from YAML config!")
    print("=" * 60)

if __name__ == "__main__":
    test_settings()
