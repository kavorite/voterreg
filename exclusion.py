import csv
import re
from usps_abbv import ABBREVIATIONS as ABBV
from math import floor, ceil
import itertools as it
from sys import stderr
from collections import deque

HALFPATTERN = re.compile('([0-9]+) 1/2?')


class StreetAddress(object):
    def __init__(self, zip_code: str, st: str, nr: str):
        self.zip = zip_code
        self.street = self.__class__.normalize(st)
        self.number = re.sub(HALFPATTERN, r'\1.5', nr)

    def tuple(self):
        return (self.zip, self.street, self.number)

    _cardinal = {
        'n': 'north',
        'e': 'east',
        's': 'south',
        'w': 'west',
        'nw': 'northwest',
        'ne': 'northeast',
        'sw': 'southwest',
        'se': 'southeast',
    }

    _directions = set(it.chain(_cardinal.keys(), _cardinal.values()))
    _qualifiers = set(it.chain(ABBV.keys(), ABBV.values()))

    @classmethod
    # N Herald Circle -> heraldcircle north internally
    def normalize(cls, street):
        street = street.lower().strip()
        tokens = street.split()
        for i in reversed(range(len(tokens))):
            # move cardinal qualifiers to beginning in reverse order of
            # appearance
            if tokens[i] in cls._directions:
                t = tokens[i]
                tokens = tokens[:i] + tokens[i+1:]
                if t in cls._cardinal:
                    t = cls._cardinal[t]
                tokens = [t] + tokens

            # collapse all tokens before the last street qualifier into a
            # single word
        for i in reversed(range(len(tokens))):
            if tokens[i] in cls._qualifiers:
                tokens = [''.join(tokens[:i])] + tokens[i:]
                # Abbreviate/canonicalize the qualifier
                if tokens[1] in ABBV:
                    tokens[1] = ABBV[tokens[1]]
                break

        return ' '.join(tokens)

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
        if row.__class__ == self.__class__:
            for k in self.__class__.__slots__:
                setattr(self, k, getattr(row, k))
        else:
            row = iter(row)
            for k in self.__class__.__slots__:
                setattr(self, k, next(row))
        self.st_nbr = re.sub(HALFPATTERN, r'\1.5', self.st_nbr)

    def address(self) -> StreetAddress:
        return StreetAddress(self.par_zip, self.gis_st_name, self.st_nbr)

    def tuple(self):
        rtn = [getattr(self, k) for k in self.__class__.__slots__]
        rtn.append(str(self))
        return tuple(rtn)

    def __str__(self):
        return (f'{self.st_nbr} {self.gis_st_name}'
                f', {self.city}, {self.par_zip}, USA')

    def is_bulk(self):
        return 'family res' not in self.prop_desc.lower()


class AddressRange(object):
    def __init__(self, ent: MonroeCtRecord, start: float, end: float):
        if start > end:
            start, end = end, start
        self.start = start
        self.end = end

    def __len__(self):
        a = floor(self.start)
        b = floor(self.end)
        n = (b - a) // 2
        if floor(b) != b:
            n += 1
        if floor(a) != a:
            n += 1


    def __iter__(self):
        a, b = self.start, self.end
        enum = range(int(a), int(b), 2)
        if floor(b) != b:
            enum = it.chain(enum, (b,))
        if floor(a) != a:
            enum = it.chain((a,), enum)

        for n in enum:
            x = MonroeCtRecord(ent)
            x.st_nbr = str(n)
            yield x


def universe(istrm):
    '''
    universe() instantiates a generator that yields the input stream's file
    header, then each record it reads as a new `MonroeCtRecord`.
    '''
    rows = csv.reader(istrm)
    yield next(rows)  # yield header
    rangedelim = re.compile('[-&]')
    for row in rows:
        ent = MonroeCtRecord(row)
        try:
            a, b = rangedelim.split(ent.st_nbr)
            enum = AddressRange(ent, float(a), float(b))
            yield enum
        except ValueError:
            yield ent


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
        try:
            record = StreetAddress(
                    ent[BOEIDX_ZIP],
                    ent[BOEIDX_DLVY_ST],
                    ent[BOEIDX_DLVY_NR])
        except Exception:
            continue
        yield record


def exclusion(universe, registered, unrollp, unroll_max):
    if unrollp:
        queue = (ent for ent in universe if hasattr(ent, '__iter__'))
    else:
        queue = universe
    for ent in queue:
        if hasattr(ent, '__iter__'):
            if unroll_max < 0 or len(ent) <= unroll_max:
                queue = it.chain(queue, ent)
        elif ent.address() not in registered:
            yield ent


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
    parser.add_argument('--unroll',
                        help='if present, only unroll address ranges',
                        action='store_true')
    parser.add_argument('--unrollmax',
                        type=int,
                        help='max. number of addresses to unroll',
                        default=3)
    args = parser.parse_args()
    # Instantiate a generator to read in the solution set of addresses
    istrm = open(args.universe)
    U = universe(istrm)
    header = list(next(U))
    header.append('CANON')

    istrm = open(args.registered)
    R = set(registered(istrm))
    X = exclusion(U, R, args.unroll, args.unrollmax)

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
