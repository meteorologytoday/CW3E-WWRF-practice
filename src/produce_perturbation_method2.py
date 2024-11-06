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

from multiprocessing import Pool
import multiprocessing


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



def work(
    pert_config,
    case_setup,
    bdy_data_dir,
):
   
    result = dict(pert_config=pert_config, label="UNKNOWN", status="UNKNOWN")
 
    try: 
        eta     = pert_config["eta"]
        epsilon = pert_config["epsilon"]

        print("# eta = %.1f, epsilon = %.1f" % (eta, epsilon,))

        label = "eta{eta:.2f}_epsilon{epsilon:.2f}".format(
            eta = eta,
            epsilon = epsilon,
        )

        result["label"] = label

        input_dir = Path(bdy_data_dir)
        output_pert_dir = Path(bdy_data_dir) / label

        if output_pert_dir.exists():

            if args.overwrite:
                print("Output directory %s already exists but `--overwrite` is flagged. Keep generating the data..." % (str(output_pert_dir),))
            
            else:
                print("Output directory %s already exists. Skip." % (str(output_pert_dir),))
                result["status"] = "DIRECTORY_EXISTS"
                return result

        output_pert_dir.mkdir(exist_ok=True, parents=True)

        """
        with open(output_pert_dir / "pert_stat.txt", "w") as f:
            pp = pprint.PrettyPrinter(indent=4)

            pert_SST_stat = dict(
                std = np.nanstd(pert_SST),#.std(skipna=True),
                absmax = np.nanmax(np.abs(pert_SST)),
            )
     
            content = pp.pformat(pert_SST_stat)
            print(content)
            f.write(content)
        """

        gen_SST_tools.addSSTPerturbationMethod2(
            epsilon    = epsilon,
            eta        = eta,
            input_dir  = input_dir,
            output_dir = str(output_pert_dir),
            beg_dt     = start_time,
            end_dt     = end_time,
            data_interval = pd.Timedelta(seconds=case_setup["bdy"]["BDY_INTERVAL_SECONDS"]),
            cmb = cmb,
            frames_per_file = 1,
            input_prefix = "met_em.d01.",
            input_suffix = ".nc",
            output_prefix = "met_em.d01.",
            output_suffix = ".nc",
        )

        result["status"] = "OK"

    except Exception as e:

        import traceback
        traceback.print_exc()

        result["status"] = "ERROR"

    return result


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='This high-level program oversees the entire process from downloading data, generating boundary files, adding perturbations to generating cases.')
    parser.add_argument('--setup', type=str, help='Setup TOML file.', required=True)
    parser.add_argument('--overwrite', action='store_true')
    parser.add_argument('--nproc', type=int, help='Number of tasks.', default=2)

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
    
    print("Generating perturbation files")
    pert_configs = [
        dict(
            etas     = case_setup["SST_perturbation"]["pert_etas"],
            epsilons = case_setup["SST_perturbation"]["pert_epsilons"],
        )
    ]
    
    flattened_pert_configs = []
    for pert_config in pert_configs:
        for eta in pert_config["etas"]:
            for epsilon in pert_config["epsilons"]:
                flattened_pert_configs.append(
                    dict(
                        epsilon=epsilon,
                        eta=eta,
                    )
                )
   

    input_args = []
             
    for pert_config in flattened_pert_configs: 
        
        input_args.append((pert_config, case_setup, bdy_data_dir)) 

    
    failed_cases = []
    with Pool(processes=args.nproc) as pool:

        results = pool.starmap(work, input_args)

        for i, result in enumerate(results):
            if result['status'] != 'OK':
                print('!!! Failed to generate output for case : %s => %s.' % (result['label'], result['status']))
                failed_cases.append(dict(result))


    print("Tasks finished.")

    """
    if len(failed_cases) > 0:
        print("Failed cases: ")
        for i, failed_case in enumerate(failed_cases):
            print("%d : %s" % (i+1, failed_case,))
   
    else:
        print("Congrats! Everything works!")     
    print("Done")
    """
    
