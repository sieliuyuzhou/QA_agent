import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.database import DatabaseManager
from infrastructure.models import init_tables


def main() -> int:
    load_dotenv()
    db = DatabaseManager(os.getenv("CONVERSATION_DB_URL", ""))
    try:
        init_tables(db)
        print("[SUCCESS] PostgreSQL schema initialized.")
        return 0
    finally:
        db.close_all()


if __name__ == "__main__":
    raise SystemExit(main())
