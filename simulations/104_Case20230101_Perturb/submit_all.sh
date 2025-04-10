#!/bin/bash

caserun_root=/home/t2hsu/temp_project/CW3E_WRF_RUNS/0.08deg/exp_20230101/runs

subgroups=( PAT00_AMP-1.0 PAT00_AMP1.0 )

cwd=`pwd`
for subgroup in "${subgroups[@]}" ; do
    runs_dir=$caserun_root/$subgroup
    for casedir in $( ls $runs_dir ); do
        
        cd $runs_dir/$casedir

        cp $HOME/projects/CW3E-WWRF-practice/templates/submit_engine.py .

        #if [[ "$casedir" =~ "ens19" ]] ; then
        #    continue
        #fi
 
        #if [[ "$casedir" =~ "ens21" ]] ; then
        #    continue
        #fi
 
        #if [[ "$casedir" =~ "ens22" ]] ; then
        #    continue
        #fi
     
        #cd $caserun_root/$casedir
       

        #check_results_before=0
        #python3 submit_engine.py --check-output &> /dev/null
        #check_results=$?

        echo "Msg: $check_results_before => $check_results"

        if [ "$check_results" = "0" ]; then
            echo "[$casedir] $file_check exists."
        else
            echo "[$casedir] $file_check not found."
            
            python3 submit_engine.py --unlock-forced
            python3 submit_engine.py --submit
        fi

        cd $cwd




    done
done 


