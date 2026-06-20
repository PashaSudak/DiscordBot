#!/bin/bash
# entrypoint.sh — Retry wrapper for Render
# If the bot hits a rate-limit (429), it waits and retries.
# This is more reliable than in-process retry because it starts a fresh Python process.

MAX_DELAY=600  # 10 minutes
BASE_DELAY=30  # 30 seconds

delay=$BASE_DELAY

while true; do
    echo "[ENTRYPOINT] Starting bot..."
    python main.py

    exit_code=$?
    echo "[ENTRYPOINT] Bot exited with code $exit_code. Restarting in ${delay}s..."

    sleep "$delay"

    # Increase delay up to MAX_DELAY
    delay=$((delay * 2))
    if [ "$delay" -gt "$MAX_DELAY" ]; then
        delay=$MAX_DELAY
    fi
done