#!/usr/bin/zsh

for i in {1..2000}
do
    echo 'line'$i >> /btrfs/documents/btrfs-doc.txt
    /usr/bin/time -f "execution time: %E" btrfs subvolume snapshot /btrfs/documents /btrfs/snapshots/documents-snap$i
done
