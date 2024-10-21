#!/bin/bash


if [ "$1" = "" ]; then
    echo "Error: The number of processors is not specified."
fi

nproc=$1

echo "Received parameter: nproc = $nproc."

# Check restart setup


echo "Copy namelist.input.original -> namelist.input"
cp namelist.input.original namelist.input


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

