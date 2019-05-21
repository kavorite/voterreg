import csv
from usps_abbv import ABBREVIATIONS as ABBV
from exclusion import normalize

U: set = set()
REDUNDANT: int = 0

with open('universe.csv') as istrm:
    rows = csv.reader(istrm)
    next(rows)  # discard header
    for row in rows:
        ent = tuple(map(normalize, row))
        if ent in U:
            REDUNDANT += 1
            continue
        U.add(ent)

print(REDUNDANT)
