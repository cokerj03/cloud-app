# Freight Rate & ETA API

A small, cloud-ready REST API that estimates freight cost and delivery time between US cities, by shipping mode (Truck, Rail, Ocean, Air, Parcel). Built as a companion to [ShipTrack](../shiptrack) — the same domain (logistics/freight), packaged as a stateless API instead of a full CRUD app, to demonstrate an actual cloud deployment path.

**Try the interactive docs page** — run it locally and open `http://localhost:8080`, or see `deploy/AWS_DEPLOY.md` to put it on AWS.

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness check — used by load balancers / container orchestrators |
| GET | `/api/meta` | Supported cities & shipping modes |
| POST | `/api/quote` | Get a cost + ETA estimate |
| GET | `/` | Small interactive docs/demo page |

**Example:**

```bash
curl -X POST http://localhost:8080/api/quote \
  -H "Content-Type: application/json" \
  -d '{"origin":"Orlando, FL","destination":"Atlanta, GA","mode":"Truck","weight_lbs":1200}'
```

```json
{
  "origin": "Orlando, FL",
  "destination": "Atlanta, GA",
  "mode": "Truck",
  "weight_lbs": 1200,
  "distance_miles": 473.8,
  "estimated_cost_usd": 1166.01,
  "estimated_transit_days": 1,
  "ship_date": "2026-08-28",
  "estimated_delivery": "2026-08-29"
}
```

## How the estimate works

`rates.py` computes great-circle distance between city coordinates (haversine formula), pads it for real road/rail/sea routing, then applies a per-mile rate + weight surcharge + mode-specific fuel surcharge for cost, and an average-speed + handling-time model for transit days. All pure functions, no external APIs — deliberately dependency-light so it's easy to read, test, and deploy.

## Run locally

```bash
pip install -r requirements.txt
python3 app.py            # http://localhost:8080
```

## Run the tests

```bash
python3 -m unittest discover -s tests -v
```

13 unit tests covering the rate/distance math and every API endpoint (success and error paths).

## Run in Docker

```bash
docker build -t freight-rate-api .
docker run -p 8080:8080 freight-rate-api
```

## Deploy to AWS

See [`deploy/AWS_DEPLOY.md`](./deploy/AWS_DEPLOY.md) — covers AWS App Runner (simplest), Elastic Beanstalk, and plain EC2/Docker.

## Project structure

```
cloud-app/
├── app.py                 # Flask routes
├── rates.py                # distance / cost / ETA logic (pure functions)
├── static/index.html       # docs + interactive demo page
├── tests/test_app.py       # unit tests (13, all passing)
├── Dockerfile
├── deploy/AWS_DEPLOY.md
└── requirements.txt
```
