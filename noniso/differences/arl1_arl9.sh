#!/bin/bash
#!
python ../../analyse_images.py \
--image1 ../script1/GLEAM_A-team_EoR1_160_MHz_no_errors_cip_restored.fits \
--image2 ../script9/GLEAM_A-team_EoR1_160_MHz_no_errors_cip_restored.fits \
--outimage ./arl1-arl9.fits | tee arl1_arl9.log

