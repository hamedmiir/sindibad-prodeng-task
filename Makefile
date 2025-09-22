.PHONY: install dev seed retrain test docker

install:
pip install -e .[dev]

dev:
uvicorn autotag.app.main:app --reload

seed:
python -m autotag.scripts.seed_db

retrain:
python -m autotag.scripts.train_ml

test:
pytest -q

docker:
docker build -t autotag:dev .
