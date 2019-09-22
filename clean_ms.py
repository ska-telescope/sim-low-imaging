import argparse
import logging
import pprint
import sys
import time

import astropy.units as u
import matplotlib.pyplot as plt
import numpy
from astropy.coordinates import SkyCoord, EarthLocation

from data_models.polarisation import ReceptorFrame
from processing_components.image.operations import qa_image, export_image_to_fits, show_image
from processing_components.imaging.base import advise_wide_field, create_image_from_visibility
from processing_components.visibility.base import create_blockvisibility_from_ms, vis_summary
from processing_components.visibility.coalesce import convert_blockvisibility_to_visibility, coalesce_visibility
from processing_components.griddata.kernels import create_awterm_convolutionfunction
from processing_components.griddata.convolution_functions import convert_convolutionfunction_to_image
from workflows.arlexecute.imaging.imaging_arlexecute import weight_list_arlexecute_workflow, \
    invert_list_arlexecute_workflow, sum_invert_results_arlexecute
from workflows.arlexecute.pipelines.pipeline_arlexecute import continuum_imaging_list_arlexecute_workflow
from wrappers.arlexecute.execution_support.arlexecute import arlexecute
from wrappers.arlexecute.execution_support.dask_init import get_dask_Client

pp = pprint.PrettyPrinter()

log = logging.getLogger()
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler(sys.stdout))
mpl_logger = logging.getLogger("matplotlib")
mpl_logger.setLevel(logging.WARNING)

import matplotlib as mpl
mpl.use('Agg')

