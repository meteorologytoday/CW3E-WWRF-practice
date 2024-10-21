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
import substitution_tools

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
    parser.add_argument('--template-dir', type=str, help='Submit file template.', default="/home/t2hsu/projects/CW3E-WWRF-practice/templates")
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
        
        print("##### Doing the case %d ##### " % (i,))
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


        print("Generating case {casename:s} under {caserun_root:s}.".format(
            casename = casename,
            caserun_root = str(caserun_root),
        ))

        if (not args.overwrite) and caserun_fullpath.exists():
            print("Error: Directory %s already exists. " % (str(caserun_fullpath),))
            continue

        caserun_fullpath.mkdir(exist_ok=True)
        
        template_dir = Path(args.template_dir)

        submit_detail_file = caserun_fullpath / "submit_detail.toml"
        print("Making file for resubmit purpose: %s" % (str(submit_detail_file),))
        with open(submit_detail_file, "w") as f:
            toml.dump(dict(
                start_time = str(start_time),
                end_time = str(end_time),
                submit_count = 0,
                domain = 1,
                resubmit_interval_hr = case_setup["resubmit_interval_hr"],
                input_nml = "namelist.input.original", 
                output_nml = "namelist.input",
                submit_file = "submit.sh", 
            ), f)
        
        submit_engine = template_dir / "submit_engine.py"
        print("Copy file: ", submit_engine)
        shutil.copyfile(submit_engine, caserun_fullpath / submit_engine.name)
        
 
        print("Making softlinks of boundary files in %s" % (str(pert_file_dir),))
        for fileobj in pert_file_dir.glob("met_em*.nc"):
            print("Making softlink for file: ", str(fileobj))
            (caserun_fullpath / fileobj.name).symlink_to(fileobj)
        

        namelist_WRF = caserun_fullpath / "namelist.input.original"
        print("Making namelist: ", str(namelist_WRF)) 
        pleaseRun("python3 generate_namelist.py --setup={setup:s} --program=WRF --output={output:s}".format(
            setup  = args.setup,
            output = str(namelist_WRF), 
        )) 


       
        runwrf_file_src = template_dir / "run_wrf.sh"
        runwrf_file_dst = caserun_fullpath / runwrf_file_src.name
        print("Generating %s" % (runwrf_file_src.name,))
        shutil.copyfile(runwrf_file_src, runwrf_file_dst)
        os.chmod(runwrf_file_dst, mode=0o755)

        submit_file = caserun_fullpath / "submit.sh"
        print("Making submit file %s" % (str(submit_file),))
        submit_file_content = open(template_dir / "submit.sh").read()
        submit_file_content = substitution_tools.stringSubstitution(
            submit_file_content,
            dict(
                PARTITION = "cw3e-compute",
                NODES = 1,
                NPROC = 128,
                JOBNAME = casename,
            )
        )
        with open(submit_file, "w") as f:
            f.write(submit_file_content)
        
        os.chmod(submit_file, mode=0o755)


        # copy a scaffold
        # If use_symbolic is True, then symbolic link will be copy
        # rather than the file content
        print("Copying files from scaffold directory: ", str(caserun_scaffold))
        shutil.copytree(
            caserun_scaffold,
            caserun_fullpath,
            symlinks=args.use_symbolic,
            ignore_dangling_symlinks=args.use_symbolic,
            dirs_exist_ok=True, 
        )
        
