import csv
import itertools as it
from common import StreetAddress, addressRecords


def registered(istrm):
    '''
    registered() instantiates a generator of BoE registered addresses from
    the input stream.
    '''
    BOEIDX_CITY = 11
    BOEIDX_DLVY_NR = 5
    BOEIDX_DLVY_ST = 6
    # BOEIDX_ZIP = 13
    rows = csv.reader(istrm)
    next(rows)  # discard header
    for ent in rows:
        try:
            record = StreetAddress(
                # ent[BOEIDX_ZIP],
                ent[BOEIDX_CITY],
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
            else:
                # unroll ends only
                ent = tuple(ent)
                k = unroll_max // 2
                queue = it.chain(queue, ent[:k])
                queue = it.chain(queue, ent[-k:])
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
    U = addressRecords(istrm)
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
