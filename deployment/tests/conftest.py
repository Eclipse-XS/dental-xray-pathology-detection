import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


@pytest.fixture
def png_bytes():
    from io import BytesIO

    from PIL import Image

    stream = BytesIO()
    Image.new("RGB", (128, 96), (10, 20, 30)).save(stream, format="PNG")
    return stream.getvalue()
