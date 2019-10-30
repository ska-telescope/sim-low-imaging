#!/bin/bash
#!

# wsclean -weight uniform -log-time -size 20480 20480 -scale 1.7578125asec -niter  20000 -mgain 0.8 -auto-threshold 3 -pol xx ../GLEAM_A-team_EoR0_no_errors.ms

pip freeze | tee pip.txt

python ../clean_ms.py --msname ../data/EoR0_20deg_24.MS --channels 131 135 --ngroup 1 \
--weighting uniform --context wprojectwstack --nwslabs 15 --use_serial_invert False \
--use_serial_predict False --plot False --fov 0.1 --single True --serial False --time_coal 0.0 \
--frequency_coal 0.0 --nmajor 5 --niter 1000 --fractional_threshold 0.2 --threshold 0.1 \
--mode pipeline | tee small_clean_ms.log
