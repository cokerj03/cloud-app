"""
Freight Rate & ETA API — a small, cloud-deployable Flask REST API that
estimates freight cost and delivery time between US cities by mode
(Truck / Rail / Ocean / Air / Parcel).

Run locally:
    pip install -r requirements.txt
    python3 app.py          # http://localhost:8080

Run in Docker:
    docker build -t freight-rate-api .
    docker run -p 8080:8080 freight-rate-api

See deploy/AWS_DEPLOY.md for deploying this to AWS.
"""
from datetime import date

from flask import Flask, jsonify, request, send_from_directory

from rates import quote, known_cities, known_modes, UnknownCityError, UnknownModeError

app = Flask(__name__, static_folder="static")


@app.get("/health")
def health():
    return jsonify(status="ok"), 200


@app.get("/api/meta")
def meta():
    return jsonify(cities=known_cities(), modes=known_modes())


@app.post("/api/quote")
def api_quote():
    body = request.get_json(silent=True) or {}
    required = ["origin", "destination", "mode", "weight_lbs"]
    missing = [f for f in required if f not in body]
    if missing:
        return jsonify(error=f"Missing required field(s): {', '.join(missing)}"), 400

    ship_date = None
    if body.get("ship_date"):
        try:
            ship_date = date.fromisoformat(body["ship_date"])
        except ValueError:
            return jsonify(error="ship_date must be YYYY-MM-DD"), 400

    try:
        weight = float(body["weight_lbs"])
        result = quote(
            origin=body["origin"],
            destination=body["destination"],
            mode=body["mode"],
            weight_lbs=weight,
            ship_date=ship_date,
        )
    except (UnknownCityError, UnknownModeError, ValueError) as e:
        return jsonify(error=str(e)), 422

    return jsonify(result), 200


@app.get("/")
def docs():
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
