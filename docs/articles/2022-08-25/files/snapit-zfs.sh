#!/usr/bin/zsh

for i in {1..2000}
do
    echo 'line'$i >> /zpool/documents/zfs-doc.txt
    /usr/bin/time -f "execution time: %E" zfs snapshot zpool/documents@snap-$i
done
