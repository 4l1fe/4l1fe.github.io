from functools import partial
from decimal import Decimal
from collections import defaultdict
from more_itertools import split_at, strip
from pprint import pprint


def to_dict(data):
    d = defaultdict(Decimal)
    for lines in data:
        for line in lines:
            k, v = line.split(':')
            d[k.strip()] += Decimal(v)
    return d


def main():
    with open('sqlitedict/hal.txt') as fsql, open('peewee-kv/hal.txt') as fkv, open('tinydb/hal.txt') as fti:
        dsql, dkv, dti = tuple(file.read().splitlines() for file in (fsql, fkv, fti))

    split_att = partial(split_at, pred=lambda line: line.startswith('/'))
    stripp = partial(strip, pred=lambda line: bool(line) is False)
    dsql, dkv, dti = map(stripp, map(split_att, (dsql, dkv, dti)))

    kvsql, kvkv, kvti = map(to_dict, (dsql, dkv, dti))
    return kvsql, kvkv, kvti


if __name__ == '__main__':
    res = main()
    pprint(res)