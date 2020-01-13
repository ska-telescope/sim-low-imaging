#!/bin/bash
python ../clean_ms_noniso.py --ngroup 1 --nworkers 8 --memory 64 --weighting uniform --context wprojectwstack \
--nwslabs 9 --mode ical --niter 1000 --nmajor 5 --fractional_threshold 0.2 --threshold 0.01 \
--amplitude_loss 0.25 --deconvolve_facets 8 --deconvolve_overlap 16 --restore_facets 4 \
--msname /mnt/storage-ssd/tim/Code/sim-low-imaging/data/noniso/GLEAM_A-team_EoR1_160_MHz_iono.ms \
--time_coal 0.0 --frequency_coal 0.0 --channels 0 1 \
--use_serial_invert False --use_serial_predict False --plot False --fov 2.5 --single False | tee clean_ms.log
