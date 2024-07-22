#!/bin/bash

WPS_DIR=/home/t2hsu/models/WRF/WESTWRF/WPS-4.4
CWD=`pwd`

sample_namelist_wps=/home/t2hsu/projects/WWRF_LEARNING/namelists/west-wrf-namelist.wps

namelist_wps=west-wrf-namelist.completed.wps

START_DATE=2024-01-05_00:00:00
END_DATE1=2024-01-08_00:00:00
END_DATE2=$END_DATE1
END_DATE3=$END_DATE2
GFS_INTERVAL=10800
MAX_DOM=1

NX=828
NY=570
DX=0.08
DY=0.08

PREFIX=FILE

NX=207
NY=142
DX=0.32
DY=0.32


sed -e "s/__START_DATE__/${START_DATE}/g"     \
    -e "s/__END_DATE1__/${END_DATE1}/g"       \
    -e "s/__END_DATE2__/${END_DATE2}/g"       \
    -e "s/__END_DATE3__/${END_DATE3}/g"       \
    -e "s/__GFS_INTERVAL__/${GFS_INTERVAL}/g"   \
    -e "s/__MAX_DOM__/${MAX_DOM}/g"             \
    -e "s/__PREFIX__/${PREFIX}/g"               \
    -e "s/__NX__/${NX}/g"               \
    -e "s/__NY__/${NY}/g"               \
    -e "s/__DX__/${DX}/g"               \
    -e "s/__DY__/${DY}/g"               \
    $sample_namelist_wps > $namelist_wps


cp $namelist_wps $WPS_DIR/namelist.wps





cd $WPS_DIR
echo "Run geogrid.exe in 3 seconds"
sleep 3

./geogrid.exe

 
