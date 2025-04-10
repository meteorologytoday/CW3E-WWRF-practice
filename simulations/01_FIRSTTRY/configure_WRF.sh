#!/bin/bash


source setup.sh


echo "Generating namelist file $namelist_wrf"

sed -e "s/__START_YEAR__/${START_YEAR}/g"       \
    -e "s/__START_MONTH__/${START_MONTH}/g"     \
    -e "s/__START_DAY__/${START_DAY}/g"         \
    -e "s/__START_HOUR__/${START_HOUR}/g"       \
    -e "s/__START_MINUTE__/${START_MINUTE}/g"   \
    -e "s/__START_SECOND__/${START_SECOND}/g"   \
    -e "s/__END_YEAR1__/${END_YEAR1}/g"         \
    -e "s/__END_YEAR2__/${END_YEAR2}/g"         \
    -e "s/__END_YEAR3__/${END_YEAR3}/g"         \
    -e "s/__END_MONTH1__/${END_MONTH1}/g"       \
    -e "s/__END_MONTH2__/${END_MONTH2}/g"       \
    -e "s/__END_MONTH3__/${END_MONTH3}/g"       \
    -e "s/__END_DAY1__/${END_DAY1}/g"           \
    -e "s/__END_DAY2__/${END_DAY2}/g"           \
    -e "s/__END_DAY3__/${END_DAY3}/g"           \
    -e "s/__END_HOUR1__/${END_HOUR1}/g"         \
    -e "s/__END_HOUR2__/${END_HOUR2}/g"         \
    -e "s/__END_HOUR3__/${END_HOUR3}/g"         \
    -e "s/__END_MINUTE__/${END_MINUTE}/g"       \
    -e "s/__END_SECOND__/${END_SECOND}/g"       \
    -e "s/__BDY_INTERVAL_SECONDS__/${BDY_INTERVAL_SECONDS}/g"   \
    -e "s/__HISTORY1_INTERVAL__/${HISTORY1_INTERVAL}/g"           \
    -e "s/__HISTORY2_INTERVAL__/${HISTORY2_INTERVAL}/g"           \
    -e "s/__HISTORY3_INTERVAL__/${HISTORY3_INTERVAL}/g"           \
    -e "s/__AUXHIST3_INTERVAL__/${AUXHIST3_INTERVAL}/g"         \
    -e "s/__MAX_DOM__/${MAX_DOM}/g"             \
    -e "s/__NPROC_X__/${NPROC_X}/g"             \
    -e "s/__NPROC_Y__/${NPROC_Y}/g"             \
    -e "s/__NZ__/${NZ}/g"                     \
    -e "s/__METGRID_LEVS__/${METGRID_LEVS}/g"                     \
    -e "s/__NX1__/${NX1}/g"                     \
    -e "s/__NY1__/${NY1}/g"                     \
    -e "s/__DX1_PHY__/${DX1_PHY}/g"             \
    -e "s/__DY1_PHY__/${DY1_PHY}/g"             \
    -e "s/__NIO_TASKS__/${NIO_TASKS}/g"         \
    -e "s/__NIO_GROUPS__/${NIO_GROUPS}/g"       \
    -e "s/__RESTART_OPT__/${RESTART_OPT}/g"       \
    -e "s/__IO_FORM__/${IO_FORM}/g"       \
    $sample_namelist_wrf > $namelist_wrf


echo "Move the name list file to $CASERUN_DIR"
cp $namelist_wrf $CASERUN_DIR/namelist.input


echo "cd into $CASERUN_DIR"
cd $CASERUN_DIR


echo "linking boundary condition files in $WPS_DIR"
ln -s $WPS_DIR/met_em.*.nc .


echo "Run real.exe in 3 seconds"
#sleep 3
mpirun -n 128 ./real.exe


