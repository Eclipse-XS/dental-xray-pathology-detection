from fastapi import APIRouter, Depends

from dental_xray_service.api.dependencies import get_inference_service
from dental_xray_service.api.schemas.model import ModelInfoResponse
from dental_xray_service.inference.service import InferenceService

router = APIRouter(tags=["model"])


@router.get("/model-info", response_model=ModelInfoResponse)
def model_info(service: InferenceService = Depends(get_inference_service)) -> dict:
    return service.backend.metadata()
