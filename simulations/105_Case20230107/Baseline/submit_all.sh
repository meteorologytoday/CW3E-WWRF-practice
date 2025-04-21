#!/bin/bash

caserun_root=/home/t2hsu/temp_project/CW3E_WRF_RUNS/0.08deg/exp_20230101/runs

for casedir in $( ls $caserun_root ); do
    
    cd $caserun_root/$casedir

    #cp $HOME/projects/CW3E-WWRF-practice/templates/submit_engine.py .
    #python3 submit_engine.py --unlock
    #python3 submit_engine.py --check-output
    python3 submit_engine.py --submit

done 


