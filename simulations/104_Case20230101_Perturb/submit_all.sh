#!/bin/bash

caserun_root=/home/t2hsu/temp_project/CW3E_WRF_RUNS/0.08deg/exp_20230101/runs

subgroups=( PAT00_AMP-1.0 PAT00_AMP1.0 )

cwd=`pwd`
for subgroup in "${subgroups[@]}" ; do
    runs_dir=$caserun_root/$subgroup
    for casedir in $( ls $runs_dir ); do
        
        cd $runs_dir/$casedir

        #cp $HOME/projects/CW3E-WWRF-practice/templates/submit_engine.py .

        #if [[ "$casedir" =~ "ens22" ]] ; then
        #    continue
        #fi
     
        python3 submit_engine.py --unlock
        python3 submit_engine.py --submit

        cd $cwd

    done
done 


