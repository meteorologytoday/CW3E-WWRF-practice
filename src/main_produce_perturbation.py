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

    args = parser.parse_args()

    pprint.pprint(args)

    case_setup = toml.load(args.setup)
    start_time = pd.Timestamp(case_setup["start_time"])
    end_time = pd.Timestamp(case_setup["end_time"])
    bdy_data_dir = Path(case_setup["caserun"]["bdy_data_dir"])
 
    # Move met_dm files to     
    bdy_files = []
    for filename in os.listdir(bdy_data_dir):

        if re.match(r"^met_em.*\.nc$", filename):
            bdy_files.append(filename)

    if len(bdy_files) == 0:
        raise Exception("Cannot find any boundary files!")

    interpolated_grid_file     = os.path.join(bdy_data_dir, bdy_files[0])

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
 
        input_dir = Path(bdy_data_dir)
        output_pert_dir = Path(os.path.join(
            bdy_data_dir,
            "EOF{mode:d}_AMP{amp:.1f}".format(
                mode = mode,
                amp = amp,
            ),
        ))

        if output_pert_dir.exists():
            print("Output directory %s already exists. Skip." % (str(output_pert_dir),))
            continue

        init_SST = xr.open_dataset(bdy_data_dir / bdy_files[0])
        pert_SST = xr.open_dataset(interpolated_EOF_file)["sst"].isel(mode=mode)
       
        pert_SST *= amp / np.nanstd(pert_SST)

        nan_cnt = np.sum(np.isnan(pert_SST))
        print("There are %d NaN points in EOF. Replace them with 0.0.")
        pert_SST = pert_SST.fillna(0.0)

        #tmp = init_SST["SST"].to_numpy()
        #tmp[tmp != 0] = 1e-6
        #init_SST["SST"][:] = tmp

        output_pert_dir.mkdir(exist_ok=True, parents=True)

        with open(output_pert_dir / "pert_stat.txt", "w") as f:
            pp = pprint.PrettyPrinter(indent=4)

            pert_SST_stat = dict(
                std = np.nanstd(pert_SST),#.std(skipna=True),
                absmax = np.nanmax(np.abs(pert_SST)),
            )
     
            content = pp.pformat(pert_SST_stat)
            print(content)
            f.write(content)
 
        gen_SST_tools.addSSTPerturbation(
            init_SST = init_SST,
            pert_SST = pert_SST,
            input_dir = input_dir,
            output_dir = str(output_pert_dir),
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

           
    

