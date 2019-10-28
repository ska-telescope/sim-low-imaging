#!/bin/bash
#!

cd run1
pip uninstall pyfftw
sh ../clean_ms.sh
cd ../run2
pip install pyfftw
sh ../clean_ms.sh
cd ..
