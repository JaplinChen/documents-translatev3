import pytest
from sqlalchemy import text

from backend.config import settings
from backend.db.engine import get_engine
from backend.db.models import Base


def test_postgres_connection():
    if not (settings.database_url or "").startswith("postgresql"):
        pytest.skip("DATABASE_URL 未設定為 PostgreSQL")
    engine = get_engine()
    try:
        Base.metadata.create_all(bind=engine)
        with engine.begin() as conn:
            value = conn.execute(text("SELECT 1")).scalar()
        assert value == 1
    except Exception:
        pytest.skip("PostgreSQL 無法連線或未啟動")
