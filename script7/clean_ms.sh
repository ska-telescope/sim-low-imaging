#!/bin/bash
#!

# wsclean -weight uniform -log-time -size 20480 20480 -scale 1.7578125asec -niter  20000 -mgain 0.8 -auto-threshold 3 -pol xx ../GLEAM_A-team_EoR0_no_errors.ms

python ../clean_ms.py --ngroup 1 --nworkers 16 --weighting uniform --context wstack --nwplanes 128 \
--niter 10000 --nmajor 1 --fractional_threshold 0.2 --threshold 0.01 \
--msname /mnt/storage-ssd/tim/Code/sim-low-imaging/data/EoR0_20deg_24.MS \
--time_coal 0.0 --frequency_coal 0.0 --memory 64 --channels 131 139 \
--use_serial_invert True --use_serial_predict True --plot False --npixel 4096 --single False | tee clean_ms.log
