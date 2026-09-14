import json
import sys
from pathlib import Path

DEPLOYMENT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DEPLOYMENT_ROOT / "src"))

from dental_xray_service.core.config import Settings  # noqa: E402
from dental_xray_service.models.metadata import load_model_identity  # noqa: E402

settings = Settings()
for path in (settings.checkpoint_path, settings.model_metadata_path):
    if not path.is_file():
        raise FileNotFoundError(path)
print(
    json.dumps(
        load_model_identity(settings.model_metadata_path, settings.checkpoint_path, "pytorch"), indent=2
    )
)
