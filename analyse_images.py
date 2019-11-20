import argparse
import logging
import os
import pprint
import sys
import time

import matplotlib as mpl
mpl.use('Agg')

import matplotlib.pyplot as plt

from processing_components.image.operations import export_image_to_fits, import_image_from_fits
from processing_components.image.operations import copy_image, qa_image, show_image

pp = pprint.PrettyPrinter()
cwd = os.getcwd()

if __name__ == "__main__":
    log = logging.getLogger()
    log.setLevel(logging.INFO)
    log.addHandler(logging.StreamHandler(sys.stdout))
    log.addHandler(logging.StreamHandler(sys.stderr))
    mpl_logger = logging.getLogger("matplotlib")
    mpl_logger.setLevel(logging.WARNING)
    
    parser = argparse.ArgumentParser(description='SKA LOW imaging using ARL')
    parser.add_argument('--image1', type=str, default=None, help='First image')
    parser.add_argument('--image2', type=str, default=None, help='Second image')
    parser.add_argument('--outimage', type=str, default=None, help='Second image')
    parser.add_argument('--mode', type=str, default='pipeline', help='Imaging mode')
    
    args = parser.parse_args()
    
    pp.pprint(vars(args))
    
    im1 = import_image_from_fits(args.image1)
    im2 = import_image_from_fits(args.image2)
    print(qa_image(im1, context='Image 1'))
    print(qa_image(im2, context='Image 2'))

    outim = copy_image(im1)
    outim.data -= im2.data
    
    print(qa_image(outim, context='Difference image'))
    export_image_to_fits(outim, args.outimage)
    
    plt.clf()
    show_image(outim)
    plt.savefig(args.outimage.replace('.fits', '.jpg'))
    plt.show(block=False)
