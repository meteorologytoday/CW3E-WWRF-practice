#!/bin/bash


if [ "$1" = "" ]; then
    echo "Error: The number of processors is not specified."
fi

nproc=$1

echo "Received parameter: nproc = $nproc."

# Check restart setup
# Check which restart segment we are in
# Modify namelist accordingly

echo "Running real.exe"
mpirun -np $nproc ./real.exe &
PID=$!
tail --retry -f --pid=$PID rsl.out.0000 &>> log.run

exit_code=$?
if [ "$exit_code" != 0 ]; then 
    echo "Warning: real.exe finished with non-zero exit code ${exit_code}."    
fi

echo "Running wrf.exe"
mpirun -np $nproc ./wrf.exe &
PID=$!
tail --retry -f --pid=$PID rsl.out.0000 &>> log.run

exit_code=$?
if [ "$exit_code" != 0 ]; then 
    echo "Warning: wrf.exe finished with non-zero exit code ${exit_code}."    
fi


# Check if we reached the end of restart cycle

# If not, then submit myself again


