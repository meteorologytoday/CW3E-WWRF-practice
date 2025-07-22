#!/bin/bash


download_dir_root=./data/GEFSv12

#date_beg=2022-12-24
#date_end=2022-12-24


date_beg=2023-01-12
date_end=2023-01-12

#    --fcst-hrs $(seq 0 3 240) $(seq 246 6 480) \

python3 src/download_gefs.py               \
    --date-rng $date_beg $date_end         \
    --init-hrs 0                           \
    --fcst-hrs $(seq 0 3 240)              \
    --groups pgrb2a:0p50 pgrb2b:0p50       \
    --perturbation-members 31              \
   --output-root $download_dir_root

