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
import gen_SST_tools
import pattern_tools

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
    parser.add_argument('--varname', type=str, help='Variable name.', required=True)
    parser.add_argument('--overwrite', action='store_true')

    args = parser.parse_args()

    pprint.pprint(args)

    case_setup = toml.load(args.setup)
    start_time = pd.Timestamp(case_setup["start_time"])
    end_time = pd.Timestamp(case_setup["end_time"])
    shared_bdy_data_dir = Path(case_setup["caserun"]["shared_bdy_data_dir"])
    individual_bdy_data_dir = Path(case_setup["caserun"]["individual_bdy_data_dir"])

    # 
    print("Making dir: ", individual_bdy_data_dir)
    individual_bdy_data_dir.mkdir(exist_ok=True, parents=True)

    # Move met_dm files to     
    bdy_files = []
    for filename in os.listdir(shared_bdy_data_dir):

        if re.match(r"^met_em.*\.nc$", filename):
            bdy_files.append(filename)

    if len(bdy_files) == 0:
        raise Exception("Cannot find any boundary files!")

    interpolated_grid_file     = os.path.join(shared_bdy_data_dir, bdy_files[0])

    # Step 4: Making interpolated climatology file

    cmb = clim_tools.climMagicBox(
        raw_mon_SST_file           = case_setup["SST_perturbation"]["raw_mon_SST_file"],
        clim_SST_file              = case_setup["SST_perturbation"]["clim_SST_file"],
        interpolated_clim_SST_file = os.path.join(shared_bdy_data_dir, "interpolated_clim_sst.nc"),
        interpolated_grid_file     = interpolated_grid_file,
    )

    print("Generating clim files if not exist")
    cmb.genClim()
    cmb.genInterpolatedClim()
    
    # Step 5: Making interpolated pattern file
    interpolated_pattern_file = os.path.join(individual_bdy_data_dir, "interpolated_pattern.nc")
    print("Generating projected pattern file: ", interpolated_pattern_file)
    if os.path.exists( interpolated_pattern_file ):
        print("Warning: pattern file %s already exists." % (interpolated_pattern_file,))
    else:
        print("Generating interpolated pattern file: ", interpolated_pattern_file)
        pattern_tools.genInterpolatedPattern(
            pattern_file = case_setup["SST_perturbation"]["pattern_file"],
            interpolated_grid_file = interpolated_grid_file,
            interpolated_pattern_file = interpolated_pattern_file,
            varname = args.varname,
        )
          
    print("Generating perturbation files")

    pert_configs = [
        dict(
            amps = case_setup["SST_perturbation"]["pert_amps"],
            pats = case_setup["SST_perturbation"]["pert_pats"],
        )
    ]
    
    flattened_pert_configs = []
    for pert_config in pert_configs:
        for pat in pert_config["pats"]:
            for amp in pert_config["amps"]:
                flattened_pert_configs.append(
                    dict(
                        amp=amp,
                        pat = pat,
                    )
                )
                    
    for pert_config in flattened_pert_configs: 
       
        amp = pert_config["amp"]
        pat = pert_config["pat"]

        print("Pat: %d, Amp: %f" % (pat, amp,))
 
        input_dir = Path(shared_bdy_data_dir)
        output_pert_dir = Path(os.path.join(
            individual_bdy_data_dir,
            "PAT{pat:d}_AMP{amp:.1f}".format(
                pat = pat,
                amp = amp,
            ),
        ))

        if output_pert_dir.exists():

            if args.overwrite:
                print("Output directory %s already exists but `--overwrite` is flagged. Keep generating the data..." % (str(output_pert_dir),))
            
            else:
                print("Output directory %s already exists. Skip." % (str(output_pert_dir),))
                continue

        init_SST = xr.open_dataset(shared_bdy_data_dir / bdy_files[0])
        print(xr.open_dataset(interpolated_pattern_file))
        pert_SST = xr.open_dataset(interpolated_pattern_file)[args.varname].isel(pattern=pat)
       
        pert_SST *= amp 

        nan_cnt = np.sum(np.isnan(pert_SST))
        print("There are %d NaN points in pattern. Replace them with 0.0.")
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

           
    

