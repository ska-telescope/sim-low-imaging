#!/bin/bash
#!

# wsclean -weight uniform -log-time -size 20480 20480 -scale 1.7578125asec -niter  20000 -mgain 0.8 -auto-threshold 3 -pol xx ../GLEAM_A-team_EoR0_no_errors.ms

cp ../clean_ms.py .
python ./clean_ms.py --ngroup 1 --nworkers 8 -- threads_per_worker 4 \
--weighting uniform --context wprojectwstack --nwslabs 51 \
--mode pipeline --niter 1000 --nmajor 5 --fractional_threshold 0.2 --threshold 0.01 \
--amplitude_loss 0.05 --deconvolve_facets 6 --deconvolve_overlap 16 --restore_facets 4 --oversampling 16 \
--msname /mnt/storage-ssd/tim/Code/sim-low-imaging/data/EoR0_20deg_192.MS \
--time_coal 0.0 --frequency_coal 0.0 --memory 128 --channels 131 135 \
--use_serial_invert True --use_serial_predict True --plot False --fov 2.9 --single False | tee clean_ms.log
