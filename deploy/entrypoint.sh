#!/bin/sh
set -eu

for name in roster inventory history; do
    if [ ! -s "/data/$name.json" ]; then
        echo "Missing sanitized /data/$name.json; set SLEEP_DATA_DIR and import a collection first." >&2
        exit 1
    fi
done
if [ ! -d /data/snapshots ]; then
    echo "Missing /data/snapshots; mount the complete sanitized collection." >&2
    exit 1
fi

exec nginx -g 'daemon off;'
