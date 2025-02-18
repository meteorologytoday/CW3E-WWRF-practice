import pandas as pd
import numpy as np
import argparse
import toml
import re
import pprint
from pathlib import Path
def searchSubstitution(s, verbose = True):
        
    matches = re.findall(r"__[a-zA-Z_0-9]+__", s)
   
    if verbose:
        print("Found the following namelist substitution:")
        for i, match in enumerate(matches):
            print("[%d] %s" % (i+1, match))

    return matches


def namelistSubstitution(namelist_content, mapping, verbose=False):
    
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
                
            

            verbose and print("Replacing %s => %s" % (searched_text, substr,))
            namelist_content = re.sub(p, substr, namelist_content)
        else:
            print("Warning: Cannot find %s" % (searched_text,))

    return namelist_content


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='This program generates namelist files for WPS and WRF from a setup TOML file.')
    parser.add_argument('--setup', type=str, help='Setup TOML file.', required=True)
    parser.add_argument('--program', type=str, help='Either WRF or WPS.', choices=["WRF", "WPS"], required=True)
    parser.add_argument('--output', type=str, help='Output file.', default="")
    parser.add_argument('--print-outcome', action="store_true")
    parser.add_argument('--sample-namelist-wps', type=str, help='Sample WPS file.', default="/home/t2hsu/projects/CW3E-WWRF-practice/namelists/west-wrf-namelist.wps")
    parser.add_argument('--sample-namelist-wrf', type=str, help='Sample WPS file.', default="/home/t2hsu/projects/CW3E-WWRF-practice/namelists/west-wrf-namelist.input.3dom")
    parser.add_argument('--verbose', action="store_true")

    args = parser.parse_args()

    pprint.pprint(args)

    case_setup = toml.load(args.setup)
    start_time = pd.Timestamp(case_setup["start_time"])
    end_time = pd.Timestamp(case_setup["end_time"])

    if args.program == "WPS":
        
        sample_namelist = args.sample_namelist_wps
        
        namelist_setup = dict(

            START_DATE = start_time.strftime("%Y-%m-%d_%H:%M:%S"),
            END_DATE1 = (SHARED_END_DATE := end_time.strftime("%Y-%m-%d_%H:%M:%S")),
            END_DATE2 = SHARED_END_DATE,
            END_DATE3 = SHARED_END_DATE,
           
            MAX_DOM=1,
            NX1=case_setup["grid"]["NX"],
            NY1=case_setup["grid"]["NY"],
            DX1_DEG=case_setup["grid"]["DX"],
            DY1_DEG=case_setup["grid"]["DY"],
            BDY_INTERVAL_SECONDS = case_setup["bdy"]["BDY_INTERVAL_SECONDS"],
            PREFIX="ERA5",

        )
   

    elif args.program == "WRF":
        
        sample_namelist = args.sample_namelist_wrf
        
        namelist_setup = dict(

            START_YEAR   = start_time.strftime("%Y"),
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

            RESTART_OPT="F",
            RESTART_INTERVAL_MIN = case_setup["restart_interval_min"],

            # in minutes
            HISTORY1_INTERVAL=case_setup["WRF"]["HISTORY_INTERVAL"],
            HISTORY2_INTERVAL=999999,
            HISTORY3_INTERVAL=999999,
            AUXHIST3_INTERVAL=360,

            MAX_DOM=1,
            NZ=case_setup["grid"]["NZ"],
            NX1=case_setup["grid"]["NX"],
            NY1=case_setup["grid"]["NY"],
            DX1_PHY=case_setup["grid"]["DX_PHY"],
            DY1_PHY=case_setup["grid"]["DY_PHY"],

            METGRID_LEVS=case_setup["grid"]["METGRID_LEVS"],
            
            BDY_INTERVAL_SECONDS = (BDY_INTERVAL_SECONDS := case_setup["bdy"]["BDY_INTERVAL_SECONDS"]),

            NPROC_X=case_setup["grid"]["NPROC_X"],
            NPROC_Y=case_setup["grid"]["NPROC_Y"],

            NIO_TASKS=0,
            NIO_GROUPS=1,

            IO_FORM=2, # netcdf

            SST_UPDATE_INTERVAL_MIN = int(BDY_INTERVAL_SECONDS / 60), 

            SSTUPDATE = case_setup["SST"]["SSTUPDATE"],
            SSTSKIN = case_setup["SST"]["SSTSKIN"],

        )


    namelist_file_content = open(sample_namelist, 'r').read()
   
    if args.verbose: 
        matches = searchSubstitution(namelist_file_content, verbose=True)

    print("##### Generating WPS namelist from sample file:", sample_namelist)
    namelist_file_content = namelistSubstitution(namelist_file_content, namelist_setup)

    if args.print_outcome:
        print("# After substitution")
        print(namelist_file_content)


    # Check if there's any missing
    matches = searchSubstitution(namelist_file_content, verbose=args.verbose)
    if len(matches) == 0:
        print("All variables are succefully substituted.")

    else:
        print("Warning: Not all variables get substituted. I list them below:")
        
        for i, match in enumerate(matches):
            print("[%d] %s" % (i+1, match))
    

    if args.output != "":

        output_file = Path(args.output)
        if output_file.exists():
            print("Remove pre-existing file: ", str(output_file))
            Path.unlink(missing_ok=False) 

        print("Write to file: ", str(output_file))
        with open(output_file, "w") as f:
            f.write(namelist_file_content)



