#!/bin/bash

CASERUN_DIR=/expanse/lustre/scratch/t2hsu/temp_project/WRF_RUNS/test_gcc_step2
#CASERUN_DIR=/expanse/lustre/scratch/t2hsu/temp_project/WRF_RUNS/test_v4.6
#/home/t2hsu/models/WRF/WESTWRF/WRFV4.4.1/run
WPS_DIR=/home/t2hsu/models/WRF_gcc/WPS-4.5
CWD=`pwd`

data_dir=/home/t2hsu/projects/CW3E-WWRF-practice/data/WRF_ERA5/
sample_namelist_wps=/home/t2hsu/projects/CW3E-WWRF-practice/namelists/west-wrf-namelist.wps
sample_namelist_wrf=/home/t2hsu/projects/CW3E-WWRF-practice/namelists/west-wrf-namelist.input.3dom
#sample_namelist_wrf=/home/t2hsu/projects/CW3E-WWRF-practice/namelists/namelist.input.original

namelist_wps=west-wrf-namelist.completed.wps
namelist_wrf=west-wrf-namelist.completed.wrf

Vtable=ungrib/Variable_Tables/Vtable.ECMWF

START_YEAR=2022
START_MONTH=01
START_DAY=07
START_HOUR=00
START_MINUTE=00
START_SECOND=00

END_YEAR1=2022
END_MONTH1=01
END_DAY1=08
END_HOUR1=00
END_MINUTE=00
END_SECOND=00

END_YEAR2=$END_YEAR1
END_MONTH2=$END_MONTH1
END_DAY2=$END_DAY1
END_HOUR2=$END_HOUR1

END_YEAR3=$END_YEAR1
END_MONTH3=$END_MONTH1
END_DAY3=$END_DAY1
END_HOUR3=$END_HOUR1


START_DATE=${START_YEAR}-${START_MONTH}-${START_DAY}_${START_HOUR}:${START_MINUTE}:${START_SECOND}

END_DATE1=${END_YEAR1}-${END_MONTH1}-${END_DAY1}_${END_HOUR1}:${END_MINUTE}:${END_SECOND}
END_DATE2=${END_DATE1}
END_DATE3=${END_DATE2}

BDY_INTERVAL_SECONDS=10800
RESTART_OPT=F

# in minutes
HISTORY1_INTERVAL=60
HISTORY2_INTERVAL=999999
HISTORY3_INTERVAL=999999
AUXHIST3_INTERVAL=360

MAX_DOM=1
NZ=100

NX1=828
NY1=570
DX1_DEG=0.08
DY1_DEG=0.08
DX1_PHY=8894.198
DY1_PHY=8894.198

#NX1=414
#NY1=285
#DX1_DEG=0.16
#DY1_DEG=0.16
#DX1_PHY=8894.198
#DY1_PHY=8894.198


#NZ=100
#NX1=207
#NY1=142
#DX1_DEG=0.32
#DY1_DEG=0.32
#DX1_PHY=35576.79
#DY1_PHY=35576.79

METGRID_LEVS=8

NPROC_X=16
NPROC_Y=8

NIO_TASKS=0
NIO_GROUPS=1

PREFIX=ERA5

IO_FORM=2 # netcdf
