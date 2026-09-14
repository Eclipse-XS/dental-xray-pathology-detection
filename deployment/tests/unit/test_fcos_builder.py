def test_model_builder_does_not_request_pretrained_downloads(monkeypatch):
    import dental_xray_service.models.fcos as module

    observed = {}

    class DummyHead:
        classification_head = None

    class DummyBackbone:
        out_channels = 256

    class DummyAnchors:
        def num_anchors_per_location(self):
            return [1]

    class DummyModel:
        head = DummyHead()
        backbone = DummyBackbone()
        anchor_generator = DummyAnchors()

    def fake_builder(**kwargs):
        observed.update(kwargs)
        return DummyModel()

    monkeypatch.setattr(module, "fcos_resnet50_fpn", fake_builder)
    monkeypatch.setattr(module, "FCOSClassificationHead", lambda *args, **kwargs: object())
    module.build_final_fcos(768)
    assert observed == {"weights": None, "weights_backbone": None, "min_size": 768, "max_size": 768}
