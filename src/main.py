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
    parser.add_argument('--workflow', type=str, help='The steps', required=True)

    args = parser.parse_args()

    pprint.pprint(args)

    case_setup = toml.load(args.setup)
    start_time = pd.Timestamp(case_setup["start_time"])
    end_time = pd.Timestamp(case_setup["end_time"])
    bdy_data_dir = case_setup["caserun"]["bdy_data_dir"]
 
    print("Boundary data dir: ", bdy_data_dir)
    Path(bdy_data_dir).mkdir(exist_ok=True, parents=True)

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
        print("Copying bdy files to directory %s" % (bdy_data_dir,))
        for filename in copy_files:
                from_filename = os.path.join(case_setup["WPS_DIR"], filename)
                to_filename = os.path.join(bdy_data_dir, filename)
                
                print("Copy file: %s" % (filename,))
                shutil.copyfile(from_filename, to_filename)


    interpolated_grid_file     = os.path.join(bdy_data_dir, copy_files[0])

    # Step 4: Making interpolated climatology file

    cmb = clim_tools.climMagicBox(
        raw_mon_SST_file           = case_setup["SST_perturbation"]["raw_mon_SST_file"],
        clim_SST_file              = case_setup["SST_perturbation"]["clim_SST_file"],
        interpolated_clim_SST_file = os.path.join(bdy_data_dir, "interpolated_clim_sst.nc"),
        interpolated_grid_file     = interpolated_grid_file,
    )

    print("Generating clim files if not exist")
    cmb.genClim()
    cmb.genInterpolatedClim()
    
    # Step 5: Making interpolated EOF file
    interpolated_EOF_file = os.path.join(bdy_data_dir, "interpolated_EOF.nc")
    print("Generating projected EOF file: ", interpolated_EOF_file)
    if os.path.exists( interpolated_EOF_file ):
        print("Warning: EOF file %s already exists." % (interpolated_EOF_file,))
    else:
        print("Generating interpolated EOF file: ", interpolated_EOF_file)
        EOF_tools.genInterpolatedEOF(
            EOF_file = case_setup["SST_perturbation"]["EOF_file"],
            interpolated_grid_file = interpolated_grid_file,
            interpolated_EOF_file = os.path.join(bdy_data_dir, "interpolated_EOF.nc"),
        )
          
    print("Generating perturbation files")

    pert_configs = [
        dict(
            modes = case_setup["SST_perturbation"]["pert_modes"],
            amps = case_setup["SST_perturbation"]["pert_amps"],
        )
    ]
    
    flattened_pert_configs = []
    for pert_config in pert_configs:
        for mode in pert_config["modes"]:
            for amp in pert_config["amps"]:
                flattened_pert_configs.append(
                    dict(
                        mode=mode,
                        amp=amp,
                    )
                )
                
    for pert_config in flattened_pert_configs: 
       
        mode = pert_config["mode"]
        amp = pert_config["amp"]

        print("Mode: %d, amp: %f" % (mode, amp,))
 
        input_dir = bdy_data_dir
        output_pert_dir = os.path.join(
            bdy_data_dir,
            "EOF{mode:d}_AMP{amp:.1f}".format(
                mode = mode,
                amp = amp,
            ),
        )

        init_SST = xr.open_dataset(os.path.join(bdy_data_dir, copy_files[0]))
        pert_SST = xr.open_dataset(interpolated_EOF_file)["sst"].isel(mode=mode)
       
        pert_SST *= amp / np.nanstd(pert_SST)

        #tmp = init_SST["SST"].to_numpy()
        #tmp[tmp != 0] = 1e-6
        #init_SST["SST"][:] = tmp

        gen_SST_tools.addSSTPerturbation(
            init_SST = init_SST,
            pert_SST = pert_SST,
            input_dir = input_dir,
            output_dir = output_pert_dir,
            beg_dt = start_time,
            end_dt = end_time,
            data_interval = pd.Timedelta(seconds=case_setup["bdy"]["BDY_INTERVAL_SECONDS"]),
            cmb = cmb,
            frames_per_file = 1,
            input_prefix = "met_em.d01.",
            input_suffix = ".nc",
            output_prefix = "met_em.d01.",
            output_suffix = ".nc",
        )

        with open(os.path.join(output_pert_dir, "pert_stat.txt"), "w") as f:
            pp = pprint.PrettyPrinter(indent=4)

            pert_SST_stat = dict(
                std = np.nanstd(pert_SST),#.std(skipna=True),
                absmax = np.nanmax(np.abs(pert_SST)),
            )
     
            content = pp.pformat(pert_SST_stat)
            print(content)
            f.write(content)
            
    #print("Try loading clim on interpolated grid")
    #test_times = [ pd.Timestamp("2021-01-01") + pd.Timedelta(days=i) for i in range(365) ]
    #ds = cmb.loadClim(test_times)
    #ds.to_netcdf("mytest.nc")


    # Step 6: Making perturbation file
    
    
         

 

    ## Part 2
    # Stage 2 :  
    

