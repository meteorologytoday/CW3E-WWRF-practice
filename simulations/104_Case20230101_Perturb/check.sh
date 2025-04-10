#!/bin/bash


caserun_root=/home/t2hsu/temp_project/CW3E_WRF_RUNS/0.08deg/exp_20230101/runs/PAT00_AMP1.0
file_check=output/wrfout/wrfout_d01_2023-01-08_00:00:00_temp


cwd=`pwd`
submit_engine_file=$( realpath ../../templates/submit_engine.py )
for casedir in $( ls $caserun_root ); do
   
#    if [[ "$casedir" =~ "ens01" ]] ; then
#        continue
#    fi
    
    cd $caserun_root/$casedir
    file_path=$caserun_root/$casedir/$file_check
    
    
    if [ -f "$file_path" ]; then
        echo "[$casedir] $file_path exists."
    else
        echo "[$casedir] $file_path not found."
        
        cp $submit_engine_file .
        #python3 submit_engine.py --unlock-if-not-running
        #python3 submit_engine.py --submit
    fi

    cd $cwd
done 


