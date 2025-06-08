from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlmodel import Session, create_engine
from src.config_settings import DATABASE_URL

# Ensure database directory exists for SQLite
db_path = DATABASE_URL.replace("sqlite:///", "")
db_dir = Path(db_path).parent
db_dir.mkdir(parents=True, exist_ok=True)

engine = create_engine(DATABASE_URL)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    session = Session(engine)
    try:
        yield session
    except Exception as e:
        session.rollback()
        raise e
    else:  # pragma: no cover
        session.commit()
    finally:
        session.close()
