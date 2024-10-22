#!/bin/bash
#SBATCH -p cw3e-shared
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH -t 50:00:00
#SBATCH -J testsubmit
#SBATCH -A csg102
#SBATCH -o testsubmit.0.%j.%N.out
#SBATCH -e testsubmit.0.%j.%N.err
#SBATCH --export=ALL


export SLURM_EXPORT_ENV=ALL

echo "Source the module file..."
source /home/t2hsu/.bashrc
conda activate lab1
source /home/t2hsu/.bashrc_WRF_gcc
echo "Done"

copy_to_dir=${SLURM_SUBMIT_DIR}
local_scratch=/scratch/${USER}/job_${SLURM_JOBID}
log_file=log.run

track_files=(
    $log_file
)

echo "copy_to_dir = $copy_to_dir"
echo "Local scratch    : $local_scratch"
echo "SLURM_SUBMIT_DIR : $SLURM_SUBMIT_DIR"
echo "Log file name    : $log_file"

echo "Copying files to local scratch"

ls | grep -v -e output -e wrfout -e wrfrst -e ".err" -e ".out" | xargs -I % cp % -t $local_scratch

if [ -d "./output/wrfrst" ] ; then
    ln -s ./output/wrfrst/* $local_scratch
fi

cd $local_scratch

echo "Current directory: `pwd`"
for track_file in "${track_files[@]}"; do
    echo "Remove old track file if it exists: $track_file"
    rm $track_file
done


echo "Running run_wrf.sh"
#bash run_wrf.sh 128 &> $log_file &

echo "Program finished. Copy files back to $copy_to_dir"


for prefix in rsl wrfinput wrfout wrfrst ; do 

    echo "Copying file group: $prefix"
    output_dir=$copy_to_dir/output/$prefix
    mkdir -p $output_dir
    ls | grep $prefix | xargs -I % cp --verbose % -t $output_dir

done

cd $SLURM_SUBMIT_DIR

# Unlock
python3 submit_engine.py --unlock

# Submit
python3 submit_engine.py --submit


echo "Done"
