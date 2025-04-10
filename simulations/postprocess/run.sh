#!/bin/bash

output_root=/home/t2hsu/temp_project/PROCESSED_CW3E_WRF_RUNS/0.08deg
input_root=/home/t2hsu/temp_project/CW3E_WRF_RUNS/0.08deg

if [ ] ; then
exp_name=exp_20221224

shares=(
    Perturb1/runs/PAT00_AMP-1.0
    Perturb1/runs/PAT00_AMP1.0
    Baseline01/runs
)
fi

exp_name=exp_20230101

shares=(
    exp_20230101/runs/PAT00_AMP1.0
    exp_20230101/runs/PAT00_AMP-1.0
)

for shared in "${shares[@]}"; do
    for casedir in $( ls $input_root/$shared ); do
        input_dirs="$input_dirs    $input_root/$shared/$casedir"
        output_dirs="$output_dirs  $output_root/$shared/$casedir"
    done    
done

input_dirs=( $input_dirs )
output_dirs=( $output_dirs )

for (( i=0; i< ${#input_dirs[@]} ; i++ )); do

    input_dir=${input_dirs[$i]}/output/wrfout
    output_dir=${output_dirs[$i]}/output/wrfout

    python3 WRF-postprocessing-tools/src/wrf_basic_reduction.py \
        --input  $input_dir  \
        --output $output_dir \
        --check-policy varnames \
        --nproc  2

done


