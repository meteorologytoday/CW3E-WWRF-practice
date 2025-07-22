#!/bin/bash

caserun_root=/home/t2hsu/temp_project/CW3E_WRF_RUNS/0.08deg/exp_20221224/runs

file_check=output/wrfout/wrfout_d01_2023-01-03_00:00:00_temp


cwd=`pwd`
for casedir in $( ls $caserun_root ); do
   
    if [[ "$casedir" =~ "ens01" ]] ; then
        continue
    fi
    
    cd $caserun_root/$casedir
    file_path=$caserun_root/$casedir/$file_check
    
    
    if [ -f "$file_path" ]; then
        echo "[$casedir] $file_check exists."
    else
        echo "[$casedir] $file_check not found."
        
        #python3 submit_engine.py --unlock
        #python3 submit_engine.py --submit
    fi

    cd $cwd
done 


