import csv
from usps_abbv import ABBREVIATIONS as ABBV

REGISTERED: set = set()
UNIVERSE: set = set()


def normalize(field):
    field = field.lower().strip()
    tokens = field.split()
    if len(tokens) > 1:
        t = tokens[-1]
        if t in ABBV:
            tokens[-1] = ABBV[t]
    return ' '.join(tokens)


with open('registered.csv') as istrm:
    rows = csv.reader(istrm)
    next(rows)  # discard header
    for ent in rows:
        REGISTERED.add(tuple(map(normalize, ent)))

with open('universe.csv') as istrm:
    rows = csv.reader(istrm)
    next(rows)  # discard header
    for ent in rows:
        UNIVERSE.add(tuple(map(normalize, ent)))

FINAL = UNIVERSE - REGISTERED

with open('unregistered.csv', 'w') as ostrm:
    stenographer = csv.writer(ostrm)
    for row in FINAL:
        stenographer.writerow(row)
