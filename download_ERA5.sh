#!/bin/bash


python3 ./src/download_ERA5.py       \
    --date-rng 2023-01-01 2023-01-21  \
    --date-inclusive both             \
    --download-dir WRF_ERA5           \
    --nproc 3
