import argparse
import logging
import os
import pprint
import sys

import numpy
from astropy.coordinates import EarthLocation

from data_models.polarisation import ReceptorFrame
from processing_components.visibility.base import create_blockvisibility_from_ms, export_blockvisibility_to_ms
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
    parser.add_argument('--msname', type=str, default='../data/EoR0_20deg_24.MS',
                        help='MS to process')
    parser.add_argument('--ngroup', type=int, default=4,
                        help='Number of channels in each BlockVisibility')
    parser.add_argument('--single', type=str, default='False', help='Use a single channel')
    parser.add_argument('--serial', type=str, default='False', help='Use serial processing?')
    parser.add_argument('--nworkers', type=int, default=4, help='Number of workers')
    parser.add_argument('--memory', type=int, default=64, help='Memory of each worker')
    args = parser.parse_args()
    
    target_ms = args.msname
    print("Target MS is %s" % target_ms)
    
    ochannels = numpy.arange(160)
    ngroup = args.ngroup
    print("Processing in groups of %d channels" % ngroup)
    serial = args.serial == "True"
    single = args.single == "True"
    nworkers = args.nworkers
    memory = args.memory
    
    if serial:
        print("Using serial processing")
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
        arlexecute.run(init_logging)
    
    import matplotlib as mpl
    
    mpl.use('Agg')
    
    
    def read_write(ms, ch):
        ms_out = ms.split('/')[-1].replace('.MS', '_ch%d_ch%d.MS' % (ch[0], ch[1]))
        print("Reading MS file %s" % (ms))
        bvis = create_blockvisibility_from_ms(ms, start_chan=ch[0], end_chan=ch[1])[0]
        bvis.configuration.location = EarthLocation(lon="116.76444824", lat="-26.824722084", height=300.0)
        bvis.configuration.frame = ""
        bvis.configuration.receptor_frame = ReceptorFrame("linear")
        bvis.configuration.data['diameter'][...] = 35.0
        print('Writing to %s' % (ms_out))
        export_blockvisibility_to_ms(ms_out, [bvis], source_name='EOR_TEST')
        return True
    
    
    channels = [[ochannels[i], ochannels[i + ngroup - 1]] for i in range(0, len(ochannels), ngroup)]
    if single:
        channels = [channels[0]]
    print("Reading channels %s" % channels)
    
    vis_list = [arlexecute.execute(read_write)(target_ms, group_chan) for group_chan in channels]
    vis_list = arlexecute.compute(vis_list, sync=True)
    
    print(vis_list)
    
    if not serial:
        arlexecute.close()
