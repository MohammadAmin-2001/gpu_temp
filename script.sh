#!/bin/bash

THRESHOLD=70

if command -v nvidia-smi >/dev/null 2>&1; then
    GPUS_TEMP=$(nvidia-smi --query-gpu=name,temperature.gpu --format=csv,noheader)
    echo "$GPUS_TEMP"
    exit 0
else
    echo "nvidia-smi not found!" >&2
    exit 1
fi
