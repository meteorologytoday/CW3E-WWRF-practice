# Work flow

## Part 1
1. Setup grid information
2. Setup datetime information
3. Genearte namelist file for WPS
4. Generate forcing files
  - Download boundary data
  - Use WPS to generate `met_em` files.
  - Generate perturbation files.
  - Modify SST in `met_em` files for each perturbation.

## Part 2
1. Genearte case for each run.
  - Copy a scaffold case
  - Generate namelist files (WRF & WPS)
2. Submit job.

