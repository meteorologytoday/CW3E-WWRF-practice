#!/bin/bash
#SBATCH -p __PARTITION__
#SBATCH --nodes=__NODES__
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=40G
#SBATCH -t 24:00:00
#SBATCH -J __JOBNAME__
#SBATCH -A csg102
#SBATCH -o __JOBNAME__.%j.%N.out
#SBATCH -e __JOBNAME__.%j.%N.err
#SBATCH --export=ALL

export SLURM_EXPORT_ENV=ALL

source /home/t2hsu/.bashrc_WRF_gcc

local_scratch=/scratch/${USER}/job_${SLURM_JOBID}
log_file=log.run

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

echo "Start tail the log file."
tail --retry -f --pid=$PID $log_file

echo "Program finished. Copy files back..."
ls | xargs -I % cp % -t $SLURM_SUBMIT_DIR

echo "Output files copied."

