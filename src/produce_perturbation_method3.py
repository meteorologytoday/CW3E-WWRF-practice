
from multiprocessing import Pool
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

def work(details):

    overwrite               = details["overwrite"]
    pat                     = details["pat"]
    amp                     = details["amp"]
    individual_bdy_data_dir = details["individual_bdy_data_dir"]
    bdy_files               = details["bdy_files"]
    interpolated_grid_file  = details["interpolated_grid_file"]
    BDY_INTERVAL_SECONDS    = details["BDY_INTERVAL_SECONDS"]
    cmb                     = details["cmb"]
    start_time = details["start_time"]
    end_time   = details["end_time"]

    input_dir = Path(shared_bdy_data_dir)

    result = dict(
        details=details,
        status="UNKNOWN", 
    )

    try:

        output_pert_dir = Path(os.path.join(
            individual_bdy_data_dir,
            "PAT{pat:d}_AMP{amp:.1f}".format(
                pat = pat,
                amp = amp,
            ),
        ))


        do_work = True
        if output_pert_dir.exists():

            if overwrite:
                print("Output directory %s already exists but `--overwrite` is flagged. Keep generating the data..." % (str(output_pert_dir),))
                            
            else:
                print("Output directory %s already exists. Skip." % (str(output_pert_dir),))
                do_work = False
            
                result['status'] = 'SKIP'

        if do_work:
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
                data_interval = pd.Timedelta(seconds=BDY_INTERVAL_SECONDS),
                cmb = cmb,
                frames_per_file = 1,
                input_prefix = "met_em.d01.",
                input_suffix = ".nc",
                output_prefix = "met_em.d01.",
                output_suffix = ".nc",
            )
        
            print("[PAT=%.1f, AMP=%.1f] Done. " % (pat, amp,))

            result['status'] = 'OK'
    except Exception as e:
        
        result['status'] = 'ERROR'
        traceback.print_stack()
        traceback.print_exc()
        print(e)



    return result           




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
    parser.add_argument('--nproc', type=int, help='Number of processors.', default=1)
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
 
    failed_cases = []
    input_args = []
    for pert_config in flattened_pert_configs: 
       
        amp = pert_config["amp"]
        pat = pert_config["pat"]

        print("Pat: %d, Amp: %f" % (pat, amp,))
 
        details = dict(
            overwrite = args.overwrite,
            pat = pert_config["pat"],
            amp = pert_config["amp"],
            individual_bdy_data_dir = individual_bdy_data_dir,
            bdy_files = bdy_files,
            interpolated_pattern_file = interpolated_pattern_file,
            BDY_INTERVAL_SECONDS = case_setup["bdy"]["BDY_INTERVAL_SECONDS"],
            start_time = start_time,
            end_time = end_time,
            cmb = cmb,
            interpolated_grid_file = interpolated_grid_file,
        )

        input_args.append((details,))

    with Pool(processes=args.nproc) as pool:

        results = pool.starmap(work, input_args)

        for i, result in enumerate(results):
            if result['status'] != 'OK':
                print('!!! Failed to generate case of %s.' % (",".join(result['details']['label'],)))
                failed_cases.append(result['details']['label'])


    print("Tasks finished.")

    print("Failed output files: ")
    for i, failed_case_label in enumerate(failed_cases):
        print("%d : %s" % (i+1, failed_case_label,))

    print("Done.")
