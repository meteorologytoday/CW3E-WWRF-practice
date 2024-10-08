#!/bin/bash

source ../../00_setup.sh

init_date=2022-01-07
init_time=00:00:00


input_dir=/home/t2hsu/temp_project/WRF_RUNS/test_gcc
output_dir=/home/t2hsu/temp_project/WRF_RUNS/altered_SST

init_SST_file=/home/t2hsu/temp_project/WRF_RUNS/test_gcc/met_em.d01.${init_date}_${init_time}.nc
pert_SST_file=/home/t2hsu/projects/CW3E-WWRF-practice/test/perturbation/pert_SST.d01.2022-01-07_00:00:00.nc

output_init_time=${init_date}T${init_time}
output_hours=24
output_interval=6

python3 $SRC_DIR/generate_prescribed_SST.py \
    --input-dir $input_dir         \
    --output-dir $output_dir       \
    --init-SST-file $init_SST_file \
    --pert-SST-file $pert_SST_file \
    --output-init-time $output_init_time  \
    --output-hours $output_hours   \
    --output-interval $output_interval \
    --pert-method persistent_SST_anomaly 

