#!/bin/bash
#!
python ../../analyse_images.py \
--image1 ../script9/GLEAM_A-team_EoR1_160_MHz_no_errors_cip_restored.fits \
--image2 ../script8/GLEAM_A-team_EoR1_160_MHz_no_errors_cip_restored.fits \
--outimage ./arl-ng8.fits | tee arl_ng8.log

