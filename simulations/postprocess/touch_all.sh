#!/bin/bash

root_dir=/home/t2hsu/temp_project/CW3E_WRF_RUNS/0.08deg/exp_20230107

process_files_log=files_process

#rm -f $process_files_log

if [ -f "$process_files_log" ]; then 
    echo "Finding files to touch and dump into $process_files_log"
    find $root_dir -name "wrfout_d01*" > $process_files_log
else
    echo "$process_files_log exists. Use it."
fi

cat $process_files_log | while read filepath 
do
    echo "File: $filepath"

    now_time=$( date +%Y-%m-%d )
    old_time=$( ls -l --time-style="+%Y-%m-%d" $filepath | awk '{ print $6 }' )

    if [ "$now_time" = "$old_time" ] ; then
        echo "Time is new enough. Skip this."
    else
        touch $filepath
        new_time=$( ls -l --time-style="+%Y-%m-%d" $filepath | awk '{ print $6 }' )
        echo "Time change: $old_time => $new_time"
    fi
done




#for case_dir in $( ls ${root_dir}/run ); do
#    
#    full_case_dir=${root_dir}/run/${case_dir}
#    echo "Doing full_case_dir = $full_case_dir"
#    
#    for ens_dir in $( ls ${full_case_dir} ); do
#        
#        full_ens_dir=${full_ens_dir}/$ens_dir
        
        
