#!/bin/bash

caserun_root=/expanse/lustre/scratch/t2hsu/temp_project/WRF_RUNS/0.16deg/runs_GEFS_MUR


for casedir in $( ls $caserun_root ); do
    
    cd $caserun_root/$casedir

    #cp $HOME/projects/CW3E-WWRF-practice/templates/submit_engine.py .
    #python3 submit_engine.py --unlock
    #python3 submit_engine.py --check-output
    python3 submit_engine.py --submit

done 


