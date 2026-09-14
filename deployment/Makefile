.PHONY: install test lint api docker-up docker-down export-onnx benchmark migrate
install:
	python -m pip install -e ".[dev]"
test:
	pytest
lint:
	ruff check .
api:
	uvicorn dental_xray_service.main:app --reload
docker-up:
	docker compose --profile core up --build
docker-down:
	docker compose --profile core down
migrate:
	alembic upgrade head
export-onnx:
	python scripts/export_onnx.py --checkpoint ../artifacts/refinement/fcos/F_final_fcos_tuned/best.pth --metadata ../artifacts/refinement/fcos/selected_final_model.json --output models/final_fcos_768.onnx
benchmark:
	python scripts/benchmark_backends.py ../data/processed/dentex_diagnosis/images/test/train_102.png --backend pytorch
