import logging
import pprint
import sys
import time
import os

import argparse

import astropy.units as u
import matplotlib.pyplot as plt
import numpy
from astropy.coordinates import SkyCoord, EarthLocation

from data_models.polarisation import ReceptorFrame, PolarisationFrame

from processing_library.image.operations import create_image
from processing_components.image.operations import qa_image, export_image_to_fits
from processing_components.imaging.base import advise_wide_field
from processing_components.visibility.base import create_blockvisibility_from_ms, export_blockvisibility_to_ms
from processing_components.visibility.coalesce import convert_blockvisibility_to_visibility

from workflows.arlexecute.imaging.imaging_arlexecute import invert_list_arlexecute_workflow, \
    sum_invert_results_arlexecute
from workflows.arlexecute.imaging.imaging_arlexecute import weight_list_arlexecute_workflow
from wrappers.arlexecute.execution_support.arlexecute import arlexecute
from wrappers.arlexecute.execution_support.dask_init import get_dask_Client

pp = pprint.PrettyPrinter()

log = logging.getLogger()
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler(sys.stdout))
mpl_logger = logging.getLogger("matplotlib")
mpl_logger.setLevel(logging.WARNING)

def init_logging():
    logging.basicConfig(filename='image_ms.log',
                        filemode='a',
                        format='%(thread)s %(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.INFO)



if __name__ == "__main__":
    
    init_logging()
    
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
    
    parser = argparse.ArgumentParser(description='Low imaging test')
    parser.add_argument('--context', type=str, default='2d', help='Imaging context')
    parser.add_argument('--msname', type=str, default='../data/EoR0_20deg_24.MS',
                        help='MS to process')
    parser.add_argument('--ngroup', type=int, default=4,
                        help='Number of channels in each BlockVisibility')
    parser.add_argument('--npixel', type=int, default=1024, help='Number of pixels')
    parser.add_argument('--single', type=str, default='True', help='Use a single channel')
    parser.add_argument('--nwplanes', type=int, default=1, help='Number of wplanes')
    parser.add_argument('--facets', type=int, default=1, help='Number of facets')
    parser.add_argument('--weighting', type=str, default='natural', help='Type of weighting')
    parser.add_argument('--use_serial_invert', type=str, default='False', help='Use serial invert?')
    parser.add_argument('--plot', type=str, default='False', help='Plot data?')
    parser.add_argument('--serial', type=str, default='False', help='Use serial processing?')
    parser.add_argument('--nworkers', type=int, default=4, help='Number of workers')
    parser.add_argument('--memory', type=int, default=64, help='Memory of each worker')
    args = parser.parse_args()
    
    target_ms = args.msname
    print("Target MS is %s" % target_ms)
    
    ochannels = numpy.arange(160)
    ngroup = args.ngroup
    print("Processing in groups of %d channels" % ngroup)
    weighting = args.weighting
    nwplanes = args.nwplanes
    npixel = args.npixel
    facets = args.facets
    context = args.context
    use_serial_invert = args.use_serial_invert == "True"
    serial = args.serial == "True"
    plot = args.plot == "True"
    single = args.single == "True"
    nworkers = args.nworkers
    memory = args.memory
    
    if plot:
        print("Writing plots")
    
    if serial:
        print("Using serial processing")
        print("Using serial invert")
        use_serial_invert = True
        arlexecute.set_client(use_dask=False)
        print(arlexecute.client)
    else:
        print("Using dask processing")
        if nworkers > 0:
            client = get_dask_Client(n_workers=nworkers, memory_limit=memory * 1024 * 1024 * 1024)
            arlexecute.set_client(client=client)
        else:
            client = get_dask_Client()
            arlexecute.set_client(client=client)

        print(arlexecute.client)
        if use_serial_invert:
            print("Using serial invert")
        else:
            print("Using distributed invert")
        arlexecute.run(init_logging)

    import matplotlib as mpl
    mpl.use('Agg')
    
    def read_convert(ms, ch):
        ms_out = ms.split('/')[-1].replace('.MS', '_ch%d_ch%d.MS' % (ch[0], ch[1]))
        if os.path.exists(ms_out):
            print("Reading MS file %s" % (ms_out))
            bvis = create_blockvisibility_from_ms(ms_out)[0]
        else:
            print("Reading MS file %s" % (ms))
            bvis = create_blockvisibility_from_ms(ms, start_chan=ch[0], end_chan=ch[1])[0]
            bvis.configuration.location = EarthLocation(lon="116.76444824", lat="-26.824722084", height=300.0)
            bvis.configuration.frame = ""
            bvis.configuration.receptor_frame = ReceptorFrame("linear")
            bvis.configuration.data['diameter'][...] = 35.0
            print('Writing to %s' % (ms_out))
            export_blockvisibility_to_ms(ms_out, [bvis], source_name='EOR_TEST')
        vis = convert_blockvisibility_to_visibility(bvis)
        del bvis
        return vis
    
    channels = [[ochannels[i], ochannels[i + ngroup - 1]] for i in range(0, len(ochannels), ngroup)]
    
    if single:
        channels = [channels[0]]
        
    print("Reading channels %s" % channels)
        
    vis_list = [arlexecute.execute(read_convert)(target_ms, group_chan) for group_chan in channels]
    vis_list = arlexecute.persist(vis_list)
    
    if plot:
        vis_list0 = arlexecute.compute(vis_list[0], sync=True)
        print(vis_list0)
        print("Size of one vis = %.3f GB" % vis_list0.size())
        advice = advise_wide_field(vis_list0)
        pp.pprint(advice)
        
        plt.clf()
        plt.plot(vis_list0.u[::101], vis_list0.v[::101], '.')
        plt.plot(-vis_list0.u[::101], -vis_list0.v[::101], '.')
        plt.savefig('uvcoverage.png')
        plt.show(block=False)
        
        plt.clf()
        plt.plot(vis_list0.uvdist[::101], numpy.abs(vis_list0.vis[:, 0][::101]), '.')
        plt.savefig('visibility.png')
        plt.show(block=False)
    
    cellsize = 1.7578125 * numpy.pi / (180.0 * 3600.0)
    phasecentre = SkyCoord(ra=0.0 * u.deg, dec=-27.0 * u.deg)
    frequency = numpy.linspace(1.32e8, 1.479e+08, 160)
    print(len(frequency), frequency)
    model_list = [arlexecute.execute(create_image)(npixel=npixel, cellsize=cellsize,
                                                   frequency=[frequency[0]],
                                                   channel_bandwidth=[(numpy.max(frequency)-numpy.min(frequency))],
                                                   phasecentre=v.phasecentre)
                  for v in vis_list]

    # Perform weighting. This is a collective computation, requiring all visibilities :(
    if weighting == 'uniform':
        print("Applying uniform weighting")
        vis_list = weight_list_arlexecute_workflow(vis_list, model_list)
    
    vis_list = arlexecute.persist(vis_list)
    
    # Now make the dirty images one for each vis
    separate = True
    if separate:
        dirty_list = []
        for iv, v in enumerate(vis_list):
            result = invert_list_arlexecute_workflow([vis_list[iv]], [model_list[iv]], context=context, vis_slices=nwplanes,
                                                     facets=facets, use_serial_invert=use_serial_invert)
            result = sum_invert_results_arlexecute(result)
            dirty_list.append(result)
        result = sum_invert_results_arlexecute(dirty_list)
    else:
        result = invert_list_arlexecute_workflow(vis_list, model_list, context=context, vis_slices=nwplanes,
                                                 facets=facets, use_serial_invert=use_serial_invert)
        result = sum_invert_results_arlexecute(result)
    
    start = time.time()
    dirty, sumwt = arlexecute.compute(result, sync=True)
    run_time = time.time() - start
    print("Processing took %.2f (s)" % run_time)
    
    print(qa_image(dirty))
    dirty_name = target_ms.split('/')[-1].replace('.MS', '.fits')
    print("Writing result to %s" % dirty_name)
    export_image_to_fits(dirty, dirty_name)
    
    if not serial:
        arlexecute.close()
