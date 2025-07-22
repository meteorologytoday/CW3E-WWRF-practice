#!/bin/bash




#source 98_trapkill.sh
#batch_cnt_limit=5


source run00_setup.sh

log_dir=log_wps


if [ ] ; then
python3 $src_dir/main_code_GEFS/main_WPS.py \
    --setup $setup_file --workflow 0 --nproc 4
fi


prog=$( realpath $src_dir/main_code_GEFS/main_WPS.py )

#for ens_id in $( seq 5 30 ) ; do
for ens_id in $( seq 1 30 ) ; do

    JOBNAME=runWPS${ens_id}

    sbatch \
        --job-name=$JOBNAME \
        --nodes=1                  \
        --time=05:00:00            \
        --partition=cw3e-shared    \
        --ntasks-per-node=1        \
        --cpus-per-task=1          \
        --mem=4G                  \
        -A csg102                  \
        -o $log_dir/$JOBNAME.%j.%N.out      \
        -e $log_dir/$JOBNAME.%j.%N.err      \
        --wrap="source $HOME/.bashrc ; conda activate lab1 ; source $HOME/.bashrc_WRF_gcc ; python3 $prog --setup $setup_file --specify-ens-id=${ens_id}"

done

echo "Done"


