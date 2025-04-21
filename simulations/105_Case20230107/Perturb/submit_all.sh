#!/bin/bash

caserun_root=/home/t2hsu/temp_project/CW3E_WRF_RUNS/0.08deg/exp_20230107/runs

groups=( PAT00_AMP0.0 PAT00_AMP2.0 )

cwd=`pwd`
for group in "${groups[@]}" ; do
    runs_dir=$caserun_root/$group
    for casedir in $( ls $runs_dir ); do
        
        cd $runs_dir/$casedir

        #cp $HOME/projects/CW3E-WWRF-practice/templates/submit_engine.py .

        #if [[ "$casedir" =~ "ens22" ]] ; then
        #    continue
        #fi
        echo "Current dir: $( pwd )"     
        python3 submit_engine.py --unlock
        python3 submit_engine.py --submit

        cd $cwd

    done
done 


