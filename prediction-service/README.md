# prediction-service

Workload Prediction Service for the Cost-Aware Intelligent Cloud Auto-Scaling
project (HKBK CSE, AY 2025-26). Owner: Namratha U.

Forecasts CPU and requests/sec 5-15 minutes ahead using an LSTM and an
XGBoost baseline, served via FastAPI so the RL engine can call it before
every scaling decision.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# run the API (stub mode until you've trained a model)
uvicorn app.main:app --reload

# run tests
pytest tests/
```

## Train a model

```bash
python scripts_train.py --csv data/trace.csv
```

This trains both the LSTM and XGBoost models, prints MAPE/RMSE, and saves:
- `saved_models/lstm_model.h5`
- `saved_models/xgboost_models.pkl`

Restart the API afterwards (or redeploy) and `/predict` will automatically
pick up the LSTM model if present.

## API

- `GET /health`
- `POST /predict` — see `app/schemas.py` for the exact request/response shape.

## Docker

```bash
docker build -t prediction-service .
docker run -p 8000:8000 prediction-service
```
