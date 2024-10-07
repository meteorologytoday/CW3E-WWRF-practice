import xarray as xr
import pandas as pd
import numpy as np
import argparse
import tool_fig_config
import wrf_load_helper 
import datetime
import os
from pathlib import Path

#    exp_beg_time = pd.Timestamp(args.exp_beg_time)
#    wrfout_data_interval = pd.Timedelta(seconds=args.wrfout_data_interval)
#    time_beg = exp_beg_time + pd.Timedelta(hours=args.time_rng[0])
#    time_end = exp_beg_time + pd.Timedelta(hours=args.time_rng[1])
#prefix = "met_em.d01."

class Perturbation:
    
    def __init__(self, pert_file):
        
        self.pert_file = pert_file

    def getPerturbation(dt, lat, lon):
        
        
        
        pass






    


def perturbation(
    
):
    # Load perturbation file
    
    
    



def addSSTPerturbation(
    pert_file,
    input_dir,
    output_dir,
    beg_dt,
    end_dt,
    data_interval,
    frames_per_file = 1,
    input_prefix = "met_em.d01.",
    input_suffix = ".nc",
    output_prefix = "met_em.d01.",
    output_suffix = ".nc",
):

    if ( end_dt - beg_dt ) / data_interval % 1 != 0:
        raise Exception("The time selected is not a multiple of `data_interval`.")


    wrf_int


    wsm = wrf_load_helper.WRFSimMetadata(
        start_datetime  = beg_dt,
        data_interval   = data_interval,
        frames_per_file = 1,
    )
    

    

    ds = wrf_load_helper.loadWRFDataFromDir(
        wsm, 
        input_dir,
        beg_time = beg_dt,
        end_time = end_dt,
        prefix=input_prefix,
        suffix=input_suffix,
        avg=None,
        verbose=False,
        inclusive="both",
    )

    ds_SST_pert = xr.open_dataset(pert_file)

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    
    new_SST = ds["SST"].to_numpy()
    new_SST += ds_SST_pert["SST"].to_numpy()
    
    ds["SST"][:, :, :] = new_SST
   
      
    
    return ds
    

if __name__ == "__main__":
    
    input_dir = "/home/t2hsu/temp_project/WRF_RUNS/test_gcc"
    output_dir = "/home/t2hsu/temp_project/WRF_RUNS/altered_SST"
    beg_dt = pd.Timestamp("2022-01-07T06:00:00")
    end_dt = pd.Timestamp("2022-01-08T00:00:00")
    data_interval = pd.Timedelta(hours=3)
    
    ds = addSSTPerturbation(
        input_dir,
        output_dir,
        beg_dt = beg_dt,
        end_dt = end_dt,
        data_interval = data_interval,
    )
    

    print(ds.time)

