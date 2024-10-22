#!/bin/bash

caserun_root=/expanse/lustre/scratch/t2hsu/temp_project/WRF_RUNS/0.16deg/WWRF_runs


for casedir in $( ls $caserun_root ); do
    
    cd $caserun_root/$casedir
    python3 submit_engine.py --unlock
    python3 submit_engine.py --reset
    python3 submit_engine.py --submit


done 


