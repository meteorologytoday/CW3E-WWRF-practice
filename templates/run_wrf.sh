#!/bin/bash


if [ "$1" = "" ]; then
    echo "Error: The number of processors is not specified."
fi

nproc=$1

echo "Received parameter: nproc = $nproc."

echo "Copy namelist.input.original -> namelist.input"
cp namelist.input.original namelist.input


echo "Running real.exe"
mpirun -np $nproc ./real.exe

if [ "$?" != 0 ]; then 
    
    echo "Error: real.exe finished with error."    
    exit 1

fi

echo "Running wrf.exe"
mpirun -np $nproc ./wrf.exe

if [ "$?" != 0 ]; then 
    
    echo "Error: wrf.exe finished with error."    
    exit 1

fi


