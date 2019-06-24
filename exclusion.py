import csv
import re
from usps_abbv import ABBREVIATIONS as ABBV
from collections import Counter


class StreetAddress(object):
    def __init__(self, city: str, postcode: int, st: str, nr: int):
        self.city = city.lower().strip()
        self.street = self.__class__.normalize(st)
        self.number = nr
        self.zip = postcode

    def tuple(self):
        return (self.city, self.zip, self.street, self.number)

    @staticmethod
    def normalize(street):
        street = street.lower().strip()
        tokens = street.split()
        if len(tokens) > 1:
            t = tokens[-1]
            if t in ABBV:
                tokens[-1] = ABBV[t]
        return ' '.join(tokens).lower()

    def __hash__(self):
        return hash(self.tuple())

    def __eq__(self, other):
        return hash(self) == hash(other)


class MonroeCtRecord(object):
    __slots__ = ("object_id", "print_key", "st_nbr", "gis_st_name",
                 "rps_st_name", "loc_pre_dir", "loc_st_name", "loc_st_type",
                 "owner1", "owner2", "own_addr", "own_addr_2", "prop_desc",
                 "sch_name", "par_zcty", "par_zip", "city", "disp_addr",
                 "fe_name", "fe_type", "p_name", "pol_address")

    def __init__(self, row):
        row = iter(row)
        for k in self.__class__.__slots__:
            setattr(self, k, next(row))

    def address(self) -> StreetAddress:
        st = f'{self.loc_st_name} {self.loc_st_type}'
        return StreetAddress(self.city, int(self.par_zip), st, int(self.st_nbr))

    def tuple(self):
        return tuple(getattr(self, k) for k in self.__class__.__slots__)
            
    @staticmethod
    def parse_family_count(res_kind: str):
        res_kind = res_kind.lower().strip()
        count_pattern = re.compile('([0-9]+) family res')
        counts = count_pattern.finditer(res_kind)
        try:
            count = int(next(counts).groups()[0])
        except (StopIteration, IndexError):
            count = -1
        return count
    
    def families(self):
        n = self.__class__.parse_family_count(self.prop_desc)
        # assume an "infinite" count of families for bulk housing and edge
        # contingencies
        return n if n > 0 else float('inf')


def universe(istrm):
    '''
    universe() instantiates a generator that yields the input stream's file
    header, then each record it reads as a new `MonroeCtRecord`.
    '''
    rows = csv.reader(istrm)
    yield next(rows)  # yield header

    for row in rows:
        yield MonroeCtRecord(row)


def registered(istrm):
    '''
    registered() creates a mapping of registered addresses to a number of
    current registrants by counting their occurrences in the given record
    stream.
    '''
    rtn = Counter()
    BOEIDX_CITY = 11
    BOEIDX_DLVY_NR = 5
    BOEIDX_DLVY_ST = 6
    BOEIDX_ZIP = 13
    rows = csv.reader(istrm)
    next(rows)  # discard header
    for ent in rows:
        try:
            record = StreetAddress(
                    ent[BOEIDX_CITY],
                    int(ent[BOEIDX_ZIP]),
                    ent[BOEIDX_DLVY_ST],
                    int(ent[BOEIDX_DLVY_NR]))
            rtn[record] += 1
        except ValueError:
            continue
    return rtn


def exclusion(U, R):
    '''
    Returns a generator that excludes Monroe County address records with at
    least as many registered voters as they have resident families from its
    output. Filter always succeeds for bulk housing and other contingencies.
    '''
    for ent in U:
        try:
            if R[ent.address()] < ent.families():
                yield ent
        except ValueError:
            continue


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser('obtain mailing list of unregistered voters')
    parser.add_argument('--universe',
                        help='path from which to read universal address set',
                        required=True)
    parser.add_argument('--registered',
                        help='path from which to read registrant address set',
                        required=True)
    parser.add_argument('--opath',
                        help='output path',
                        default=None)
    args = parser.parse_args()
    # Instantiate a generator to read in the solution set of addresses
    istrm = open(args.universe)
    U = universe(istrm)
    header = next(U)

    # Create a mapping of addresses to their current nr. of registered voters
    istrm = open(args.registered)
    R = registered(istrm)

    X = exclusion(U, R)

    if args.opath is None:
        from sys import stdout
        ostrm = stdout
    else:
        ostrm = open(args.opath, 'w')

    stenographer = csv.writer(ostrm)

    try:
        stenographer.writerow(header)
        for ent in X:
            stenographer.writerow(ent.tuple())
    finally:
        ostrm.close()
