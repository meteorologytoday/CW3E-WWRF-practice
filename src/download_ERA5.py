from multiprocessing import Pool
import multiprocessing
import cdsapi
from pathlib import Path
import argparse
import pandas as pd
import traceback
import numpy as np
import xarray as xr
import os

parser = argparse.ArgumentParser(
                    prog = 'plot_skill',
                    description = 'Plot prediction skill of GFS on AR.',
)

parser.add_argument('--date-rng', type=str, nargs=2, help='Target date to download. Left inclusive only.', required=True)
parser.add_argument('--date-inclusive', type=str, help='Inclusiveness of `--date-rng`.', default="left")
parser.add_argument('--download-dir', type=str, help='Output directory', required=True)
parser.add_argument('--nproc', type=int, help='Output directory', default=4)

args = parser.parse_args()
print(args)


beg_time = pd.Timestamp(args.date_rng[0])
end_time = pd.Timestamp(args.date_rng[1])
nproc = args.nproc


c = cdsapi.Client()

download_targets = ["pl", "sl"]


dhr = 3 
if 24 % dhr != 0:
    raise Exception("Not cool. 24 / dhr (dhr = %d) is not an integer." % (dhr, ) )

download_time = [ "%02d:00" % (i * dhr, ) for i in range(int(24 / dhr))]


def ifSkip(dt):

    skip = False
    if not ( dt.month in [10, 11, 12, 1, 2, 3, 4] ):
        skip = True

    return skip



varnames = dict(
    
    pl = [
        'geopotential',
        'relative_humidity',
        'temperature',
        'u_component_of_wind',
        'v_component_of_wind',
    ],
    
    sl  = [
        '10m_u_component_of_wind',
        '10m_v_component_of_wind',
        '2m_dewpoint_temperature',
        '2m_temperature',
        'land_sea_mask',
        'mean_sea_level_pressure',
        'sea_ice_cover',
        'sea_surface_temperature',
        'skin_temperature',
        'snow_density',
        'snow_depth',
        'soil_temperature_level_1',
        'soil_temperature_level_2',
        'soil_temperature_level_3',
        'soil_temperature_level_4',
        'surface_pressure',
        'volumetric_soil_water_layer_1',
        'volumetric_soil_water_layer_2',
        'volumetric_soil_water_layer_3',
        'volumetric_soil_water_layer_4',
    ],

)


area = [
    65, -180, 0, 180,
]

pressure_levels = [
    '10'  ,
    '50'  ,
    '100' ,
    '250' , 
    '500' ,
    '850' ,
    '1000',
]


download_tmp_dir = os.path.join(args.download_dir, "tmp")

def doJob(details, detect_phase=False):
        
    target_date = details["target_date"]
    
    # phase \in ['detect', 'work']
    result = dict(
        dt = target_date,
        status="UNKNOWN", 
        need_work=False, 
        detect_phase=detect_phase,
    )

    try:



        y = target_date.year
        m = target_date.month
        d = target_date.day

        time_str = target_date.strftime("%Y-%m-%d")
        
        file_prefix = "WRF_ERA5"
 
        # Detecting
        if not os.path.isdir(args.download_dir):
            print("Create dir: %s" % (args.download_dir,))
            Path(args.download_dir).mkdir(parents=True, exist_ok=True)
                    
        output_filenames = dict(
            pl = os.path.join(args.download_dir, "%s-pl-%s.grib" % (file_prefix, time_str, )),
            sl = os.path.join(args.download_dir, "%s-sl-%s.grib" % (file_prefix, time_str, )),
        )

        need_work = False
        for _, output_filename in output_filenames.items():
            need_work = need_work or ( not os.path.isfile(output_filename) )
        
        
        # First round is just to decide which files
        # to be processed to enhance parallel job 
        # distribution. I use variable `phase` to label
        # this stage.
        if detect_phase is True:

            result['need_work'] = need_work
            result['status'] = 'OK'
            
            return result

        files_to_remove = []

        if not need_work:
            
            print("[%s] Data already exists. Skip." % (time_str, ))
            
        else:
       
            #print(output_filenames) 
            for lev_type, output_filename in output_filenames.items():
                
                
                #print(lev_type)
                #print(output_filename)
                
                tmp_filename_downloading = os.path.join(
                    download_tmp_dir,
                    "%s-%s-%s.downloading.tmp" % (
                        file_prefix,
                        lev_type,
                        time_str,
                    )
                )

                files_to_remove.append(tmp_filename_downloading)
                
                print("[%s] Now producing file: %s" % (time_str, output_filename,))

                if lev_type == "pl":
                    
                    era5_dataset_name = 'reanalysis-era5-pressure-levels'
                    params = {
                                'product_type': 'reanalysis',
                                'format': 'grib',
                                'area': area,
                                'time': download_time,
                                'day': ["%02d" % d, ],
                                'month': ["%02d" % m,],
                                'year': ["%04d" % y,],
                                'pressure_level': pressure_levels,
                                'variable': varnames[lev_type],
                    }

                elif lev_type == "sl":
                    
                    era5_dataset_name = 'reanalysis-era5-single-levels'
                    params = {
                                'product_type': 'reanalysis',
                                'format': 'grib',
                                'area': area,
                                'time': download_time,
                                'day': ["%02d" % d, ],
                                'month': ["%02d" % m,],
                                'year': ["%04d" % y,],
                                'pressure_level': pressure_levels,
                                'variable': varnames[lev_type],
                    }

                else:
                    
                    raise Exception("Unknown lev_type = %s" % (lev_type,))

                print("Downloading file: %s" % ( tmp_filename_downloading, ))
                c.retrieve(era5_dataset_name, params, tmp_filename_downloading)
                os.rename(tmp_filename_downloading, output_filename)


        for remove_file in files_to_remove:
            if os.path.isfile(remove_file):
                print("[%s] Remove file: `%s` " % (time_str, remove_file))
                os.remove(remove_file)

        result['status'] = 'OK'

    except Exception as e:

        result['status'] = 'ERROR'
        traceback.print_stack()
        traceback.print_exc()
        print(e)

    print("[%s] Done. " % (time_str,))

    return result


failed_dates = []
dts = pd.date_range(beg_time.strftime("%Y-%m-%d"), end_time.strftime("%Y-%m-%d"), freq="D", inclusive=args.date_inclusive)

input_args = []

for dt in dts:

    time_str = dt.strftime("%Y-%m-%d")

    if ifSkip(dt):
        print("Skip the date: %s" % (time_str,))
        continue


    details = dict(
        target_date = dt,
    )

    result = doJob(details, detect_phase=True)
    
    if result['status'] != 'OK':
        print("[detect] Failed to detect date %s " % (str(dt),))
    
    if result['need_work'] is False:
        print("[detect] Files all exist for date %s" % (str(dt),))
    else:
        input_args.append((details,))
    
print("Create dir: %s" % (download_tmp_dir,))
Path(download_tmp_dir).mkdir(parents=True, exist_ok=True)

with Pool(processes=args.nproc) as pool:

    results = pool.starmap(doJob, input_args)

    for i, result in enumerate(results):
        if result['status'] != 'OK':
            print('!!! Failed to generate output of date %s.' % (result['dt'].strftime("%Y-%m-%d_%H"), ))

            failed_dates.append(result['dt'])


print("Tasks finished.")

print("Failed dates: ")
for i, failed_date in enumerate(failed_dates):
    print("%d : %s" % (i+1, failed_date.strftime("%Y-%m"),))


print("Done.")
