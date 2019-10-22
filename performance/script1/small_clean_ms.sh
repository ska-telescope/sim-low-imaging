#!/bin/bash
#!

# wsclean -weight uniform -log-time -size 20480 20480 -scale 1.7578125asec -niter  20000 -mgain 0.8 -auto-threshold 3 -pol xx ../GLEAM_A-team_EoR0_no_errors.ms

cp ../../clean_ms.py .
python ./clean_ms.py --msname ../data/EoR0_20deg_24.MS --channels 131 132 --ngroup 1 --weighting natural \
--context 2d --nwplanes 128 --use_serial_invert True --use_serial_predict True --plot False --fov 0.75 \
--single True --serial True --time_coal 0.0 --frequency_coal 0.0 --nmajor 1 --niter 1000 --fractional_threshold 0.2 \
--threshold 0.1 --mode invert | tee clean_ms.log