from sqlmodel import create_engine, Session
import os
from typing import Generator
from contextlib import contextmanager

engine = create_engine(os.environ['DATABASE_URL'])

@contextmanager
def get_session() -> Generator[Session, None, None]:
    session = Session(engine)
    try:
        yield session
    except Exception as e:
        session.rollback()
        raise e
    else:
        session.commit()
    finally:
        session.close()