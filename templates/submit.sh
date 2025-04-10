#!/bin/bash
#SBATCH -p __PARTITION__
#SBATCH --nodes=__NODES__
#SBATCH --ntasks-per-node=__NPROC_PER_NODE__
#SBATCH --cpus-per-task=1
#SBATCH -t 50:00:00
#SBATCH -J __JOBNAME__
#SBATCH -A csg102
#SBATCH -o __JOBNAME__.%j.%N.out
#SBATCH -e __JOBNAME__.%j.%N.err
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

wrfrst_dir=${SLURM_SUBMIT_DIR}/output/wrfrst

track_files=(
    $log_file
)

echo "copy_to_dir = $copy_to_dir"
echo "Local scratch    : $local_scratch"
echo "SLURM_SUBMIT_DIR : $SLURM_SUBMIT_DIR"
echo "Log file name    : $log_file"
echo "Copying files to local scratch"

ls | grep -v -e output -e wrfout -e wrfrst -e ".err" -e ".out" | xargs -I % cp % -t $local_scratch

cd $local_scratch
echo "Current directory: `pwd`"

echo "Make soft links of restart files if any."
if [ -d "$wrfrst_dir" ] ; then
    ln -s $wrfrst_dir/* ./
fi

for track_file in "${track_files[@]}"; do
    echo "Remove old track file if it exists: $track_file"
    rm $track_file
done


echo "Running run_wrf.sh"
bash run_wrf.sh __NPROC_PER_ATM_MODEL__ &> $log_file &

PID=$!
echo "WRF pid = $PID"
for track_file in "${track_files[@]}"; do
    echo "Start tail the file: $track_file"
    tail --retry -f --pid=$PID $track_file &
done

echo "Now hold."
wait

echo "Program finished. Copy files back to $copy_to_dir"


for prefix in rsl wrfinput wrfout wrfrst ; do 

    echo "Copying file group: $prefix"
    output_dir=$copy_to_dir/output/$prefix
    mkdir -p $output_dir
    for filename in $( ls | grep $prefix ) ; do
        if [ -L "$filename" ]; then
            echo "File $filename is a soft link. Skip it. "
            continue
        fi
        cp --verbose $filename $output_dir/
    done

done

cd $SLURM_SUBMIT_DIR

# Unlock
python3 submit_engine.py --unlock

# Check
python3 submit_engine.py --check-output

exit_code=$?
if [ "$exit_code" != 0 ]; then 
    echo "Warning: Output check failed with non-zero exit code ${exit_code}."    
fi

# Submit
echo "Try submitting."
python3 submit_engine.py --submit

echo "End of file 'submit.sh'."
