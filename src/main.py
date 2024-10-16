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
    parser.add_argument('--workflow', type=str, help='The steps', required=True)
    parser.add_argument('--bdy-data-dir', type=str, help='The steps', required=True)

    args = parser.parse_args()

    pprint.pprint(args)

    case_setup = toml.load(args.setup)
    start_time = pd.Timestamp(case_setup["start_time"])
    end_time = pd.Timestamp(case_setup["end_time"])
  
    print("Boundary data dir: ", args.bdy_data_dir)
    Path(args.bdy_data_dir).mkdir(exist_ok=True, parents=True)

    ## Part 1
    
    # Step 3: generate namelist file for WPS
    
    wps_output_file = os.path.join(case_setup["WPS_DIR"], "namelist.wps")
    pleaseRun("python3 generate_namelist.py --program WPS --setup setup.toml --output {wpsoutput:s}".format(
        wpsoutput = wps_output_file,
    ))
    
    # Run WPS
    #pleaseRun(os.path.join(case_setup["WPS_DIR"], "metgrid.exe"), cwd=case_setup["WPS_DIR"])

    # Move met_dm files to     

    copy_files = []
    for filename in os.listdir(case_setup["WPS_DIR"]):

        if re.match(r"^met_em.*\.nc$", filename):
            copy_files.append(filename)

    if len(copy_files) == 0:
        raise Exception("Cannot find any boundary files!")
    else:
        print("Copying bdy files to directory %s" % (args.bdy_data_dir,))
        for filename in copy_files:
                from_filename = os.path.join(case_setup["WPS_DIR"], filename)
                to_filename = os.path.join(args.bdy_data_dir, filename)
                
                print("Copy file: %s" % (filename,))
                shutil.copyfile(from_filename, to_filename)



    # Step 4: Making interpolated climatology file

    cmb = clim_tools.climMagicBox(
        raw_mon_SST_file           = case_setup["clim"]["raw_mon_SST_file"],
        clim_SST_file              = case_setup["clim"]["clim_SST_file"],
        interpolated_clim_SST_file = os.path.join(args.bdy_data_dir, "interpolated_clim_sst.nc"),
        interpolated_grid_file     = os.path.join(args.bdy_data_dir, copy_files[0]),
    )

    print("Generating clim files if not exist")
    cmb.genClim()
    cmb.genInterpolatedClim()
    
    print("Generating projected EOF file")
    
    print("Generating perturbation files")

 
    print("Try loading clim on interpolated grid")
    test_times = [ pd.Timestamp("2021-01-01") + pd.Timedelta(days=i) for i in range(365) ]
    ds = cmb.loadClim(test_times)

    ds.to_netcdf("mytest.nc")

    # Step 5: Making interpolated EOF file
    # Step 6: Making perturbation file
    
    
         

 

    ## Part 2
    # Stage 2 :  
    

