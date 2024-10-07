#!/bin/bash


source setup.sh


echo "Generating namelist file $namelist_wps"

sed -e "s/__START_DATE__/${START_DATE}/g"     \
    -e "s/__END_DATE1__/${END_DATE1}/g"       \
    -e "s/__END_DATE2__/${END_DATE2}/g"       \
    -e "s/__END_DATE3__/${END_DATE3}/g"       \
    -e "s/__BDY_INTERVAL_SECONDS__/${BDY_INTERVAL_SECONDS}/g" \
    -e "s/__MAX_DOM__/${MAX_DOM}/g"           \
    -e "s/__PREFIX__/${PREFIX}/g"             \
    -e "s/__NX1__/${NX1}/g"                   \
    -e "s/__NY1__/${NY1}/g"                   \
    -e "s/__DX1_DEG__/${DX1_DEG}/g"           \
    -e "s/__DY1_DEG__/${DY1_DEG}/g"           \
    $sample_namelist_wps > $namelist_wps

echo "Move the name list file to $WPS_DIR"
cp $namelist_wps $WPS_DIR/namelist.wps



cd $WPS_DIR

rm Vtable
echo "Make softlink Vtable -> $Vtable"
ln -s $Vtable Vtable



echo "Run geogrid.exe in 3 seconds"
#sleep 3
mpirun -n 16 ./geogrid.exe

echo "Run link_grib.csh in 3 seconds"
#sleep 3
./link_grib.csh $data_dir


echo "Run ungrib.exe in 3 seconds"
#sleep 3
mpirun -n 16 ./ungrib.exe


echo "Run metgrid.exe in 3 seconds"
#sleep 3
./metgrid.exe


