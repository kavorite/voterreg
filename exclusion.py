import csv
from usps_abbv import ABBREVIATIONS as ABBV

REGISTERED: set = set()
UNIVERSE: set = set()


def normalize(field):
    field = field.lower().strip()
    tokens = (ABBV[t] if t in ABBV else t for t in field.split())
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
