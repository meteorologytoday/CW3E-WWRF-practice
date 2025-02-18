#!/bin/bash

echo "[[[ This program extracts West-WRF postprocessed data for verification ]]] "

archive_root=/expanse/nfs/cw3e/datasets/cw3e/NRT/2022-2023/NRT_ens/
processed_root=./processed_data

needed_varnames=(
    precip
    precip_g
    precip_c
    precip_bkt
    snow_g
    IWV
    IVT
    IVTU
    IVTV
    SST
    slp
    pblh
    time
    forecast_reference_time
    lat
    lon
    LandMask
)

START_TIMES=(
    2022121400
)

REL_DIRS=(
    cf/ecm001
)


# Convert into comma-separated string
IFS=,
variable_list="${needed_varnames[*]}"

echo "===== Basic setup ====="
echo "archive_root = $archive_root"
echo "processed_root = $processed_root"
echo "variable_list = $variable_list"

echo "===== Processing Files ===="
for start_time in ${START_TIMES[@]} ; do
for rel_dir in ${REL_DIRS[@]} ; do
 
    # Example format:
    #   start_time=2022121400
    #   rel_dir=cf/ecm001
    
    input_dir=$archive_root/$start_time/$rel_dir
    output_dir=$processed_root/$start_time/$rel_dir
    
    echo "input_dir = $input_dir"
    echo "output_dir = $output_dir"

    mkdir -p $output_dir

    for filename in $( ls $input_dir ) ; do
        
        input_file=$input_dir/$filename
        output_file=$output_dir/$filename

        echo "* Doing: $input_file => $output_file"        
        ncks -O -v "$variable_list" $input_file $output_file 
        
    done
   
done
done
 
