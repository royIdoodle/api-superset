#!/usr/bin/env python3
import sys
from pathlib import Path

# 确保可以导入 app.*
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pymysql
from sqlalchemy import create_engine

from app.config import get_settings
from app.database import Base


def create_database_if_not_exists() -> None:
    settings = get_settings()
    conn = pymysql.connect(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        database="mysql",
        charset="utf8mb4",
        autocommit=True,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{settings.MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
    finally:
        conn.close()


def create_tables() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_uri, future=True, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)


def main() -> None:
    print("[db-init] Creating database if not exists...")
    create_database_if_not_exists()
    print("[db-init] Creating tables...")
    create_tables()
    print("[db-init] Done.")


if __name__ == "__main__":
    main()


