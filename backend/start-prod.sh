#!/bin/bash
# Production startup script for UniVote Backend
# Uses Gunicorn with Uvicorn workers for high concurrency.

# Calculate workers based on CPU cores if not specified
# Rule of thumb: (2 x num_cores) + 1
WORKERS=${WORKERS:-4}

echo "Starting UniVote Backend with $WORKERS workers..."
gunicorn -k uvicorn.workers.UvicornWorker \
         -w $WORKERS \
         --bind 0.0.0.0:${PORT:-8000} \
         --access-logfile - \
         --error-logfile - \
         main:app
