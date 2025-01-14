#!/bin/bash
echo "Testing mount points..."
python test_mount.py

echo "Starting server..."
uvicorn app:app --loop asyncio --reload --workers ${WORKERS} --host $CURRENT_HOST --port $PORT --proxy-headers