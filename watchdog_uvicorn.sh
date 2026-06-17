#!/bin/bash

BASE_DIR="/home/oscar/sw/mapas"

PROCESS="/home/oscar/sw/envs/datadis_api/bin/uvicorn app:app --host 0.0.0.0 --port 8000"

LOGFILE="$BASE_DIR/watchdog_uvicorn.log"
UVICORN_LOG="$BASE_DIR/uvicorn.log"

if pgrep -f "$PROCESS" > /dev/null 2>&1; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - uvicorn ya está ejecutándose" >> "$LOGFILE"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - uvicorn NO está ejecutándose. Arrancando..." >> "$LOGFILE"

    nohup bash -c "
        cd '$BASE_DIR' || exit 1
        exec $PROCESS
    " >> "$UVICORN_LOG" 2>&1 &

    echo "$(date '+%Y-%m-%d %H:%M:%S') - uvicorn arrancado" >> "$LOGFILE"
fi
