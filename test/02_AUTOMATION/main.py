import pandas as pd
import numpy as np
import argparse
import toml
import re
import pprint


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
            print("Warning: Cannot find %s" % (searched_text,))

    return namelist_content



if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--setup', type=str, help='Setup TOML file.', required=True)
    parser.add_argument('--sample-namelist-wps', type=str, help='Sample WPS file.', default="/home/t2hsu/projects/CW3E-WWRF-practice/namelists/west-wrf-namelist.wps")
    parser.add_argument('--sample-namelist-wrf', type=str, help='Sample WPS file.', default="/home/t2hsu/projects/CW3E-WWRF-practice/namelists/west-wrf-namelist.input.3dom")

    args = parser.parse_args()

    pprint.pprint(args)

    case_setup = toml.load(args.setup)


    start_time = pd.Timestamp(case_setup["start_time"])
    end_time = pd.Timestamp(case_setup["end_time"])

    WPS_namelist_setup = dict(

        START_DATE = start_time.strftime("%Y-%m-%d_%H:%M:%S"),
        END_DATE1 = (SHARED_END_DATE := end_time.strftime("%Y-%m-%d_%H:%M:%S")),
        END_DATE2 = SHARED_END_DATE,
        END_DATE3 = SHARED_END_DATE,
       
        MAX_DOM=1,
        NX1=case_setup["grid"]["NX"],
        NY1=case_setup["grid"]["NY"],
        DX1_DEG=case_setup["grid"]["DX"],
        DY1_DEG=case_setup["grid"]["DY"],

        PREFIX="ERA5",
    )

    WRF_namelist_setup = dict(

        START_MONTH  = start_time.strftime("%m"),
        START_DAY    = start_time.strftime("%d"),
        START_HOUR   = start_time.strftime("%H"),
        START_MINUTE = start_time.strftime("%M"),
        START_SECOND = start_time.strftime("%S"),

        END_YEAR1   = (END_YEAR  := end_time.strftime("%Y")),
        END_MONTH1  = (END_MONTH := end_time.strftime("%m")),
        END_DAY1    = (END_DAY   := end_time.strftime("%d")),
        END_HOUR1   = (END_HOUR  := end_time.strftime("%H")),
        END_MINUTE = end_time.strftime("%M"),
        END_SECOND = end_time.strftime("%S"),

        END_YEAR2 = END_YEAR,
        END_YEAR3 = END_YEAR,
        END_MONTH2 = END_MONTH,
        END_MONTH3 = END_MONTH,
        END_DAY2 = END_DAY,
        END_DAY3 = END_DAY,
        END_HOUR2 = END_HOUR,
        END_HOUR3 = END_HOUR,

        BDY_INTERVAL_SECONDS=10800,
        RESTART_OPT="F",

        # in minutes
        HISTORY1_INTERVAL=60,
        HISTORY2_INTERVAL=999999,
        HISTORY3_INTERVAL=999999,
        AUXHIST3_INTERVAL=360,

        MAX_DOM=1,
        NZ=case_setup["grid"]["NZ"],
        NX1=case_setup["grid"]["NX"],
        NY1=case_setup["grid"]["NY"],
        DX1_PHY=case_setup["grid"]["DX_PHY"],
        DY1_PHY=case_setup["grid"]["DY_PHY"],

        METGRID_LEVS=8,

        NPROC_X=16,
        NPROC_Y=8,

        NIO_TASKS=0,
        NIO_GROUPS=1,

        IO_FORM=2, # netcdf
           
    )

    print("##### Generating WPS namelist file:", args.sample_namelist_wps)
    namelist_file_content = namelistSubstitution( open(args.sample_namelist_wps, 'r').read(), WPS_namelist_setup)

    print("# After substitution")
    print(namelist_file_content)

    print("##### Generating WRF namelist file:", args.sample_namelist_wrf)
    namelist_file_content = namelistSubstitution( open(args.sample_namelist_wrf, 'r').read(), WRF_namelist_setup)

    print("# After substitution")
    print(namelist_file_content)

