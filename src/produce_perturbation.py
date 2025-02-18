import traceback
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

def create_soft_links(source_dir, target_dir, skip_if_exists=False, filelist=None):
    """Creates soft links for all files in source_dir within target_dir."""
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    if filelist is None:
        filelist = os.listdir(source_dir)

    for filename in filelist:
        source_path = os.path.join(source_dir, filename)
    
        if os.path.exists(source_path):
            target_path = os.path.join(target_dir, filename)
            
            if os.path.exists(target_path):

                if skip_if_exists == False:
                    raise Exception("File %s already exists." % (target_path,))
            else:
                os.symlink(source_path, target_path)
            print(f"Created soft link: {target_path} -> {source_path}")


def work(details):

    label                   = details["label"]
    overwrite               = details["overwrite"]
    pat                     = details["pat"]
    amp                     = details["amp"]
    init_SST_file           = details["init_SST_file"]
#    interpolated_grid_file  = details["interpolated_grid_file"]
    BDY_INTERVAL_SECONDS    = details["BDY_INTERVAL_SECONDS"]
    cmb                     = details["cmb"]
    start_time = details["start_time"]
    end_time   = details["end_time"]
    input_bdy_data_dir  = Path(details["input_bdy_data_dir"])
    output_bdy_data_dir = Path(details["output_bdy_data_dir"])
    method = details["method"]
    pert_SST_varname = details["pert_SST_varname"]
    bdy_SST_varname = details["bdy_SST_varname"]

    result = dict(
        details=details,
        status="UNKNOWN", 
    )

    try:


        do_work = True
        if output_bdy_data_dir.exists():

            if overwrite:
                print("Output directory %s already exists but `--overwrite` is flagged. Keep generating the data..." % (str(output_bdy_data_dir),))
                            
            else:
                print("Output directory %s already exists. Skip." % (str(output_bdy_data_dir),))
                do_work = False
            
                result['status'] = 'SKIP'

        if do_work:
            
            init_SST = xr.open_dataset(input_bdy_data_dir / bdy_files[0])
            pert_SST = xr.open_dataset(interpolated_pattern_file)[pert_SST_varname].isel(pattern=pat)
            pert_SST *= amp 

            nan_cnt = np.sum(np.isnan(pert_SST))
            print("There are %d NaN points in pattern. Replace them with 0.0.")
            pert_SST = pert_SST.fillna(0.0)

            output_bdy_data_dir.mkdir(exist_ok=True, parents=True)


            with open(output_bdy_data_dir / "pert_stat.txt", "w") as f:
                pp = pprint.PrettyPrinter(indent=4)

                pert_SST_stat = dict(
                    std = np.nanstd(pert_SST),#.std(skipna=True),
                    absmax = np.nanmax(np.abs(pert_SST)),
                )
         
                content = pp.pformat(pert_SST_stat)
                print(content)
                f.write(content)

            _end_time = end_time

            if method == "fixed":
                # For fixed_anom method, we only need to tweak the
                # First snapshot, then keep it constant
                _end_time = start_time

            gen_SST_tools.addSSTPerturbation(
                init_SST = init_SST,
                pert_SST = pert_SST,
                input_dir = input_bdy_data_dir,
                output_dir = str(output_bdy_data_dir),
                beg_dt = start_time,
                end_dt = _end_time,
                data_interval = pd.Timedelta(seconds=BDY_INTERVAL_SECONDS),
                cmb = cmb,
                SST_varname = bdy_SST_varname,
                frames_per_file = 1,
                input_prefix = "met_em.d01.",
                input_suffix = ".nc",
                output_prefix = "met_em.d01.",
                output_suffix = ".nc",
            )

            if method == "fixed":

                # For fixed_anom method, we only need to tweak the
                # First snapshot, then make rest of files softlinks
                create_soft_links(
                    input_bdy_data_dir,
                    output_bdy_data_dir,
                    skip_if_exists = True,
                )
                
 
            print("[%s] Done. " % (label,))

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
    parser.add_argument('--bdy-SST-varname', type=str, help='Variable name for sst. It can be SKINTEMP in GEFS', required=True, choices=["SST", "SKINTEMP"])
    parser.add_argument('--pert-SST-varname', type=str, help='Variable name for sst perturbation file', required=True)
    parser.add_argument('--method', type=str, help='Variable name.', required=True, choices=["fixed", "persistent_anom"])
    parser.add_argument('--nproc', type=int, help='Number of processors.', default=1)
    parser.add_argument('--overwrite', action='store_true')

    args = parser.parse_args()

    pprint.pprint(args)

    case_setup = toml.load(args.setup)
    start_time = pd.Timestamp(case_setup["start_time"])
    end_time = pd.Timestamp(case_setup["end_time"])
    
    ensemble_members = case_setup["ensemble"]["ensemble_members"]
    input_bdy_data_root    = Path(case_setup["SST_perturbation"]["original_bdy_data_root"])

    caserun_root   = Path(case_setup["caserun"]["caserun_root"])
    if "bdy_data_root" in case_setup["caserun"]:
        output_bdy_data_root   = Path(case_setup["caserun"]["bdy_data_root"])
    else:
        output_bdy_data_root = caserun_root / "bdy"
        print("Option `bdy_data_root` does not exist. Assume it is under the `caserun_root`. ")
        print("Set `bdy_data_root` = %s" % (output_bdy_data_root,))


    pat_amp_pairs = zip( 
        case_setup["SST_perturbation"]["pert_pats"],
        case_setup["SST_perturbation"]["pert_amps"],
    )
    pert_configs = [
        dict(
            pat = pat,
            amp = amp,
        ) for pat, amp in pat_amp_pairs
    ]
    
    interpolate_climatology_flag = False
    input_args = []
    for pert_config in pert_configs:
    
        pat = pert_config["pat"]
        amp = pert_config["amp"]
        
        pert_label = f"PAT{pat:02d}_AMP{amp:.1f}"

        print(f"Doing pert_config : {pert_label:s}")     

        # This is for each perturbation pattern--amplitude combination
        output_bdy_data_subroot   = output_bdy_data_root / pert_label

        
        interpolate_perturbation_flag = False
        
        for i, ens_id in enumerate(range(ensemble_members)):
            
            ens_label = "%02d" % (ens_id,)
            
            input_bdy_data_dir  = input_bdy_data_root / ens_label 
            output_bdy_data_dir = output_bdy_data_subroot / ens_label

            # 
            print("Making subroot dir: ", output_bdy_data_subroot)
            output_bdy_data_subroot.mkdir(exist_ok=True, parents=True)


            # List bdy file
            bdy_files = []
            for filename in os.listdir(input_bdy_data_dir):
            
                if re.match(r"^met_em.*\.nc$", filename):
                    bdy_files.append(filename)

            bdy_files = sorted(bdy_files)

            if len(bdy_files) == 0:
                    
                print(f"[ERROR, ens={ens_label}] Cannot find any boundary files!")
                continue
           
            # Need to generate the climatology
            if interpolate_climatology_flag is False:
                print("The flag `interpolation_flag` is False. Now produce it...")

                # This is the reference file that contains the grid information
                interpolated_grid_file     = input_bdy_data_dir / bdy_files[0]
                
                # Only need 1 clim file, so I put it in the output_bdy_data_root
                interpolated_clim_SST_file = output_bdy_data_root / "interpolated_clim_sst.nc"

                # Step 4: Making interpolated climatology file
                cmb = clim_tools.climMagicBox(
                    raw_mon_SST_file           = case_setup["SST_perturbation"]["raw_mon_SST_file"],
                    clim_SST_file              = case_setup["SST_perturbation"]["clim_SST_file"],
                    interpolated_clim_SST_file = str(interpolated_clim_SST_file),
                    interpolated_grid_file     = str(interpolated_grid_file),
                )

                print("Generating clim files if not exist")
                cmb.genClim()
                cmb.genInterpolatedClim()

                interpolate_climatology_flag = True
                print("Interpolation of climatology is done.") 
                
            if interpolate_perturbation_flag is False:
                
                # Step 5: Making interpolated pattern file
                #         Each pattern need one interpolation file, so we put it in output_bdy_data_subroot.
                interpolated_pattern_file = output_bdy_data_subroot / "interpolated_pattern.nc"
                print("Generating projected pattern file: ", interpolated_pattern_file)
                if interpolated_pattern_file.exists():
                    print("Warning: pattern file %s already exists." % (interpolated_pattern_file,))
                else:
                    print("Generating interpolated pattern file: ", interpolated_pattern_file)
                    pattern_tools.genInterpolatedPattern(
                        pattern_file = case_setup["SST_perturbation"]["pattern_file"],
                        interpolated_grid_file = interpolated_grid_file,
                        interpolated_pattern_file = interpolated_pattern_file,
                        varname = args.pert_SST_varname,
                    )
               
                print("Interpolation of pattern %s is done." % (pert_label,)) 
                interpolate_perturbation_flag = True 


            print(f"Making details for {pert_label:s}")
            details = dict(
                label = pert_label,
                overwrite = args.overwrite,
                pat = pat,
                amp = amp,
                input_bdy_data_dir = input_bdy_data_dir,
                output_bdy_data_dir = output_bdy_data_dir,
                init_SST_file = bdy_files[0],
                interpolated_pattern_file = interpolated_pattern_file,
                BDY_INTERVAL_SECONDS = case_setup["bdy"]["BDY_INTERVAL_SECONDS"],
                start_time = start_time,
                end_time = end_time,
                cmb = cmb,
                method = args.method,
                bdy_SST_varname = args.bdy_SST_varname,
                pert_SST_varname = args.pert_SST_varname,
#                interpolated_grid_file = interpolated_grid_file,
            )

            input_args.append((details,))


    failed_cases = []
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
