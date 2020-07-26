#!/bin/bash
until python3 ./forever_run.py; do
    echo "'forever_run.py' crashed with exit code $?. Restarting..." >&2
    sleep 1
done

