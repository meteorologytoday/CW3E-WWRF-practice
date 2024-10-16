import xarray as xr
import numpy as np

prototype_file = "/home/t2hsu/models/WRF_gcc/WPS-4.5/met_em.d01.2022-01-07_00:00:00.nc"
output_file = "pert_SST.d01.2022-01-07_00:00:00.nc"

dSST = 1
clat = 40.0
clon = 230.0

sig_lat = 5.0
sig_lon = 10.0


ds = xr.open_dataset(prototype_file)


lat = ds["XLAT_M"].to_numpy()
lon = ds["XLONG_M"].to_numpy() % 360.0


da_pert_SST = ds["SST"].copy().rename("pert_SST")


pert_SST = dSST * np.exp( - ( (lat - clat)**2 / (2 * sig_lat**2) + (lon - clon)**2 / (2 * sig_lon**2) )  )


da_pert_SST[:] = pert_SST

print("Output file: ", output_file)
da_pert_SST.to_netcdf(output_file)




