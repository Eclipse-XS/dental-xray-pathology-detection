from dental_xray_service.db.base import Base
from dental_xray_service.db.repositories import PredictionRepository
from dental_xray_service.db.session import create_session_factory
from dental_xray_service.inference.types import Detection


def test_repository_round_trip(tmp_path):
    engine, factory = create_session_factory(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    metadata = {
        "experiment_id": "F_final_fcos_tuned",
        "model_version": "v1",
        "architecture": "FCOS",
        "backend": "fake",
        "artifact_sha256": "a" * 64,
        "runtime": "test",
    }
    with factory() as session:
        repo = PredictionRepository(session)
        repo.save(
            prediction_id="p1",
            correlation_id="c1",
            metadata=metadata,
            width=100,
            height=80,
            content_type="image/png",
            storage_uri=None,
            latency_ms=1.2,
            detections=[Detection(0, "Impacted", 0.9, (1, 2, 3, 4))],
        )
        loaded = repo.get("p1")
        assert loaded.id == "p1"
        assert loaded.detections[0].class_name == "Impacted"
