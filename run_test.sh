#!/bin/bash
set -euo pipefail

# Run fake server and live_api together for testing

cleanup() {
    echo "Stopping servers..."
    pkill -f "f1_race_analytics" 2>/dev/null || true
}
trap cleanup EXIT

echo "Starting fake server..."
uv run python -m f1_race_analytics.fake_server &
/bin/sleep 4

echo "Starting live_api..."
export OPENF1_API=http://localhost:1221/v1
export OPENF1_TOKEN_URL=http://localhost:1221/token
export OPENF1_MQTT_BROKER=localhost
export OPENF1_MQTT_PORT=1883
export OPENF1_USE_TLS=false
export OPENF1_USERNAME=test
export OPENF1_PASSWORD=test

uv run python -m f1_race_analytics.live_api &
/bin/sleep 2

echo ""
echo "========================================"
echo "  Both servers running!"
echo "========================================"
echo ""
echo "  Open: http://localhost:8000/live?session_key=99999"
echo ""
echo "  Press Ctrl+C to stop"
echo ""

wait
