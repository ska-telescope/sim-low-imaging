
import logging
import sys

from processing_components.visibility.base import create_blockvisibility_from_ms

log = logging.getLogger()
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler(sys.stdout))
mpl_logger = logging.getLogger("matplotlib")
mpl_logger.setLevel(logging.WARNING)

# 116G	/mnt/storage-ssd/tim/data/GLEAM_A-team_EoR0_0.270_dB.ms
# 116G	/mnt/storage-ssd/tim/data/GLEAM_A-team_EoR0_no_errors.ms
msnames = ['/mnt/storage-ssd/tim/data/GLEAM_A-team_EoR0_0.270_dB.ms',
           '/mnt/storage-ssd/tim/data/GLEAM_A-team_EoR0_no_errors.ms']

# 7.8G	/mnt/storage-ssd/tim/data/EoR0_20deg_24.MS
# 31G	/mnt/storage-ssd/tim/data/EoR0_20deg_96.MS
# 62G	/mnt/storage-ssd/tim/data/EoR0_20deg_192.MS
# 116G	/mnt/storage-ssd/tim/data/EoR0_20deg_360.MS
# 155G	/mnt/storage-ssd/tim/data/EoR0_20deg_480.MS
# 194G	/mnt/storage-ssd/tim/data/EoR0_20deg_600.MS
# 232G	/mnt/storage-ssd/tim/data/EoR0_20deg_720.MS

msname_times = [
    '/mnt/storage-ssd/tim/data/EoR0_20deg_24.MS',
    '/mnt/storage-ssd/tim/data/EoR0_20deg_96.MS',
    '/mnt/storage-ssd/tim/data/EoR0_20deg_192.MS',
    '/mnt/storage-ssd/tim/data/EoR0_20deg_480.MS',
    '/mnt/storage-ssd/tim/data/EoR0_20deg_600.MS',
    '/mnt/storage-ssd/tim/data/EoR0_20deg_360.MS',
    '/mnt/storage-ssd/tim/data/EoR0_20deg_720.MS']

for msname in msname_times:
    print("Reading ", msname)
    bvis = create_blockvisibility_from_ms(msname)
    print(bvis[0])
    del bvis