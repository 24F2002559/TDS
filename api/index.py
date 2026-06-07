import json
import math
import statistics
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow CORS from any origin for POST requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load the telemetry data once when the app starts
with open("q-vercel-latency.json", "r") as f:
    TELEMETRY = json.load(f)

def compute_metrics(records, threshold):
    if not records:
        return {
            "avg_latency": 0,
            "p95_latency": 0,
            "avg_uptime": 0,
            "breaches": 0
        }
    latencies = [r["latency"] for r in records]
    uptimes = [r["uptime"] for r in records]
    avg_lat = statistics.mean(latencies)
    avg_upt = statistics.mean(uptimes)
    breaches = sum(1 for l in latencies if l > threshold)

    # Calculate 95th percentile using nearest‑rank
    sorted_lat = sorted(latencies)
    n = len(sorted_lat)
    idx = math.ceil(0.95 * n) - 1
    idx = min(idx, n - 1)
    p95_lat = sorted_lat[idx]

    return {
        "avg_latency": avg_lat,
        "p95_latency": p95_lat,
        "avg_uptime": avg_upt,
        "breaches": breaches
    }

@app.post("/")
async def analyse_latency(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 180)

    result = {}
    for region in regions:
        region_records = [r for r in TELEMETRY if r["region"] == region]
        result[region] = compute_metrics(region_records, threshold)

    return result
