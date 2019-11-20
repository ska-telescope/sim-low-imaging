#!/bin/bash
#!
python ../../analyse_images.py \
--image1 ../script8/GLEAM_A-team_EoR1_160_MHz_no_errors_cip_restored.fits \
--image2 ../script7/GLEAM_A-team_EoR1_160_MHz_no_errors_cip_restored.fits \
--outimage ./ng8-ng7.fits | tee ng8-ng7.log

