from fastapi import Request

from dental_xray_service.inference.service import InferenceService


def get_inference_service(request: Request) -> InferenceService:
    return request.app.state.inference_service


def get_session_factory(request: Request):
    return request.app.state.session_factory
