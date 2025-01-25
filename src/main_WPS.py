import xarray as xr
import pandas as pd
import numpy as np
import argparse
import toml
import re
import pprint
import subprocess, shlex
import os,shutil
from pathlib import Path

import clim_tools
import EOF_tools
import gen_SST_tools

def pleaseRun(cmds, cwd=None):

    if isinstance(cmds, str):
        cmds = [cmds,]

    for cmd in cmds:
        cmd_split = shlex.split(cmd)
        print(">> ", cmd)

        #subprocess.run(cmd_split)

        with subprocess.Popen(
            cmd_split,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            text=True,
            universal_newlines=True,
            encoding='utf-8',
            cwd=cwd,
        ) as p:
       
            for line in p.stdout:
                print(line, end='', flush=True)

            p.wait()

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='This high-level program oversees the entire process from downloading data, generating boundary files, adding perturbations to generating cases.')
    parser.add_argument('--setup', type=str, help='Setup TOML file.', required=True)
    parser.add_argument('--nproc', type=int, help='If we are using multi-processors.', default=1)
    parser.add_argument('--workflow', type=str, help='The steps', required=True)

    args = parser.parse_args()

    pprint.pprint(args)

    case_setup = toml.load(args.setup)
    start_time = pd.Timestamp(case_setup["start_time"])
    end_time = pd.Timestamp(case_setup["end_time"])
    shared_bdy_data_dir = case_setup["caserun"]["shared_bdy_data_dir"]
 
    print("Shared boundary data dir: ", shared_bdy_data_dir)
    Path(shared_bdy_data_dir).mkdir(exist_ok=True, parents=True)

    ## Part 1
    
    # Step 3: generate namelist file for WPS
    WPS_DIR =  Path(case_setup["WPS_DIR"])
    wps_output_file = WPS_DIR / "namelist.wps"
    pleaseRun("python3 generate_namelist.py --program WPS --setup setup.toml --output {wpsoutput:s}".format(
        wpsoutput = str(wps_output_file),
    ))
    
    # Run WPS

    #def wrapMPIrun(cmd_str):
    #    if args.nproc == 1:
    #        return cmd_str
    #    else:
    #        return "mpirun -np %d %s" % (args.nproc, cmd_str,)


    pleaseRun(str(WPS_DIR / "geogrid.exe"), cwd=str(WPS_DIR))
    pleaseRun("%s %s" % (
        str(WPS_DIR / "link_grib.csh"),
        case_setup["data_dir"],
    ), cwd=str(WPS_DIR))
    pleaseRun(str(WPS_DIR / "ungrib.exe"), cwd=str(WPS_DIR))
    pleaseRun(str(WPS_DIR / "metgrid.exe"), cwd=str(WPS_DIR))
    
    # Move met_dm files to     

    copy_files = []
    for filename in os.listdir(case_setup["WPS_DIR"]):

        if re.match(r"^met_em.*\.nc$", filename):
            copy_files.append(filename)

    if len(copy_files) == 0:
        raise Exception("Cannot find any boundary files!")
    else:
        print("Copying bdy files to directory %s" % (shared_bdy_data_dir,))
        for filename in copy_files:
                from_filename = os.path.join(case_setup["WPS_DIR"], filename)
                to_filename = os.path.join(shared_bdy_data_dir, filename)
                
                print("Copy file: %s" % (filename,))
                shutil.copyfile(from_filename, to_filename)


