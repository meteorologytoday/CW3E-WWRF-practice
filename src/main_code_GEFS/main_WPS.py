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
import shutil


script_dir = Path(os.path.dirname(__file__))

def create_soft_links(source_dir, target_dir, skip_if_exists=False):
    """Creates soft links for all files in source_dir within target_dir."""
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    for filename in os.listdir(source_dir):
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
    
    WPS_DIR =  Path(details["WPS_DIR"])
    WPS_TMP_DIR =  Path(details["WPS_TMP_DIR"])
    wps_output_file = WPS_TMP_DIR / "namelist.wps"
    source_boundary_data_dirs = details["source_boundary_data_dirs"] 
    final_boundary_data_dir = Path(details["final_boundary_data_dir"]) 
    setup_file = Path(details["setup_file"])

    results = dict(details = details, status="UNKNOWN") 

    try: 
            
        WPS_TMP_DIR.mkdir(parents=True, exist_ok=True)
        final_boundary_data_dir.mkdir(parents=True, exist_ok=True)

        print("Making %s" % (wps_output_file,))       
        pleaseRun("python3 {src_dir:s}/generate_namelist.py --program WPS --setup {setup_file:s} --output {wpsoutput:s}".format(
            src_dir = str( script_dir / ".." ),
            wpsoutput = str(wps_output_file),
            setup_file = str(setup_file),
        ))
 
        print("Making soft links...")       
        create_soft_links(WPS_DIR, WPS_TMP_DIR, skip_if_exists=True) 
        pleaseRun(f"ln -s %s/ungrib/Variable_Tables/Vtable.GFSENS %s/Vtable" % (WPS_TMP_DIR, WPS_TMP_DIR,))
       
        # Run WPS
        geogrid_file = WPS_TMP_DIR / "geo_em.d01.nc"
        if geogrid_file.exists():
            print("The geogrid file `%s` already exists. Remove it." % (geogrid_file,))
            geogrid_file.unlink()

        pleaseRun(str(WPS_TMP_DIR / "geogrid.exe"), cwd=str(WPS_TMP_DIR))

        pleaseRun("%s %s" % (
            str(WPS_TMP_DIR / "link_grib.csh"),
            " ".join(["%s/" % (source_boundary_data_dir,) for source_boundary_data_dir in source_boundary_data_dirs ]),
        ), cwd=str(WPS_TMP_DIR))
        pleaseRun(str(WPS_TMP_DIR / "ungrib.exe"), cwd=str(WPS_TMP_DIR))
        pleaseRun(str(WPS_TMP_DIR / "metgrid.exe"), cwd=str(WPS_TMP_DIR))
        
        # Move met_dm files to 
        boundary_files = []
        for filename in os.listdir(WPS_TMP_DIR):

            if re.match(r"^met_em.*\.nc$", filename):
                boundary_files.append(filename)

        if len(boundary_files) == 0:
            raise Exception("Cannot find any boundary files!")
        else:
            print("Copying bdy files to directory %s" % (final_boundary_data_dir,))
            for filename in boundary_files:
                    from_filename = WPS_TMP_DIR / filename
                    to_filename = final_boundary_data_dir / filename
                    
                    print("Copy file: %s" % (filename,))
                    try:
                        shutil.move(from_filename, to_filename)
                        print(f"File moved successfully from {from_filename} to {to_filename}")
                    except FileNotFoundError:
                        print(f"Error: Source file {from_filename} not found.")
                        raise e
                    except Exception as e:
                        print(f"An error occurred: {e}")
                        raise e

        results['status'] = 'OK'

    except Exception as e:

        results['status'] = 'ERROR'
        traceback.print_exc()

    return results



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
    parser.add_argument('--specify-ens-id', type=int, help='Used to do only one known case.', default=None)

    args = parser.parse_args()

    pprint.pprint(args)

    case_setup = toml.load(args.setup)
    start_time = pd.Timestamp(case_setup["start_time"])
    end_time = pd.Timestamp(case_setup["end_time"])

    ensemble_members = case_setup["ensemble"]["ensemble_members"]
 
    WPS_DIR =  Path(case_setup["WPS_DIR"])
    WPS_TMP_ROOT =  Path(case_setup["WPS_TMP_ROOT"])
   
    caserun_root = Path(case_setup["caserun"]["caserun_root"])
    bdy_root =  caserun_root / "bdy"


    if args.specify_ens_id is not None:
        
        ens_ids = [args.specify_ens_id, ]

    else:
        ens_ids = list(range(ensemble_members))
       

    print("ens_ids: ", ens_ids) 
        

    #if WPS_TMP_ROOT.exists():
    #    raise Exception(f"WPS_TMP_ROOT `{WPS_TMP_ROOT}` exists.")

    input_args = []
    for i, ens_id in enumerate(ens_ids):
            
        member_label = "c00" if ens_id == 0 else f"p{ens_id:02d}"

        final_boundary_data_dir = bdy_root / f"{ens_id:02d}"
        input_boundary_dir = Path(case_setup["caserun"]["input_boundary_dir"])
        source_boundary_data_dirs = [
            input_boundary_dir / member_label / "atmos",
        ] 

        details = dict(
            WPS_DIR = WPS_DIR,
            WPS_TMP_DIR = WPS_TMP_ROOT / f"{ens_id:02d}",
            source_boundary_data_dirs = source_boundary_data_dirs,
            final_boundary_data_dir = final_boundary_data_dir,
            label = member_label,
            setup_file = args.setup,
        )


        input_args.append((details,))




    failed_labels = []
    with Pool(processes=args.nproc) as pool:

        results = pool.starmap(work, input_args)

        for i, result in enumerate(results):
            if result['status'] != 'OK':
                print('!!! Failed to generate output : %s.' % (result["details"]['label'],))
                failed_labels.append(result["details"]['label'],)


        print("Tasks finished.")

        print("Failed files: ")
        for i, failed_label in enumerate(failed_labels):
            print("%d : %s" % (i+1, failed_label,))
        


        
