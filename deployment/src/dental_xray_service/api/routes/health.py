from fastapi import APIRouter, Request, Response, status

from dental_xray_service.api.schemas.common import HealthResponse

router = APIRouter(tags=["service"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/ready", response_model=HealthResponse)
def ready(request: Request, response: Response) -> HealthResponse:
    if not request.app.state.ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="not_ready")
    return HealthResponse(status="ready")
