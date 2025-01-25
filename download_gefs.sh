#!/bin/bash


download_dir_root=./data/GEFSv12

date_beg=2023-01-01
date_end=2023-01-01

python3 src/download_gefs.py               \
    --date-rng $date_beg $date_end         \
    --init-hrs 0 12                        \
    --fcst-hrs $(seq 0 3 240)              \
    --groups pgrb2a:0p50 pgrb2b:0p50       \
    --perturbation-members 31              \
   --output-root $download_dir_root

