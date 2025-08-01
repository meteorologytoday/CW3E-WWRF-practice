#!/bin/bash

rev=NO
if [ "$1" = "rev" ] ; then
    rev=YES
    echo "Reverse!"
fi 



output_root=/home/t2hsu/temp_project/PROCESSED_CW3E_WRF_RUNS/0.08deg
input_root=/home/t2hsu/temp_project/CW3E_WRF_RUNS/0.08deg

shares=(


#    exp_20221224/runs/CTL
#    exp_20221224/runs/PAT00_AMP1.0
#    exp_20221224/runs/PAT00_AMP-1.0


#    exp_20230101/runs/CTL
#    exp_20230101/runs/PAT00_AMP1.0
#    exp_20230101/runs/PAT00_AMP-1.0


#    exp_20230107/runs/PAT00_AMP2.0


#    exp_20230107/runs/PAT00_AMP0.0

#    exp_20230107/runs/PAT01_AMP-1.0
#    exp_20230107/runs/PAT01_AMP1.0
#    exp_20230107/runs/PAT01_AMP2.0
#    exp_20230107/runs/PAT01_AMP4.0

#    exp_20230107/runs/PAT00_AMP1.0
#    exp_20230107/runs/PAT00_AMP-1.0
#    exp_20230107/runs/PAT00_AMP2.0

    exp_20230112/runs/CTL
    exp_20230112/runs/PAT00_AMP1.0
    exp_20230112/runs/PAT00_AMP-1.0
)


# Reverse the order 
if [ "$rev" = "YES" ] ; then

    echo "Reverse order now!!!"

    num_elements="${#shares[@]}"
    # Loop from the last element to the first
    for (( i = num_elements - 1; i >= 0; i-- )); do
        reversed_shares+=("${shares[i]}")
    done

    shares=(${reversed_shares[@]})
fi



for shared in "${shares[@]}"; do
    for casedir in $( ls $input_root/$shared ); do
        input_dirs="$input_dirs    $input_root/$shared/$casedir"
        output_dirs="$output_dirs  $output_root/$shared/$casedir"
    done    
done

input_dirs=( $input_dirs )
output_dirs=( $output_dirs )





for (( i=0; i < ${#input_dirs[@]} ; i++ )); do

    input_dir=${input_dirs[$i]}/output/wrfout
    output_dir=${output_dirs[$i]}/output/wrfout

    python3 WRF-postprocessing-tools/src/wrf_basic_reduction.py \
        --input  $input_dir  \
        --output $output_dir \
        --check-policy varnames \
        --nproc  6

done 

wait




