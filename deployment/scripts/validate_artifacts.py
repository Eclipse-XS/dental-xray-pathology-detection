"""Check immutable deployment inputs without loading the model."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dental_xray_service.core.config import Settings  # noqa: E402

settings = Settings()
required = [settings.checkpoint_path, settings.model_metadata_path]
missing = [str(path) for path in required if not path.is_file()]
if missing:
    raise FileNotFoundError(f"Missing deployment artifacts: {missing}")
print({"status": "PASS", "artifacts": [str(path) for path in required]})
