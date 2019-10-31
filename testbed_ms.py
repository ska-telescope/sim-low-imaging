"""

python testbed_ms.py --msname data/EoR0_20deg_24.MS --weighting uniform --context 2d --fov 0.2
"""

import argparse
import logging
import pprint
import sys
import time

import matplotlib as mpl

#mpl.use('Agg')

import matplotlib.pyplot as plt
import astropy.units as u
from astropy.coordinates import SkyCoord, EarthLocation

from data_models.polarisation import ReceptorFrame
from processing_components.image.operations import qa_image, export_image_to_fits, show_image
from processing_components.imaging.base import advise_wide_field, create_image_from_visibility
from processing_components.visibility.base import create_blockvisibility_from_ms
from processing_components.visibility.coalesce import convert_blockvisibility_to_visibility
from processing_components.imaging.base import invert_2d
from processing_components.imaging.weighting import weight_visibility

pp = pprint.PrettyPrinter()

log = logging.getLogger()
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler(sys.stdout))
mpl_logger = logging.getLogger("matplotlib")
mpl_logger.setLevel(logging.WARNING)

if __name__ == "__main__":
    
    start_epoch = time.asctime()
    print("\nSKA LOW imaging using ARL\nStarted at %s\n" % start_epoch)
    
    ########################################################################################################################
    
    parser = argparse.ArgumentParser(description='SKA LOW imaging using ARL')
    parser.add_argument('--context', type=str, default='2d', help='Imaging context')
    parser.add_argument('--msname', type=str, default='../data/EoR0_20deg_24.MS',
                        help='MS to process')
    parser.add_argument('--local_directory', type=str, default='dask-workspace',
                        help='Local directory for Dask files')
    
    parser.add_argument('--npixel', type=int, default=None, help='Number of pixels')
    parser.add_argument('--fov', type=float, default=1.0, help='Field of view in primary beams')
    parser.add_argument('--cellsize', type=float, default=None, help='Cellsize in radians')
    
    parser.add_argument('--wstep', type=float, default=None, help='FStep in w')
    parser.add_argument('--nwplanes', type=int, default=None, help='Number of wplanes')
    parser.add_argument('--nwslabs', type=int, default=None, help='Number of w slabs')
    parser.add_argument('--amplitude_loss', type=float, default=0.02, help='Amplitude loss due to w sampling')
    parser.add_argument('--facets', type=int, default=1, help='Number of facets in imaging')
    parser.add_argument('--oversampling', type=int, default=16, help='Oversampling in w projection kernel')
    parser.add_argument('--weighting', type=str, default='natural', help='Type of weighting')
    
    args = parser.parse_args()
    pp.pprint(vars(args))
    
    target_ms = args.msname
    print("Target MS is %s" % target_ms)
    
    weighting = args.weighting
    nwplanes = args.nwplanes
    nwslabs = args.nwslabs
    npixel = args.npixel
    cellsize = args.cellsize
    fov = args.fov
    facets = args.facets
    wstep = args.wstep
    context = args.context
    dela = args.amplitude_loss
    
    ####################################################################################################################
    
    # Read an MS and convert to Visibility format. This might need to be changed for another MS
    print("\nSetup of visibility ingest")
    msname = args.msname
    bvis = create_blockvisibility_from_ms(msname, start_chan=131, end_chan=131)[0]
    bvis.configuration.location = EarthLocation(lon="116.76444824", lat="-26.824722084", height=300.0)
    bvis.configuration.frame = ""
    bvis.configuration.receptor_frame = ReceptorFrame("linear")
    bvis.configuration.data['diameter'][...] = 35.0
    vis = convert_blockvisibility_to_visibility(bvis)
    ####################################################################################################################
    
    print("\nSetup of images")
    phasecentre = SkyCoord(ra=0.0 * u.deg, dec=-27.0 * u.deg)
    
    advice = advise_wide_field(vis, guard_band_image=fov, delA=dela, verbose=True)
    print(advice)
    
    if npixel is None:
        npixel = advice['npixels_min']
    
    if wstep is None:
        wstep = 1.1 * advice['wstep']
    
    if nwplanes is None:
        nwplanes = advice['wprojection_planes']
    
    if cellsize is None:
        cellsize = advice['cellsize']
    
    print('Image shape is %d by %d pixels' % (npixel, npixel))
    
    ####################################################################################################################
    
    print("\nSetup of wide field imaging")
    vis_slices = 1
    actual_context = '2d'
    support = 1
    if context == 'wprojection':
        # w projection
        vis_slices = 1
        support = advice[0]['nwpixels']
        actual_context = '2d'
        print("Will do w projection, %d planes, support %d, step %.1f" %
              (nwplanes, support, wstep))
    
    elif context == 'wstack':
        # w stacking
        print("Will do w stack, %d planes, step %.1f" % (nwplanes, wstep))
        actual_context = 'wstack'
    
    elif context == 'wprojectwstack':
        # Hybrid w projection/wstack
        nwplanes = int(1.5 * nwplanes) // nwslabs
        support = int(1.5 * advice[0]['nwpixels'] / nwslabs)
        support = max(15, int(3.0 * advice[0]['nwpixels'] / nwslabs))
        support -= support % 2
        vis_slices = nwslabs
        actual_context = 'wstack'
        print("Will do hybrid w stack/w projection, %d w slabs, %d w planes, support %d, w step %.1f" %
              (nwslabs, nwplanes, support, wstep))
    else:
        print("Will do 2d processing")
        # Simple 2D
        actual_context = '2d'
        vis_slices = 1
        wstep = 1e15
        nwplanes = 1
    
    model = create_image_from_visibility(vis, npixel=npixel, cellsize=cellsize)
    
    # Perform weighting. This is a collective computation, requiring all visibilities :(
    print("\nSetup of weighting")
    if weighting == 'uniform':
        print("Will apply uniform weighting")
        vis_list = weight_visibility(vis, model)
    
    dirty, sumwt = invert_2d(vis, model, context=actual_context, vis_slices=nwplanes)
    print(qa_image(dirty))
    
    show_image(dirty)
    plot_name = target_ms.split('/')[-1].replace('.MS', '_dirty.jpg')
    plt.savefig(plot_name)
    plt.show(block=False)

    dirty_name = target_ms.split('/')[-1].replace('.MS', '_dirty.fits')
    export_image_to_fits(dirty, dirty_name)

    
    
