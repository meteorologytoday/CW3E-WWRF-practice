import xarray as xr
import os
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from pathlib import Path

def interpFromRegularGrid(lat, lon, data, new_lat, new_lon):
    
    Nt = data.shape[0]
    N = new_lat.size
    new_shape = new_lat.shape
 
    new_pts = np.zeros((N, 2), dtype=float)

    new_pts[:, 0] = new_lat.flatten()
    new_pts[:, 1] = new_lon.flatten()
    new_data = np.zeros( (Nt, *new_lat.shape), dtype=float)
   

    repeated_lon = np.concatenate( (lon - 360, lon, lon + 360) )
 
    for t in range(Nt):
        
        interp = RegularGridInterpolator(
            (lat, repeated_lon),
            np.tile(
                data[t, :, :],
                (1, 3),
            ),
        )

        _tmp = interp(new_pts).reshape(new_shape)
        new_data[t, :, :] = _tmp
    

    return new_data

def genInterpolatedEOF(
        EOF_file,
        interpolated_grid_file,
        interpolated_EOF_file,
    ):
        
    print("Input EOF File: ", EOF_file)
    print("Interpolated Grid File: ", interpolated_grid_file)

    print("Interpolating now... ")
    ds = xr.open_dataset(EOF_file)
    ds_gd = xr.open_dataset(interpolated_grid_file)

    lat = ds.coords["lat"].to_numpy()
    lon = ds.coords["lon"].to_numpy()
    data = ds["EOF"].to_numpy()

    # Only need one time
    new_lat = ds_gd["XLAT_M"].to_numpy()[0, :, :]
    new_lon = ds_gd["XLONG_M"].to_numpy()[0, :, :]
    
    new_data = interpFromRegularGrid(lat, lon, data, new_lat, new_lon)
   
    new_ds = xr.Dataset(
        data_vars=dict(
            sst = (["mode", "south_north", "west_east"], new_data),
        ),
        coords = dict(
            mode = (["mode",], ds.coords["mode"].to_numpy()),
            XLAT_M  = (["south_north", "west_east", ], new_lat),
            XLONG_M = (["south_north", "west_east", ], new_lon),
        )
    ) 
    
    print("Output file:", interpolated_EOF_file)
    new_ds.to_netcdf(interpolated_EOF_file)


if __name__ == "__main__":
   
    EOF_file = "./data/EOFs_GHRSST,MUR_JPL,OSTIA_UKMO,DMIOI_DMI,GAMSSA_ABOM,K10SST_NAVO,GPBN_OSPO_decentralize-F_WWRF_sst_Y2020-2023_P-6-11.nc"
    interpolated_EOF_file = "./gendata/interpolated_EOF.nc"

    interpolated_grid_file = "/home/t2hsu/temp_project/WRF_RUNS/test_bdy/met_em.d01.2022-01-07_00:00:00.nc"

    print("Creating dir: ", os.path.dirname(interpolated_EOF_file))
    Path(os.path.dirname(interpolated_EOF_file)).mkdir(exist_ok=True, parents=True)
    
    genInterpolatedEOF(
        EOF_file = EOF_file,
        interpolated_grid_file = interpolated_grid_file,
        interpolated_EOF_file = interpolated_EOF_file,
    )
 
