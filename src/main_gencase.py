import xarray as xr
import pandas as pd
import numpy as np
import argparse
import toml
import re
import pprint
import subprocess, shlex
import os,shutil,glob
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
    parser.add_argument('--overwrite', action="store_true")
    parser.add_argument('--use-symbolic', action="store_true")

    args = parser.parse_args()

    pprint.pprint(args)

    case_setup = toml.load(args.setup)
    start_time = pd.Timestamp(case_setup["start_time"])
    end_time = pd.Timestamp(case_setup["end_time"])
    bdy_data_dir = Path(case_setup["caserun"]["bdy_data_dir"])
 
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

    # For each case                
    
    caserun_root = Path(case_setup["caserun"]["caserun_root"])
    caserun_scaffold = Path(case_setup["caserun"]["caserun_scaffold"])
    print("Generating case caserun dirs.")
    print("Caserun root: ", caserun_root)
    print("Scaffold directory: ", caserun_scaffold)
    
    if caserun_root.exists():
        print("Warning: Directory `caserun_root` = %s already exists." % (caserun_root,))
   
    caserun_root.mkdir(exist_ok=True, parents=True)
    
    for i, pert_config in enumerate(flattened_pert_configs): 
        
        print("Doing the case %d" % (i,))
        mode = pert_config["mode"]
        amp = pert_config["amp"]



        pert_label = "EOF{mode:d}_AMP{amp:.1f}".format(
            mode = mode,
            amp = amp,
        )

        casename = "{label:s}_{pert_label:s}".format(
            label = case_setup["caserun"]["caserun_label"],
            pert_label = pert_label,
        )

        caserun_fullpath = caserun_root / casename
        pert_file_dir = bdy_data_dir / pert_label

        # copy a scaffold
        print("Generating case {casename:s} under {caserun_root:s}.".format(
            casename = casename,
            caserun_root = str(caserun_root),
        ))

        if (not args.overwrite) and caserun_fullpath.exists():
            print("Error: Directory %s already exists. " % (str(caserun_fullpath),))
            continue

        # If use_symbolic is True, then symbolic link will be copy
        # rather than the file content 
        shutil.copytree(
            caserun_scaffold,
            caserun_fullpath,
            symlinks=args.use_symbolic,
            ignore_dangling_symlinks=args.use_symbolic,
            
        )
        
        print("Making softlinks of boundary files in %s" % (str(pert_file_dir),))
        for fileobj in pert_file_dir.glob("met_em*.nc"):
            print("Making softlink for file: ", str(fileobj))
            (caserun_fullpath / fileobj.name).symlink_to(fileobj)
        
         
    

