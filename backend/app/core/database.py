from __future__ import annotations

from sqlalchemy import Engine, create_engine, event, select
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


def create_database_engine(database_url: str) -> Engine:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, connect_args=connect_args, future=True)
    if database_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def configure_sqlite(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.close()
    return engine


def initialize_database(engine: Engine) -> None:
    from app import models  # noqa: F401
    from app.models.schema_metadata import SchemaMetadata

    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        for schema_version in ("ot009-import", "ot010-analysis", "ot011-semantic", "ot012-proposals"):
            existing = session.scalar(select(SchemaMetadata).where(SchemaMetadata.schema_version == schema_version))
            if existing is None:
                session.add(SchemaMetadata(schema_version=schema_version))
        session.commit()
