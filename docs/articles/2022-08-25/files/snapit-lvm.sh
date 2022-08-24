#!/usr/bin/zsh

for i in {1..2000}
do
    echo 'line'$i >> /lvm-fs/lvm-doc.txt
    /usr/bin/time -f "execution time: %E" lvcreate -q --name lvm-snap-$i --snapshot vgstoragebox/lvm
done
