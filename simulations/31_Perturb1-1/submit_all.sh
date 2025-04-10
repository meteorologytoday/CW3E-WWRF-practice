#!/bin/bash

caserun_root=/home/t2hsu/temp_project/CW3E_WRF_RUNS/0.08deg/exp_Perturb1-1/runs
subgroups=( PAT00_AMP1.0 )

for subgroup in "${subgroups[@]}" ; do
    runs_dir=$caserun_root/$subgroup
    for casedir in $( ls $runs_dir ); do
        
        cd $runs_dir/$casedir

        #cp $HOME/projects/CW3E-WWRF-practice/templates/submit_engine.py .
        python3 submit_engine.py --unlock
        #python3 submit_engine.py --check-output
        python3 submit_engine.py --submit

    done
done 


