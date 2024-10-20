#!/bin/bash
#SBATCH -p __PARTITION__
#SBATCH --nodes=__NODES__
#SBATCH --ntasks-per-node=__NPROC__
#SBATCH --cpus-per-task=1
#SBATCH -t 50:00:00
#SBATCH -J __JOBNAME__
#SBATCH -A csg102
#SBATCH -o __JOBNAME__.%j.%N.out
#SBATCH -e __JOBNAME__.%j.%N.err
#SBATCH --export=ALL

export SLURM_EXPORT_ENV=ALL

source /home/t2hsu/.bashrc_WRF_gcc

copy_to_dir=${SLURM_SUBMIT_DIR}
local_scratch=/scratch/${USER}/job_${SLURM_JOBID}
log_file=log.run
track_files=(
    rsl.out.0000
    rsl.error.0000
)

echo "copy_to_dir = $copy_to_dir"
echo "Local scratch    : $local_scratch"
echo "SLURM_SUBMIT_DIR : $SLURM_SUBMIT_DIR"
echo "Log file name    : $log_file"

echo "Copying files to local scratch"

ls | grep -v -e wrfout -e wrfrst -e ".err" -e ".out" | xargs -I % cp % -t $local_scratch

cd $local_scratch


echo "Current directory: `pwd`"

echo "Remove old log file."
rm $log_file

echo "Running run_wrf.sh"
bash run_wrf.sh __NPROC__ &> $log_file &

PID=$!
echo "WRF pid = $PID"


for track_file in "${track_files[@]}"; do
    echo "Start tail the file: $track_file"
    tail --retry -f --pid=$PID $track &
done

wait

echo "Program finished. Copy files back to $copy_to_dir"
ls | xargs -I % cp --verbose % -t $copy_to_dir

echo "Output files copied."

