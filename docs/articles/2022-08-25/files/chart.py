from datetime import timedelta
from pathlib import Path
from itertools import zip_longest

import seaborn as sns
import pandas as pd


btrfs_test = Path('output-btrfs.txt').read_text()
lvm_test = Path('output-lvm.txt').read_text()
zfs_test = Path('output-zfs.txt').read_text()

exec_time = {}


def get_lines(output_text):
    return [line for line in output_text.splitlines()
            if line.startswith('execution')]


def get_lines_data(lines):
    return [timedelta(minutes=int((digits := line.strip()[-7:])[0]),
                      seconds=int(digits[2:4]),
                      milliseconds=int(digits[5:7]))
            for line in lines]


exec_time['btrfs'] = get_lines(btrfs_test)
exec_time['zfs'] = get_lines(zfs_test)
exec_time['lvm'] = get_lines(lvm_test)

exec_time['lvm-data'] = get_lines_data(exec_time['lvm'])
exec_time['zfs-data'] = get_lines_data(exec_time['zfs'])
exec_time['btrfs-data'] = get_lines_data(exec_time['btrfs'])

data = zip_longest(exec_time['zfs-data'], exec_time['lvm-data'], exec_time['btrfs-data'])
df = pd.DataFrame(data, columns=['ZFS', 'LVM', 'BTRFS'])
df = df.cumsum()

sns.set_theme()
plot = df.plot(title='Snapshots creation time.', fontsize=8)
plot.legend(fontsize='x-small')
plot.figure.savefig('creation-time-chart.png', dpi=1200.0)
print('Done.')
