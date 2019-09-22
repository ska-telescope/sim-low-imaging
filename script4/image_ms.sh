#!/bin/bash
#!

# wsclean -weight uniform -log-time -size 20480 20480 -scale 1.7578125asec -niter  20000 -mgain 0.8 -auto-threshold 3 -pol xx ../GLEAM_A-team_EoR0_no_errors.ms

python ../image_ms.py --ngroup 2 --nworkers 8 --weighting uniform --context wstack --nwplanes 128 \
--msname /mnt/storage-ssd/tim/Code/sim-low-imaging/data/EoR0_20deg_96.MS \
--channels 131 146 --use_serial_invert True --plot False --npixel 8192 --single False --memory 128 | tee image_ms.log
