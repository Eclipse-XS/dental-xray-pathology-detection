from fastapi import APIRouter, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from dental_xray_service.core.config import get_settings

router = APIRouter(tags=["monitoring"])


@router.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    if not get_settings().prometheus_enabled:
        raise HTTPException(status_code=404, detail="Metrics are disabled")
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
