import csv
import re
from usps_abbv import ABBREVIATIONS as ABBV


class StreetAddress(object):
    def __init__(self, zip_code: str, st: str, nr: str):
        self.zip = zip_code
        self.street = self.__class__.normalize(st)
        self.number = nr

    def tuple(self):
        return (self.street, self.number)

    _cardinal = {
        'n': 'north',
        'e': 'east',
        's': 'south',
        'w': 'west',
    }

    @classmethod
    def normalize(cls, street):
        street = street.lower().strip()
        tokens = street.split()
        if len(tokens) > 1:
            for i in range(len(tokens)):
                if tokens[i] in cls._cardinal:
                    tokens[i] = cls._cardinal[tokens[i]]

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
        return StreetAddress(self.par_zip, self.gis_st_name, self.st_nbr)

    def tuple(self):
        return tuple(getattr(self, k) for k in self.__class__.__slots__)

    def is_bulk(self):
        return 'family res' not in self.prop_desc.lower()


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
    registered() instantiates a generator of BoE registered addresses from
    the input stream.
    '''
    # BOEIDX_CITY = 11
    BOEIDX_DLVY_NR = 5
    BOEIDX_DLVY_ST = 6
    BOEIDX_ZIP = 13
    rows = csv.reader(istrm)
    next(rows)  # discard header
    for ent in rows:
        record = StreetAddress(
                ent[BOEIDX_ZIP],
                ent[BOEIDX_DLVY_ST],
                ent[BOEIDX_DLVY_NR])
        yield record


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

    istrm = open(args.registered)
    R = set(registered(istrm))

    X = (ent for ent in U if ent.is_bulk() or ent.address() not in R)

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
