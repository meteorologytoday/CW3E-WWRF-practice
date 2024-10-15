import numpy as np
import re

def namelistSubstitution(namelist_content, mapping):
    
    for keyword, content in mapping.items():
        searched_text = "__%s__" % (keyword,)
        
        p = re.compile(searched_text)
        if re.search(p, namelist_content):

            if isinstance(content, str):
                substr = content
            elif isinstance(content, int):
                substr = "%d" % (content,)
            elif isinstance(content, float):
                substr = "%f" % (content,)
                
            

            print("Replacing %s => %s" % (searched_text, substr,))
            namelist_content = re.sub(p, substr, namelist_content)
        else:
            print("Cannot find %s" % (searched_text,))

    return namelist_content


sample_namelist_wps = "/home/t2hsu/projects/CW3E-WWRF-practice/namelists/west-wrf-namelist.wps"
sample_namelist_wrf = "/home/t2hsu/projects/CW3E-WWRF-practice/namelists/west-wrf-namelist.input.3dom"


case_setup = dict(
    WPS_DIR     = "/home/t2hsu/models/WRF_gcc/WPS-4.5",
    CASERUN_DIR = "/expanse/lustre/scratch/t2hsu/temp_project/WRF_RUNS/test_gcc_step2",
    START_DATE = "",
    data_dir = "/home/t2hsu/projects/CW3E-WWRF-practice/data/WRF_ERA5/",
    namelist = dict(
        WPS = "west-wrf-namelist.completed.wps",
        WRF = "west-wrf-namelist.completed.wrf",
    ),
    Vtable = "ungrib/Variable_Tables/Vtable.ECMWF",

    start_time = "2022-01-07T00:00:00",
    end_time   = "2022-01-08T00:00:00",
)

WRF_namelist_setup = dict(

    BDY_INTERVAL_SECONDS=10800,
    RESTART_OPT="F",

    # in minutes
    HISTORY1_INTERVAL=60,
    HISTORY2_INTERVAL=999999,
    HISTORY3_INTERVAL=999999,
    AUXHIST3_INTERVAL=360,

    MAX_DOM=1,
    NZ=100,
    NX1=828,
    NY1=570,
    DX1_DEG=0.08,
    DY1_DEG=0.08,
    DX1_PHY=8894.198,
    DY1_PHY=8894.198,

    METGRID_LEVS=8,

    NPROC_X=16,
    NPROC_Y=8,

    NIO_TASKS=0,
    NIO_GROUPS=1,

    PREFIX="ERA5",

    IO_FORM=2, # netcdf
       
)

print("Generating namelist file:", sample_namelist_wps)
namelist_file_content = namelistSubstitution( open(sample_namelist_wps, 'r').read(), WRF_namelist_setup)

print("# After substitution")
print(namelist_file_content)


"""
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
"""


"""
data = data.replace

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



class CLI:


funcs = [
    dict(
        "Configure WPS",
        "Configure WRF",
    ),
]



"""
