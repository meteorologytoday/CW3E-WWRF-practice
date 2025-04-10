import pandas as pd
import xarray as xr
from pathlib import Path

cropped_year = [1980, 2024]
dhr=6

input_file = "/expanse/lustre/scratch/t2hsu/temp_project/data/AR_catalogue/globalARcatalog_ERA5_1940-2024_v4.0.nc"
output_dir = Path("/expanse/lustre/scratch/t2hsu/temp_project/data/AR_catalogue/subset")

def genTimeSeriesOfMonth(
    year, month, dhr,
):

    beg_dt = pd.Timestamp(year=year, month=month, day=1)
    end_dt = beg_dt + pd.DateOffset(months=1)

    delta_time = end_dt - beg_dt
    N = int(delta_time / pd.Timedelta(hours=dhr))

    return [beg_dt + pd.Timedelta(hours=i * dhr) for i in range(N)]



print("Open and slice file: ", input_file)
ds = xr.open_dataset(input_file)
data = []

for year in range(cropped_year[0], cropped_year[1]+1):
    
    print("Year: ", year)

    for month in range(1, 13): 

        selected_time = genTimeSeriesOfMonth(year, month, dhr)
    
        output_file = output_dir / "year_{y:04d}-{m:02}.nc".format(
            y = year,
            m = month,
        )

        if output_file.exists():

            print("File %s already exists. Skip." % (str(output_file),))
        else:
            print("File %s is not there, now slice data..." % (str(output_file),))
            _ds = ds.sel(time=selected_time)

            print("Writing file: ", output_file)
            _ds.to_netcdf(output_file, unlimited_dims="time")

        






