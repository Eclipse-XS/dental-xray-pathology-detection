import sys
from pathlib import Path

DEPLOYMENT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DEPLOYMENT_ROOT / "src"))

from dental_xray_service.core.config import get_settings  # noqa: E402
from dental_xray_service.db.base import Base  # noqa: E402
from dental_xray_service.db.session import create_session_factory  # noqa: E402

settings = get_settings()
engine, _ = create_session_factory(settings.database_url)
Base.metadata.create_all(engine)
print("Database schema created")