if __name__ == "__main__":
    
    # 116G	/mnt/storage-ssd/tim/data/GLEAM_A-team_EoR0_0.270_dB.ms
    # 116G	/mnt/storage-ssd/tim/data/GLEAM_A-team_EoR0_no_errors.ms
    msnames = ['/mnt/storage-ssd/tim/data/GLEAM_A-team_EoR0_0.270_dB.ms',
               '/mnt/storage-ssd/tim/data/GLEAM_A-team_EoR0_no_errors.ms']
    
    msnames = ['/alaska/tim/Code/sim-low-imaging/data/GLEAM_A-team_EoR0_0.270_dB.ms',
               '/alaska/tim/Code/sim-low-imaging/data/GLEAM_A-team_EoR0_no_errors.ms']
    
    # 7.8G	/mnt/storage-ssd/tim/data/EoR0_20deg_24.MS
    # 31G	/mnt/storage-ssd/tim/data/EoR0_20deg_96.MS
    # 62G	/mnt/storage-ssd/tim/data/EoR0_20deg_192.MS
    # 116G	/mnt/storage-ssd/tim/data/EoR0_20deg_360.MS
    # 155G	/mnt/storage-ssd/tim/data/EoR0_20deg_480.MS
    # 194G	/mnt/storage-ssd/tim/data/EoR0_20deg_600.MS
    # 232G	/mnt/storage-ssd/tim/data/EoR0_20deg_720.MS
    msname_times = [
        '/alaska/tim/Code/sim-low-imaging/data/EoR0_20deg_24.MS',
        '/alaska/tim/Code/sim-low-imaging/data/EoR0_20deg_96.MS',
        '/alaska/tim/Code/sim-low-imaging/data/EoR0_20deg_192.MS',
        '/alaska/tim/Code/sim-low-imaging/data/EoR0_20deg_480.MS',
        '/alaska/tim/Code/sim-low-imaging/data/EoR0_20deg_600.MS',
        '/alaska/tim/Code/sim-low-imaging/data/EoR0_20deg_360.MS',
        '/alaska/tim/Code/sim-low-imaging/data/EoR0_20deg_720.MS']
    
    print("\nSKA LOW imaging using ARL\n")

    ########################################################################################################################

    parser = argparse.ArgumentParser(description='Low imaging test')
    parser.add_argument('--context', type=str, default='2d', help='Imaging context')
    parser.add_argument('--mode', type=str, default='pipeline', help='Imaging mode')
    parser.add_argument('--msname', type=str, default='../data/EoR0_20deg_24.MS',
                        help='MS to process')
    parser.add_argument('--local_directory', type=str, default='dask-workspace',
                        help='Local directory for Dask files')
    parser.add_argument('--ngroup', type=int, default=4,
                        help='Number of channels in each BlockVisibility')
    
    parser.add_argument('--channels', type=int, nargs=2, default=[0, 160], help='Channels to process')
    parser.add_argument('--npixel', type=int, default=None, help='Number of pixels')
    parser.add_argument('--fov', type=float, default=1.0, help='Field of view in primary beams' )
    parser.add_argument('--cellsize', type=float, default=None, help='Cellsize in radians' )
    parser.add_argument('--single', type=str, default='False', help='Use a single channel')
    parser.add_argument('--wstep', type=float, default=None, help='FStep in w' )
    parser.add_argument('--nwplanes', type=int, default=None, help='Number of wplanes')
    parser.add_argument('--nwslabs', type=int, default=None, help='Number of w slabs')
    parser.add_argument('--amplitude_loss', type=float, default=0.02, help='Amplitude loss due to w sampling')
    parser.add_argument('--nmajor', type=int, default=1, help='Number of major cycles')
    parser.add_argument('--niter', type=int, default=1, help='Number of iterations per major cycle')
    parser.add_argument('--fractional_threshold', type=float, default=0.2, help='Fractional threshold to terminate major cycle')
    parser.add_argument('--threshold', type=float, default=0.01, help='Absolute threshold to terminate')
    parser.add_argument('--window', type=str, default='no_edge', help='Window shape')
    parser.add_argument('--facets', type=int, default=1, help='Number of facets')
    parser.add_argument('--weighting', type=str, default='natural', help='Type of weighting')
    parser.add_argument('--use_serial_invert', type=str, default='False', help='Use serial invert?')
    parser.add_argument('--use_serial_predict', type=str, default='False', help='Use serial invert?')
    parser.add_argument('--plot', type=str, default='False', help='Plot data?')
    parser.add_argument('--serial', type=str, default='False', help='Use serial processing?')
    parser.add_argument('--nworkers', type=int, default=4, help='Number of workers')
    parser.add_argument('--memory', type=int, default=64, help='Memory of each worker')
    parser.add_argument('--time_coal', type=float, default=0.0, help='Coalesce time')
    parser.add_argument('--frequency_coal', type=float, default=0.0, help='Coalesce frequency')
    
    parser.add_argument('--deconvolve_facets', type=int, default=1, help='Number of facets in deconvolution')
    parser.add_argument('--deconvolve_overlap', type=int, default=128, help='overlap in deconvolution')
    parser.add_argument('--deconvolve_taper', type=str, default='tukey', help='Number of facets in deconvolution')

    args = parser.parse_args()
    
    target_ms = args.msname
    print("Target MS is %s" % target_ms)
    
    ochannels = numpy.arange(args.channels[0], args.channels[1]+1)
    print(ochannels)
    ngroup = args.ngroup
    weighting = args.weighting
    nwplanes = args.nwplanes
    nwslabs = args.nwslabs
    npixel = args.npixel
    cellsize = args.cellsize
    mode = args.mode
    fov = args.fov
    facets = args.facets
    wstep = args.wstep
    context = args.context
    use_serial_invert = args.use_serial_invert == "True"
    use_serial_predict = args.use_serial_predict == "True"
    serial = args.serial == "True"
    plot = args.plot == "True"
    single = args.single == "True"
    nworkers = args.nworkers
    memory = args.memory
    time_coal = args.time_coal
    frequency_coal = args.frequency_coal
    local_directory = args.local_directory
    window = args.window
    dela = args.amplitude_loss

    ####################################################################################################################

    print("\nSetup of processing mode")
    if serial:
        print("Will use serial processing")
        use_serial_invert = True
        arlexecute.set_client(use_dask=False)
        print(arlexecute.client)
    else:
        print("Will use dask processing")
        if nworkers > 0:
            client = get_dask_Client(n_workers=nworkers, memory_limit=memory * 1024 * 1024 * 1024,
                                     local_dir=local_directory)
            arlexecute.set_client(client=client)
        else:
            client = get_dask_Client()
            arlexecute.set_client(client=client)
        
        print(arlexecute.client)
        if use_serial_invert:
            print("Will use serial invert")
        else:
            print("Will use distributed invert")

    ####################################################################################################################

    # Read an MS and convert to Visibility format
    print("\nSetup of visibility ingest\n")
    def read_convert(ms, ch):
        start = time.time()
        bvis = create_blockvisibility_from_ms(ms, start_chan=ch[0], end_chan=ch[1])[0]
        # The following are not set in the MSes
        bvis.configuration.location = EarthLocation(lon="116.76444824", lat="-26.824722084", height=300.0)
        bvis.configuration.frame = ""
        bvis.configuration.receptor_frame = ReceptorFrame("linear")
        bvis.configuration.data['diameter'][...] = 35.0
        
        if time_coal > 0.0 or frequency_coal > 0.0:
            vis = coalesce_visibility(bvis, time_coal=time_coal, frequency_coal=frequency_coal)
            print("Time to read and convert %s, channels %d to %d = %.1f s" % (ms, ch[0], ch[1], time.time() - start))
            print('Size of visibility before compression %s, after %s' % (vis_summary(bvis), vis_summary(vis)))
        else:
            vis = convert_blockvisibility_to_visibility(bvis)
            print("Time to read and convert %s, channels %d to %d = %.1f s" % (ms, ch[0], ch[1], time.time() - start))
            print('Size of visibility before conversion %s, after %s' % (vis_summary(bvis), vis_summary(vis)))
        del bvis
        return vis
        
    print("Processing in groups of %d channels" % ngroup)
    channels = []
    for i in range(0, len(ochannels)-1, ngroup):
        channels.append([ochannels[i], ochannels[i + ngroup - 1]])
    print(channels)

    if single:
        channels = [channels[0]]
        print("Will read single range of channels %s" % channels)
    
    vis_list = [arlexecute.execute(read_convert)(target_ms, group_chan) for group_chan in channels]
    vis_list = arlexecute.persist(vis_list)

    ####################################################################################################################

    print("\nSetup of images\n")
    cellsize = 1.7578125 * numpy.pi / (180.0 * 3600.0)
    phasecentre = SkyCoord(ra=0.0 * u.deg, dec=-27.0 * u.deg)

    advice = [arlexecute.execute(advise_wide_field)(v, guard_band_image=fov, delA=dela, verbose=(iv==0))
              for iv, v in enumerate(vis_list)]
    advice = arlexecute.compute(advice, sync=True)
    
    if npixel is None:
        npixel = advice[0]['npixels23']
    
    if wstep is None:
        wstep = 1.1 * advice[0]['wstep']
        
    if nwplanes is None:
        nwplanes = int(1.1 * advice[0]['wprojection_planes'])
        
    if cellsize is None:
        cellsize = advice[-1]['cellsize']
        
    print('Image shape is %d by %d pixels' % (npixel, npixel))

    model_list = [arlexecute.execute(create_image_from_visibility)(v, npixel=npixel, cellsize=cellsize)
                  for v in vis_list]

    # Perform weighting. This is a collective computation, requiring all visibilities :(
    print("\nSetup of weighting\n")
    if weighting == 'uniform':
        print("\nWill apply uniform weighting\n")
        vis_list = weight_list_arlexecute_workflow(vis_list, model_list)

    ####################################################################################################################

    print("\nSetup of wide field imaging\n")
    vis_slices = 1
    actual_context = '2d'
    support = 1
    if context == 'wprojection':
        # w projection
        print("Will construct w projection kernels, %d planes, step %.1f" % (nwplanes, wstep))
        vis_slices = 1
        support = advice[0]['nwpixels']
        actual_context = '2d'
    elif context == 'wstack':
        # w stacking
        print("Will w stack, %d planes, step %.1f" % (nwplanes, wstep))
        actual_context = 'wstack'
    elif context == 'wprojectwstack':
        # Hybrid w projection/wstack
        nwplanes = 2 * nwplanes // nwslabs
        support = advice[0]['nwpixels'] // nwslabs
        vis_slices = nwslabs
        actual_context = 'wstack'
        print("Will do hybrid w stack/ w projection, %d w slabs, %d planes, step %.1f" % (nwslabs, nwplanes, wstep))
    else:
        # Simple 2D
        actual_context = '2d'
        vis_slices = 1
        wstep = 1e15
        nwplanes = 1
    
    if context == 'wprojection' or context == 'wprojectwstack':
        print("Will construct w projection kernels")
        gcfcf_list = [arlexecute.execute(create_awterm_convolutionfunction)(m, nw=nwplanes, wstep=wstep,
                                                                            oversampling=4,
                                                                            support=support,
                                                                            maxsupport=512)
                      for m in model_list]
        gcfcf_list = arlexecute.persist(gcfcf_list)
    else:
        gcfcf_list = None
        
        
    ####################################################################################################################

    if mode == 'pipeline':
        print("\nRunning pipeline\n")
        result = continuum_imaging_list_arlexecute_workflow(vis_list, model_list, context=actual_context,
                                                            vis_slices=vis_slices,
                                                            facets=facets, use_serial_invert=use_serial_invert,
                                                            use_serial_predict=use_serial_predict,
                                                            niter=args.niter,
                                                            fractional_threshold=args.fractional_threshold,
                                                            threshold=args.threshold,
                                                            nmajor=args.nmajor, gain=0.1,
                                                            algorithm='mmclean',
                                                            nmoment=1, findpeak='ARL',
                                                            scales=[0],
                                                            deconvolve_facets=args.deconvolve_facets,
                                                            deconvolve_overlap=args.deconvolve_overlap,
                                                            deconvolve_taper=args.deconvolve_taper,
                                                            timeslice='auto',
                                                            psf_support=256,
                                                            window_shape=window,
                                                            window_edge=128,
                                                            gcfcf=gcfcf_list,
                                                            return_moments=True)
        result = arlexecute.persist(result[2])
        restored = result[0]

        start = time.time()
        restored = arlexecute.compute(restored, sync=True)
        run_time = time.time() - start
        print("Processing took %.2f (s)" % run_time)

        print(qa_image(restored))

        show_image(restored, vmax=0.03, vmin=-0.003)
        plot_name = target_ms.split('/')[-1].replace('.MS', '_restored.jpg')
        plt.savefig(plot_name)
        plt.show(block=False)

        restored_name = target_ms.split('/')[-1].replace('.MS', '_restored.fits')
        print("Writing restored image to %s" % restored_name)
        export_image_to_fits(restored, restored_name)

    else:
        print("\nRunning invert\n")
        result = invert_list_arlexecute_workflow(vis_list, model_list, context=context, vis_slices=nwplanes,
                                                            facets=facets, use_serial_invert=use_serial_invert,
                                                            gcfcf=gcfcf_list)
        result = sum_invert_results_arlexecute(result)
        result = arlexecute.persist(result)
        dirty = result[0]
        
        start = time.time()
        dirty = arlexecute.compute(dirty, sync=True)
        run_time = time.time() - start
        print("Processing took %.2f (s)" % run_time)

        print(qa_image(dirty))
        
        show_image(dirty, vmax=0.03, vmin=-0.003)
        plot_name = target_ms.split('/')[-1].replace('.MS', '_dirty.jpg')
        plt.savefig(plot_name)
        plt.show(block=False)

        dirty_name = target_ms.split('/')[-1].replace('.MS', '_dirty.fits')
        print("Writing dirty image to %s" % dirty_name)
        export_image_to_fits(dirty, dirty_name)

    if not serial:
        arlexecute.close()
