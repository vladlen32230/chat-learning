import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


def test_database_con_session_exception_handling():
    """Test get_session exception handling and rollback"""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_db_path = Path(temp_dir) / "test_exception.db"
        test_db_url = f"sqlite:///{test_db_path}"

        with patch.dict(os.environ, {"DATABASE_URL": test_db_url}):
            # Clear cached imports
            import sys

            if "src.database_con" in sys.modules:
                del sys.modules["src.database_con"]

            from src.database_con import get_session

            # Test exception handling
            with pytest.raises(Exception, match="Test exception"):
                with get_session():
                    # Force an exception to test rollback
                    raise Exception("Test exception")


def test_database_con_non_sqlite_url():
    """Test with non-SQLite DATABASE_URL to cover the if condition"""
    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test"}):
        # Clear cached imports
        import sys

        if "src.database_con" in sys.modules:
            del sys.modules["src.database_con"]

        # Import should work without directory creation
        from src.database_con import engine

        assert engine is not None
